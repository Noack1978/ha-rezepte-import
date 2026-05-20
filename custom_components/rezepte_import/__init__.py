"""Rezepte Import – optionale Erweiterung für ha-rezepte.

Stellt drei Services bereit:
  rezepte_import.parse_text   – Freitext / TXT-Dateiinhalt analysieren
  rezepte_import.parse_image  – Foto / Scan via LLM Vision analysieren
  rezepte_import.parse_url    – Webseite abrufen und Rezept extrahieren

Ergebnis wird nach /config/www/rezepte/import_result.json geschrieben.
import.js in der Web-App liest das Ergebnis per Polling aus.
"""
from __future__ import annotations

import base64
import json
import logging
import shutil
import time
from html.parser import HTMLParser
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN                   = "rezepte_import"
REZEPTE_DOMAIN           = "rezepte"
RESULT_FILE              = "import_result.json"
AGENT_ID_DEFAULT         = "conversation.google_generative_ai"
LLMVISION_PROVIDER_DEFAULT = "Google"
MAX_TEXT_LENGTH          = 8000   # Zeichen – Limit für URL-Extraktion
VALID_UNITS              = {"g", "kg", "ml", "l", "TL", "EL", "Stk.", "Prise", "n.B."}

# ── Prompts ────────────────────────────────────────────────────────────────────

_PROMPT_BASE = """Analysiere den folgenden Rezepttext und gib AUSSCHLIESSLICH ein JSON-Objekt zurück.
Kein Markdown, keine Codeblöcke, keine Erklärungen – nur das rohe JSON-Objekt.

Format:
{
  "title": "Rezeptname",
  "subtitle": "Gerätename oder Variante (leer lassen wenn nicht vorhanden)",
  "emoji": "passendes Emoji",
  "category": "Kategorie (z.B. Hauptgericht, Sauce, Dessert, Beilage, Snack, Getränk)",
  "description": "1-2 Sätze Kurzbeschreibung",
  "baseServings": 4,
  "servingLabel": "Portionen",
  "ingredients": [
    {"amount": 200, "unit": "g", "name": "Zutatname"}
  ],
  "steps": [
    {"text": "Schrittbeschreibung", "timerSec": 300}
  ],
  "notes": ["Tipp oder Hinweis"]
}

Regeln:
- amount ist eine Zahl (0 wenn keine Mengenangabe)
- unit MUSS eines dieser Werte sein: g, kg, ml, l, TL, EL, Stk., Prise, n.B.
- timerSec ist die Wartezeit/Kochzeit in Sekunden (0 wenn kein Timer sinnvoll)
- notes enthält Tipps, Variationen, Hinweise als einzelne Strings
- Antworte NUR mit dem JSON-Objekt – kein Text davor oder danach

Rezepttext:
"""

_PROMPT_IMAGE = """Analysiere das Bild. Es zeigt ein Rezept, eine Zutatenliste oder ein Gericht.
Extrahiere alle sichtbaren Rezeptinformationen und gib AUSSCHLIESSLICH ein JSON-Objekt zurück.
Kein Markdown, keine Codeblöcke, keine Erklärungen.

Format:
{
  "title": "Rezeptname",
  "subtitle": "",
  "emoji": "passendes Emoji",
  "category": "Kategorie",
  "description": "Kurzbeschreibung",
  "baseServings": 4,
  "servingLabel": "Portionen",
  "ingredients": [{"amount": 200, "unit": "g", "name": "Zutatname"}],
  "steps": [{"text": "Schrittbeschreibung", "timerSec": 0}],
  "notes": []
}

Regeln: amount=Zahl, unit eines von: g,kg,ml,l,TL,EL,Stk.,Prise,n.B., timerSec=Sekunden (0 wenn unklar).
Antworte NUR mit dem JSON-Objekt."""


# ── Setup ──────────────────────────────────────────────────────────────────────

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integration einrichten."""
    agent_id        = entry.data.get("conversation_agent", AGENT_ID_DEFAULT)
    llmvision_prov  = entry.data.get("llmvision_provider", LLMVISION_PROVIDER_DEFAULT)

    # import.js nach /config/www/rezepte/ kopieren
    await hass.async_add_executor_job(_provision_js, hass)

    # ── Service: parse_text ────────────────────────────────────────────────────
    async def handle_parse_text(call: ServiceCall) -> None:
        text = call.data.get("text", "").strip()
        if not text:
            _write_error(hass, "Kein Text übergeben.")
            return
        prompt = _PROMPT_BASE + text
        await _call_conversation(hass, agent_id, prompt)

    # ── Service: parse_image ───────────────────────────────────────────────────
    async def handle_parse_image(call: ServiceCall) -> None:
        image_b64 = call.data.get("image_data", "")
        mime_type  = call.data.get("mime_type", "image/jpeg")
        if not image_b64:
            _write_error(hass, "Keine Bilddaten übergeben.")
            return

        ext       = "jpg" if "jpeg" in mime_type else mime_type.split("/")[-1]
        tmp_path  = f"/tmp/rezept_import_{int(time.time())}.{ext}"

        await hass.async_add_executor_job(_write_image_file, tmp_path, image_b64)
        try:
            result = await hass.services.async_call(
                "llmvision", "image_analyzer",
                {
                    "provider":        llmvision_prov,
                    "message":         _PROMPT_IMAGE,
                    "image_file":      [tmp_path],
                    "max_tokens":      2000,
                    "target_width":    1920,
                    "include_filename": False,
                },
                blocking=True,
                return_response=True,
            )
            response_text = result.get("response_text", "")
            _write_parsed(hass, response_text)
        except Exception as err:
            _write_error(hass, f"LLM Vision Fehler: {err}")
        finally:
            await hass.async_add_executor_job(_delete_file, tmp_path)

    # ── Service: parse_url ────────────────────────────────────────────────────
    async def handle_parse_url(call: ServiceCall) -> None:
        url = call.data.get("url", "").strip()
        if not url:
            _write_error(hass, "Keine URL übergeben.")
            return
        try:
            session = async_get_clientsession(hass)
            async with session.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; HA-Rezepte-Import/1.0)"},
                timeout=__import__("aiohttp").ClientTimeout(total=20),
            ) as resp:
                resp.raise_for_status()
                html = await resp.text(errors="replace")
            text = _extract_text_from_html(html)[:MAX_TEXT_LENGTH]
        except Exception as err:
            _write_error(hass, f"URL abrufen fehlgeschlagen: {err}")
            return
        prompt = _PROMPT_BASE + text
        await _call_conversation(hass, agent_id, prompt)

    hass.services.async_register(DOMAIN, "parse_text",  handle_parse_text)
    hass.services.async_register(DOMAIN, "parse_image", handle_parse_image)
    hass.services.async_register(DOMAIN, "parse_url",   handle_parse_url)

    _LOGGER.info("Rezepte Import geladen (Agent: %s, Vision: %s)", agent_id, llmvision_prov)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    for svc in ("parse_text", "parse_image", "parse_url"):
        hass.services.async_remove(DOMAIN, svc)
    return True


# ── Hilfsfunktionen – KI ──────────────────────────────────────────────────────

async def _call_conversation(hass: HomeAssistant, agent_id: str, prompt: str) -> None:
    """Sendet Prompt an den konfigurierten Konversationsagenten und schreibt Ergebnis."""
    try:
        result = await hass.services.async_call(
            "conversation", "process",
            {"text": prompt, "agent_id": agent_id, "language": "de"},
            blocking=True,
            return_response=True,
        )
        response_text = (
            result
            .get("response", {})
            .get("speech", {})
            .get("plain", {})
            .get("speech", "")
        )
        _write_parsed(hass, response_text)
    except Exception as err:
        _write_error(hass, f"Konversations-API Fehler: {err}")


def _write_parsed(hass: HomeAssistant, response_text: str) -> None:
    """JSON aus KI-Antwort extrahieren, validieren und Ergebnis schreiben."""
    try:
        recipe = _parse_json_response(response_text)
        recipe = _validate_recipe(recipe)
        _write_result(hass, {"ts": int(time.time()), "status": "ok", "recipe": recipe})
    except Exception as err:
        _write_error(hass, f"JSON-Parsing fehlgeschlagen: {err}. Antwort: {response_text[:200]}")


def _parse_json_response(text: str) -> dict:
    """Extrahiert und parst JSON aus der KI-Antwort."""
    text = text.strip()
    # Markdown-Fences entfernen
    if "```" in text:
        for part in text.split("```"):
            part = part.strip().lstrip("json").strip()
            try:
                return json.loads(part)
            except Exception:
                continue
    # Direkt parsen
    try:
        return json.loads(text)
    except Exception:
        pass
    # JSON-Objekt im Text suchen
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("Kein gültiges JSON gefunden")


def _validate_recipe(r: dict) -> dict:
    """Prüft und korrigiert die Rezeptdatenstruktur."""
    r.setdefault("title",        "Importiertes Rezept")
    r.setdefault("subtitle",     "")
    r.setdefault("emoji",        "🍳")
    r.setdefault("category",     "")
    r.setdefault("description",  "")
    r.setdefault("servingLabel", "Portionen")
    r.setdefault("notes",        [])

    try:
        r["baseServings"] = max(1, int(r.get("baseServings", 4)))
    except (ValueError, TypeError):
        r["baseServings"] = 4

    # Zutaten
    cleaned_ings = []
    for ing in r.get("ingredients", []):
        if not isinstance(ing, dict):
            continue
        try:
            ing["amount"] = float(ing.get("amount", 0)) or 0.0
        except (ValueError, TypeError):
            ing["amount"] = 0.0
        if ing.get("unit") not in VALID_UNITS:
            ing["unit"] = "g"
        ing.setdefault("name", "")
        if ing["name"]:
            cleaned_ings.append(ing)
    r["ingredients"] = cleaned_ings

    # Schritte
    cleaned_steps = []
    for step in r.get("steps", []):
        if not isinstance(step, dict):
            continue
        try:
            step["timerSec"] = max(0, int(step.get("timerSec", 0)))
        except (ValueError, TypeError):
            step["timerSec"] = 0
        step.setdefault("text", "")
        if step["text"]:
            cleaned_steps.append(step)
    r["steps"] = cleaned_steps

    # Notizen
    r["notes"] = [str(n) for n in r.get("notes", []) if n]

    return r


# ── Hilfsfunktionen – Dateien ─────────────────────────────────────────────────

def _result_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path("www", REZEPTE_DOMAIN, RESULT_FILE))


def _write_result(hass: HomeAssistant, data: dict) -> None:
    path = _result_path(hass)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    _LOGGER.debug("Import-Ergebnis geschrieben: status=%s", data.get("status"))


def _write_error(hass: HomeAssistant, msg: str) -> None:
    _LOGGER.error("Rezepte Import: %s", msg)
    _write_result(hass, {"ts": int(time.time()), "status": "error", "error": msg})


def _write_image_file(path: str, b64: str) -> None:
    missing = len(b64) % 4
    if missing:
        b64 += "=" * (4 - missing)
    Path(path).write_bytes(base64.b64decode(b64))


def _delete_file(path: str) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


def _provision_js(hass: HomeAssistant) -> None:
    """import.js nach /config/www/rezepte/ kopieren."""
    src = Path(__file__).parent / "www" / "import.js"
    dst_dir = Path(hass.config.path("www", REZEPTE_DOMAIN))
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst_dir / "import.js")
    _LOGGER.info("import.js bereitgestellt in %s", dst_dir)


# ── HTML-Text-Extraktion ──────────────────────────────────────────────────────

class _TextExtractor(HTMLParser):
    _SKIP = {"script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"}

    def __init__(self) -> None:
        super().__init__()
        self._depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in self._SKIP:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._depth > 0:
            self._depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._depth:
            stripped = data.strip()
            if stripped:
                self.parts.append(stripped)


def _extract_text_from_html(html: str) -> str:
    extractor = _TextExtractor()
    try:
        extractor.feed(html)
    except Exception:
        pass
    return "\n".join(extractor.parts)

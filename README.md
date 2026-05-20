# 📋 Rezepte Import – Erweiterung für ha-rezepte

Optionale Import-Erweiterung für die [ha-rezepte](https://github.com/DEIN_USERNAME/ha-rezepte) Integration.
Ermöglicht das Importieren von Rezepten aus Text, Textdateien und Weblinks direkt in die Rezepte-App.

---

## Voraussetzungen

- **[ha-rezepte](https://github.com/DEIN_USERNAME/ha-rezepte)** installiert und eingerichtet
- Ein **Konversationsagent** in HA konfiguriert (siehe unten)

---

## Installation

### Via HACS

1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL dieses Repositories, Kategorie: **Integration**
3. **Rezepte Import** installieren
4. Home Assistant **neu starten**

### Manuell

`custom_components/rezepte_import/` nach `/config/custom_components/rezepte_import/` kopieren,
dann HA neu starten.

---

## Einrichtung

1. **Einstellungen → Integrationen → + Hinzufügen → „Rezepte Import"**
2. **Konversationsagent** eintragen (entity_id des gewünschten Agenten, z. B. `conversation.google_generative_ai`)
3. **LLM Vision Anbieter** auswählen (aktuell nur für zukünftige Nutzung relevant, siehe Bild-Import)
4. Bestätigen – fertig

Der **📋-Button** erscheint automatisch in der Rezepte-App.

### Einstellungen nachträglich ändern

**Einstellungen → Integrationen → Rezepte Import → ⋮ → Neu konfigurieren**

HA lädt die Integration automatisch neu – kein Neustart nötig.

---

## Import-Methoden

### ✏️ Text

Rezepttext direkt einfügen – beliebiges Format:
- Fließtext aus einem Kochbuch abgetippt
- Strukturierte Zutatenlisten
- Aus einer Webseite kopierter Text
- Ergebnis aus Google Lens (Texterkennung aus Foto)

**Tipp:** Das zuverlässigste Verfahren. Funktioniert mit allen Konversationsagenten.

---

### 📁 Datei

| Dateityp | Verarbeitung | Hinweis |
|----------|-------------|---------|
| `.txt` | Text wird direkt analysiert | Empfohlen |
| `.jpg` `.jpeg` `.png` `.webp` | Bild-Analyse via Google AI | Siehe Bild-Import unten |
| `.heic` `.bmp` | Bild-Analyse via Google AI | Siehe Bild-Import unten |
| `.pdf` | ❌ Nicht unterstützt | Text via Google Lens extrahieren, dann Text-Tab nutzen |

---

### 🔗 Link

URL einer Rezept-Webseite einfügen. HA ruft die Seite **serverseitig** ab (kein CORS-Problem).

- Webseiten mit **JSON-LD** Rezeptdaten (Standard bei chefkoch.de, rezeptwelt.de, allrecipes.com u.v.m.) werden strukturiert ausgelesen – sehr zuverlässig
- Andere Webseiten: Seitentext wird extrahiert und analysiert – Ergebnis abhängig vom Seitenaufbau
- **Nicht geeignet** für: Login-geschützte Seiten, rein JavaScript-gerenderte Seiten ohne JSON-LD

---

### 🖼️ Bild-Import (Datei-Tab, Bilder)

Bilder werden über `google_generative_ai_conversation.generate_content` analysiert.

**Voraussetzung:** Die HA Google Generative AI Integration muss einen **Vision-fähigen** Gemini-Modell verwenden und die Aktion `generate_content` muss in der installierten Version verfügbar sein.

**Aktuell bekannte Einschränkungen:**
- LLM Vision (HACS) hat in Version 1.6.0 einen internen Bug der den Bild-Import verhindert
- `google_generative_ai_conversation.generate_content` ist erst ab bestimmten HA-Versionen verfügbar

**Empfohlener Workaround wenn Bild-Import fehlschlägt:**
1. **Google Lens** auf dem Smartphone öffnen
2. Foto des Rezepts aufnehmen → Text automatisch erkannt
3. Erkannten Text kopieren
4. Im Import-Modal **Text-Tab** öffnen und Text einfügen

---

## KI-Konfiguration

Der Import nutzt den in HA konfigurierten **Konversationsagenten** für Text- und Link-Imports.

### Google Gemini (empfohlen)

Integration: **Google Generative AI** (in HA bereits integriert)

| Modell | Anfragen/Tag (kostenlos) | Empfehlung |
|--------|--------------------------|------------|
| `gemini-2.5-flash` | 20/Tag | ❌ Zu wenig für regelmäßigen Einsatz |
| `gemini-1.5-flash` | 1.500/Tag | ✅ Empfohlen für Rezept-Import |
| `gemini-1.5-pro` | 50/Tag | ⚠️ Nur für gelegentlichen Einsatz |

**Modell wechseln:**
Einstellungen → Integrationen → Google Gemini → Konfigurieren → Modell ändern

**Rate Limit überschritten?**
Der Fehler „This model is currently experiencing high demand" oder HTTP 429 bedeutet das Tageslimit ist aufgebraucht. Am nächsten Tag automatisch wieder verfügbar, oder auf `gemini-1.5-flash` wechseln.

---

### Groq (kostenlos, sehr schnell)

Integration: **[Groq](https://github.com/Limych/ha-groq)** via HACS

| Modell | Anfragen/Minute | Tokens/Minute |
|--------|----------------|---------------|
| `llama-3.3-70b-versatile` | 30 | 6.000 |
| `llama-3.1-8b-instant` | 30 | 20.000 |

**Einrichtung:**
1. [console.groq.com](https://console.groq.com) → kostenlosen Account erstellen → API-Key generieren
2. HACS → Groq Integration installieren → HA neu starten
3. Einstellungen → Integrationen → Groq → API-Key eintragen
4. In Rezepte Import: Konversationsagent auf `conversation.groq` setzen

**Vorteil:** Sehr schnelle Antwortzeiten, großzügigeres kostenloses Kontingent als Gemini.

---

### Ollama (lokal, kostenlos, unbegrenzt)

Integration: **[Ollama](https://www.home-assistant.io/integrations/ollama/)** (HA built-in seit 2024.4)

**Voraussetzung:** Ollama läuft auf einem Server im lokalen Netzwerk (oder direkt auf dem HA-Host).

**Empfohlene Modelle für Rezept-Parsing:**
- `llama3.1:8b` – guter Kompromiss aus Geschwindigkeit und Qualität
- `mistral:7b` – schnell, gute JSON-Ausgabe
- `llama3.2:3b` – sehr schnell, für schwache Hardware

**Vorteil:** Keine Rate Limits, keine Internetverbindung nötig, keine Kosten.
**Nachteil:** Braucht Hardware (mind. 8 GB RAM für 7B-Modelle), langsamer als Cloud-Modelle.

---

### OpenAI

Integration: **[OpenAI Conversation](https://www.home-assistant.io/integrations/openai_conversation/)** (HA built-in)

Kostenpflichtig. Für Rezept-Import empfiehlt sich `gpt-4o-mini` (günstigstes Modell mit guter JSON-Ausgabe).

---

## Wie es funktioniert

```
Web-App → HA REST API → rezepte_import.*
                              ↓
              conversation.process    (Text / URL / Textdatei)
              google_generative_ai_conversation.generate_content  (Bilder)
                              ↓
         /config/www/rezepte/import_result.json
                              ↑
         Web-App pollt Ergebnis (max. 45 Sek.)
```

Die eingebaute **Struktur-Validierung** korrigiert automatisch:
- Fehlende Pflichtfelder → werden mit Standardwerten befüllt
- Ungültige Einheiten → werden auf bekannte Einheiten gemappt (g, kg, ml, l, TL, EL, Stk., Prise, n.B.)
- Falsche Datentypen → werden konvertiert (z. B. Mengenangaben als Text → Zahl)

Nach dem Import kann das Rezept direkt gespeichert oder zuerst im Formular bearbeitet werden.

---

## Fehlerbehebung

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| „High demand / Please try again later" | Gemini Rate Limit (Tageskontingent) | Auf `gemini-1.5-flash` wechseln oder warten |
| „429 Too Many Requests" | API-Kontingent überschritten | Auf anderes Modell/Anbieter wechseln |
| „Kein gültiges JSON gefunden" | KI hat kein reines JSON zurückgegeben | Erneut versuchen; ggf. Prompt des Agenten prüfen |
| „Action not found" | HA-Version zu alt für diese Aktion | HA aktualisieren oder anderen Import-Weg nutzen |
| Bild-Import schlägt fehl | LLM Vision Bug oder fehlende Vision-Unterstützung | Google Lens → Text kopieren → Text-Tab nutzen |
| Leeres Rezept nach Import | Webseite ohne JSON-LD, JS-gerendert | URL direkt im Browser öffnen, Text kopieren, Text-Tab nutzen |

---

## Lizenz

MIT

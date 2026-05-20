# 📋 Rezepte Import – Erweiterung für ha-rezepte

Optionale Import-Erweiterung für ha-rezepte.

## Features

- ✏️ **Text** – beliebigen Rezepttext einfügen und analysieren
- 📁 **Datei** – TXT-Dateien oder Rezeptfotos (JPG, PNG, WEBP) hochladen
- 🔗 **Link** – URL einer Rezept-Webseite angeben (HA ruft sie serverseitig ab)
- 🤖 Analyse via konfiguriertem **Konversationsagenten** (z. B. Google Gemini)
- 📸 Bilderkennung via **LLM Vision**
- ✅ Automatische **Struktur-Validierung** und Korrektur des geparsten Rezepts
- 👁 Vorschau vor dem Import – direkt speichern oder zuerst im Formular bearbeiten

## Voraussetzungen

- **ha-rezepte** installiert und eingerichtet
- Konversationsagent in HA konfiguriert (z. B. Google Generative AI)
- **LLM Vision** für Bild-Import (optional)

---

## Installation

### Via HACS

1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL dieses Repositories, Kategorie: **Integration**
3. **Rezepte Import** installieren und HA neu starten

### Manuell

`custom_components/rezepte_import/` nach `/config/custom_components/rezepte_import/` kopieren, HA neu starten.

---

## Einrichtung

1. **Einstellungen → Integrationen → + Hinzufügen → „Rezepte Import"**
2. **Konversationsagent** eintragen, z. B. `conversation.google_generative_ai`
3. **LLM Vision Anbieter** auswählen
4. Bestätigen

Der **📋-Button** erscheint automatisch in der Rezepte-App.

---

## Wie es funktioniert

```
Web-App → HA REST API → rezepte_import.*
                              ↓
              conversation.process     (Text / URL)
              llmvision.image_analyzer (Bilder)
                              ↓
         /config/www/rezepte/import_result.json
                              ↑
         Web-App pollt Ergebnis (max. 45 Sek.)
```

Die Struktur-Validierung korrigiert automatisch fehlende Felder,
ungültige Einheiten und falsche Datentypen.

---

## Lizenz

MIT

# Rico System V5 - PDF Pipeline

## 🚀 Übersicht

Automatische Konvertierung aller Markdown-Dateien in `docs/` zu professionell formatierten PDFs in `docs/pdf/`.

## 📋 Features

- ✅ **Automatische Konvertierung** aller Markdown-Dateien
- ✅ **Einheitliches Design** mit Rico System Theme
- ✅ **Front-Matter Support** für Deckblätter
- ✅ **Robuste Fehlerbehandlung** mit detailliertem Logging
- ✅ **CLI-Interface** für einzelne Dateien oder Batch-Verarbeitung
- ✅ **Keine Secrets** - vollständig lokale Lösung

## 🛠️ Installation

```bash
# Dependencies installieren
npm install

# PDF-Verzeichnis erstellen (automatisch)
mkdir -p docs/pdf
```

## 📖 Verwendung

### Alle Markdown-Dateien konvertieren
```bash
npm run pdf:all
```

### Einzelne Datei konvertieren
```bash
npm run pdf:one --file docs/Rico_System_Start.md
```

### Watch-Modus (optional)
```bash
npm run pdf:watch
```

## 📁 Struktur

```
docs/
├── _pdf_config.json          # PDF-Konfiguration
├── _pdf_theme.css            # Rico System Theme
├── pdf/                      # Generierte PDFs
│   ├── autopilot_spec.pdf
│   ├── Rico_System_Start.pdf
│   └── ...
└── *.md                      # Markdown-Quellen
```

## ⚙️ Konfiguration

### PDF-Einstellungen (`docs/_pdf_config.json`)
- A4-Format mit optimierten Rändern
- Header/Footer mit Seitenzahlen
- Rico System Theme
- UTF-8 Encoding

### Theme (`docs/_pdf_theme.css`)
- Elegantes, gut lesbares Design
- Smaragdgrün (#009688) für Überschriften
- Monospace-Fonts für Code
- Druck-optimierte Stile

## 🎨 Design-Features

- **Schriftarten:** Inter, Segoe UI, Roboto, Helvetica
- **Farben:** Smaragdgrün für Überschriften, neutrale Grautöne
- **Code-Blöcke:** Monospace mit Hintergrund
- **Tabellen:** Dezente Rahmen, abwechselnde Zeilen
- **Deckblätter:** Front-Matter Support für Titel, Autor, Datum

## 📊 Beispiel-Output

```
🚀 Rico System V5 - PDF Pipeline gestartet
📁 Gefunden: 13 Markdown-Dateien
📄 Konvertiere: docs/Rico_System_Start.md → docs/pdf/Rico_System_Start.pdf
✅ Erfolgreich: docs/pdf/Rico_System_Start.pdf
...

📊 Zusammenfassung:
✅ Erfolgreich: 13
❌ Fehlgeschlagen: 0
⏱️  Dauer: 44.6s

🎉 PDF-Pipeline erfolgreich abgeschlossen!
```

## 🔧 Technische Details

- **Engine:** md-to-pdf mit Headless Chromium
- **Dependencies:** md-to-pdf, globby, fs-extra
- **Plattform:** Windows, macOS, Linux
- **Keine Secrets:** Vollständig lokale Lösung

## 🚨 Fehlerbehandlung

- Einzelne Fehler stoppen nicht die Batch-Verarbeitung
- Detaillierte Fehlermeldungen mit Dateinamen
- Exit Code 1 bei Fehlern
- Robuste Pfad-Behandlung (Windows/macOS)

## 📝 Front-Matter Support

```yaml
---
title: "Dokumenttitel"
subtitle: "Untertitel"
author: "Autor"
date: "2024-01-01"
---
```

Generiert automatisch ein elegantes Deckblatt.

## 🎯 Akzeptanzkriterien

- ✅ Alle `docs/*.md` → `docs/pdf/*.pdf`
- ✅ Konsistentes Layout und Theme
- ✅ Keine Änderung an Markdown-Quellen
- ✅ Keine Secrets oder .env-Abhängigkeiten
- ✅ Windows/macOS kompatibel
- ✅ Robuste Fehlerbehandlung

---

**Rico System V5 - PDF Pipeline erfolgreich implementiert! 🎉**

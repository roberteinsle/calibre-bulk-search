# Calibre Bulk Search

Eine Web-App zur Massensuche von Buchtiteln in deiner Calibre-Bibliothek.

## Features

- 📚 Massensuche von Buchtiteln in Calibre
- ✅ Anzeige gefundener/nicht gefundener Bücher
- 🔗 Direkte Links zu Büchern in Calibre-Web
- 📝 Flexible Eingabe (Titel, "Autor - Titel", Copy/Paste von Webseiten)

## Voraussetzungen

- Python 3.8 oder höher
- Laufender Calibre Content Server (lokal oder im Netzwerk)

## Installation

1. Repository klonen:
```bash
git clone https://github.com/roberteinsle/calibre-bulk-search.git
cd calibre-bulk-search
```

2. Virtuelle Umgebung erstellen und aktivieren:
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Dependencies installieren:
```bash
pip install -r requirements.txt
```

4. Konfiguration einrichten:
```bash
# .env.example nach .env kopieren
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# .env bearbeiten und deine Calibre-Server-URL eintragen
```

## Konfiguration

Bearbeite die `.env` Datei:

```env
CALIBRE_SERVER_URL=http://192.168.10.59:8722
CALIBRE_LIBRARY_ID=Calibre-Bibliothek
APP_HOST=0.0.0.0
APP_PORT=8000
```

## Verwendung

1. Server starten:
```bash
uvicorn main:app --reload
```

2. Browser öffnen:
```
http://localhost:8000
```

3. Buchtitel eingeben (eine Zeile pro Buch):
```
Drohnenland
Der Schwarm von Frank Schätzing
Stephen King - Es
```

4. Auf "Suchen" klicken und Ergebnisse sehen!

## Entwicklung

### Projekt-Struktur
```
calibre-bulk-search/
├── .env.example          # Beispiel-Konfiguration
├── .gitignore
├── requirements.txt
├── README.md
├── CLAUDE.md
├── main.py              # FastAPI Backend
├── calibre_client.py    # Calibre API Client
├── text_parser.py       # Buch-Titel Parser
├── config.py            # Konfiguration
└── static/
    ├── index.html       # Frontend
    ├── style.css
    └── app.js
```

### Server im Development-Modus starten
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Technologie-Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS/JavaScript mit Bootstrap
- **HTTP Client**: httpx (async)
- **Calibre API**: AJAX-Endpoints (`/ajax/search/`)

## Lizenz

Private Repository - Nicht für öffentliche Nutzung bestimmt.

## Autor

Robert Einsle (robert@einsle.com)

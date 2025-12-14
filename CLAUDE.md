# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Calibre Bulk Search is a web application for searching multiple book titles simultaneously in a Calibre library. It provides a simple web interface for bulk searching and displays results with direct links to Calibre-Web.

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS/JavaScript with Bootstrap 5
- **HTTP Client**: httpx (async)
- **Configuration**: pydantic-settings with .env file
- **Calibre Integration**: AJAX endpoints (`/ajax/search/`)

## Development Commands

### Initial Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

### Running the Application

```bash
# Development mode with auto-reload
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000

# Using Python directly
python main.py
```

Access the application at: `http://localhost:8000`

## Architecture

### Backend Components

1. **main.py**: FastAPI application with endpoints
   - `GET /`: Serves the main HTML page
   - `GET /health`: Health check endpoint
   - `POST /api/search`: Bulk search endpoint
   - `GET /api/book/{book_id}`: Get book details

2. **calibre_client.py**: Async HTTP client for Calibre Content Server
   - `search_book()`: Single book search
   - `bulk_search()`: Parallel search for multiple books
   - `get_book_details()`: Fetch detailed book information
   - `get_book_url()`: Generate Calibre-Web URLs

3. **text_parser.py**: Text parsing utilities
   - `parse_input()`: Parse multi-line input into search queries
   - `_clean_line()`: Handle various input formats (Titel, Autor - Titel, etc.)
   - `extract_title_only()`: Extract title from query

4. **config.py**: Configuration management using pydantic-settings
   - Loads from `.env` file
   - Provides settings instance

### Frontend Components

- **index.html**: Main UI with search form and results display
- **style.css**: Custom styling with animations
- **app.js**: Client-side logic for API calls and result rendering

## Calibre API Integration

The app uses Calibre Content Server's AJAX endpoints:

- **Search**: `GET /ajax/search/{library_id}?query={search_term}`
- **Book Details**: `GET /ajax/book/{book_id}/{library_id}`

Response format:
```json
{
  "total_num": 11,
  "book_ids": [3133, 2560, 3128],
  "query": "search term",
  "library_id": "Calibre-Bibliothek"
}
```

## Key Patterns

### Async/Await
All Calibre API calls use async/await for parallel processing of multiple search queries.

### Error Handling
- HTTP errors are caught and returned in the response
- Failed searches are marked with `found: false`
- Network errors are logged to console

### Input Parsing
Supports multiple input formats:
- Simple title: "Drohnenland"
- Author - Title: "Frank Schätzing - Der Schwarm"
- Title by Author: "Es von Stephen King"

## Configuration

Required environment variables in `.env`:

```env
CALIBRE_SERVER_URL=http://192.168.10.59:8722
CALIBRE_LIBRARY_ID=Calibre-Bibliothek
APP_HOST=0.0.0.0
APP_PORT=8000
```

## Important Notes

- The app is designed for local network use
- No authentication required (Calibre server must be accessible)
- All searches are performed in parallel for performance
- Results include direct links to Calibre-Web interface
- Private repository - credentials must not be committed

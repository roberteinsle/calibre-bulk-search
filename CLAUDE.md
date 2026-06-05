# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Calibre Bulk Search is a web application for searching multiple book titles simultaneously in a Calibre library. It provides a simple web interface for bulk searching and displays results with direct links to Calibre-Web.

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS/JavaScript with Bootstrap 5
- **HTTP Client**: httpx (async)
- **Configuration**: pydantic-settings with config.env file
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

# Create config.env file from example
copy config.env.example config.env  # Windows
# cp config.env.example config.env  # Linux/Mac
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
   - `GET /health`: Health check endpoint (returns Calibre server URL)
   - `POST /api/search`: Bulk search endpoint (request: `{text: string}`, response: `BulkSearchResponse`)
   - `GET /api/book/{book_id}`: Get book details from Calibre
   - `GET /api/test-scenenzbs?query={query}`: Test SceneNZBs URL generation

2. **calibre_client.py**: Async HTTP client for Calibre Content Server
   - `bulk_search()`: Parallel search for multiple books using `asyncio.gather()` — the live search path
   - `_smart_search()`: Multi-strategy search with fallback patterns (called per-query by `bulk_search`)
   - `_generate_search_strategies()`: Creates multiple search patterns from a query
   - `_search_with_query()`: Internal method to execute a search with a shared client
   - `search_book()`: Standalone single-book search — NOT used by `bulk_search` (legacy/utility; spins up its own client)
   - `get_book_details()`: Fetch detailed book information (backs `/api/book/{id}`, independent of search)
   - `get_book_url()`: Generate Calibre-Web URLs (format: `{base}/#book_id={id}&library_id={lib}&panel=book_details`)
   - `get_scenenzbs_url()`: Generate SceneNZBs search URLs with author/title parsing

3. **text_parser.py**: Text parsing utilities
   - `parse_input()`: Parse multi-line input into search queries
   - `_clean_line()`: Handle various input formats (Titel, Autor - Titel, etc.)
   - `extract_title_only()`: Extract title from query

4. **config.py**: Configuration management using pydantic-settings
   - Loads from `config.env` file
   - Provides settings instance

### Frontend Components

- **index.html**: Main UI with search form and results display
- **style.css**: Custom styling with animations
- **app.js**: Client-side logic for API calls and result rendering

### Data Flow

1. **User Input** → Frontend (`app.js`)
   - User enters multi-line text with book titles
   - Form submission triggers POST to `/api/search`

2. **Text Parsing** → `BookTitleParser`
   - Splits input by newlines
   - Cleans each line (removes bullets, numbers, extra whitespace)
   - Handles various author/title formats
   - Returns list of clean search queries

3. **Bulk Search** → `CalibreClient.bulk_search()`
   - Spawns parallel searches using `asyncio.gather()`
   - For each query, runs `_smart_search()` with multiple strategies
   - Tries strategies sequentially until results found
   - Returns list of results with book IDs, URLs, and SceneNZBs links

4. **Response Assembly** → `main.py`
   - Converts raw results to `SearchResult` models
   - Counts found/not found books
   - Returns `BulkSearchResponse` with statistics

5. **Display** → Frontend (`app.js`)
   - Renders results with color coding (green = found, red = not found)
   - Shows Calibre-Web links for found books
   - Shows SceneNZBs links for all books

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

### Smart Search Strategy
The `CalibreClient._smart_search()` method implements a multi-strategy search approach:
1. **Strategy Generation**: For queries like "Carlo Masala: Weltunordnung", generates multiple search patterns:
   - Title only: "Weltunordnung"
   - Calibre format: `title:"Weltunordnung" author:"Carlo Masala"`
   - Combined: "Weltunordnung Carlo Masala"
   - Original query as fallback
2. **Sequential Execution**: Tries each strategy in order until results are found
3. **Early Exit**: Stops searching once any strategy returns results

### Async/Await
All Calibre API calls use async/await for parallel processing:
- `bulk_search()` executes all queries concurrently using `asyncio.gather()`
- Shares a single `httpx.AsyncClient` across parallel searches for connection pooling
- Handles exceptions individually with `return_exceptions=True`

### Error Handling
- HTTP errors are caught and returned in the response
- Failed searches are marked with `found: false`
- Network errors are logged to console
- Each search failure doesn't interrupt other parallel searches

### Input Parsing
`BookTitleParser._clean_line()` supports multiple input formats:
- Simple title: "Drohnenland" → unchanged
- `Author - Title`: "Frank Schätzing - Der Schwarm" → **reordered** to "Der Schwarm Frank Schätzing" (only ` - ` with spaces; en/em-dashes are not split here)
- `Title by/von/from Author`: "Es von Stephen King" / "It by Stephen King" → kept as-is (whole line is the query)
- Cleans list markers (bullets, numbers, dashes at start) and collapses whitespace

Note: the parser and `CalibreClient` parse separators independently. `_clean_line` reorders `Author - Title`, while `get_scenenzbs_url()` and `_generate_search_strategies()` split `:`, en-dash, and em-dash too. Keep these in sync when changing separator handling.

### SceneNZBs Integration
For books not found in Calibre, the app generates SceneNZBs search URLs:
- Parses query to extract author and title separately
- Removes year information in parentheses (e.g., "(2024)")
- URL format: `https://scenenzbs.com/books?author={author}&title={title}`
- Falls back to general search if parsing fails

## Configuration

Required environment variables in `config.env` (loaded by `config.py` via pydantic-settings; keys are case-insensitive). Defaults are also hardcoded in `Settings`, so the app runs even without `config.env`:

```env
CALIBRE_SERVER_URL=http://192.168.10.59:8722
CALIBRE_LIBRARY_ID=Calibre-Bibliothek
APP_HOST=0.0.0.0
APP_PORT=8000
```

Note: `CALIBRE_SERVER_URL` is concatenated directly (e.g. `{base}/ajax/search/...`), so a trailing slash yields a double slash in the path. Calibre tolerates it, but prefer no trailing slash.

## Development Notes

### No Tests
This project currently has no test suite. When making changes:
- Test manually by running the app and trying various input formats
- Use `/api/test-scenenzbs?query=...` to test SceneNZBs URL generation
- Verify the Calibre server is accessible via `/health` endpoint

### CORS Configuration
The app has CORS enabled with `allow_origins=["*"]` for local development. This allows the frontend to call the API from any origin.

### Static Files
Static files are served via FastAPI's `StaticFiles` mount at `/static`. The root path `/` serves `static/index.html` directly.

### httpx vs requests
The project uses `httpx` instead of `requests` for HTTP calls because:
- Native async/await support for parallel searches
- Connection pooling with shared `AsyncClient`
- Better performance for concurrent requests

## Important Notes

- The app is designed for local network use
- No authentication required (Calibre server must be accessible)
- All searches are performed in parallel for performance
- Results include direct links to Calibre-Web interface
- Private repository - credentials must not be committed
- Calibre-Web deep-link format (from `get_book_url`): `{CALIBRE_SERVER_URL}/#book_id={id}&library_id={library}&panel=book_details`

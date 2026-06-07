from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os

from calibre_client import CalibreClient
from text_parser import BookTitleParser
from config import settings


app = FastAPI(
    title="Calibre Bulk Search",
    description="Web app for bulk searching books in Calibre library",
    version="1.0.3"
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Calibre client
calibre_client = CalibreClient()


class SearchRequest(BaseModel):
    text: str


class SearchAttempt(BaseModel):
    strategy: str
    status: int | None = None
    total_num: int = 0
    book_count: int = 0
    error: str | None = None
    elapsed_ms: int = 0


class SearchResult(BaseModel):
    query: str
    found: bool
    book_id: int | None = None
    book_url: str | None = None
    total_num: int = 0
    all_book_ids: List[int] = []
    error: str | None = None
    scenenzbs_url: str | None = None
    log: List[SearchAttempt] = []


class BulkSearchResponse(BaseModel):
    results: List[SearchResult]
    total_queries: int
    found_count: int
    not_found_count: int
    calibre_server: str


@app.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "calibre_server": settings.calibre_server_url}


@app.get("/api/test-scenenzbs")
async def test_scenenzbs(query: str):
    """Test SceneNZBs URL generation."""
    url = calibre_client.get_scenenzbs_url(query)
    return {"query": query, "scenenzbs_url": url}


@app.post("/api/search", response_model=BulkSearchResponse)
async def bulk_search(request: SearchRequest):
    """
    Bulk search for books in Calibre library.

    Args:
        request: SearchRequest with text containing book titles (one per line)

    Returns:
        BulkSearchResponse with search results for each query
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="No search text provided")

    # Parse input text into individual queries
    queries = BookTitleParser.parse_input(request.text)

    if not queries:
        raise HTTPException(status_code=400, detail="No valid book titles found in input")

    # Perform bulk search
    raw_results = await calibre_client.bulk_search(queries)

    # Convert to response format
    results = []
    found_count = 0
    not_found_count = 0

    for result in raw_results:
        search_result = SearchResult(
            query=result["query"],
            found=result["found"],
            book_id=result.get("book_id"),
            book_url=result.get("book_url"),
            total_num=result.get("total_num", 0),
            all_book_ids=result.get("all_book_ids", []),
            error=result.get("error"),
            scenenzbs_url=result.get("scenenzbs_url"),
            log=result.get("log", [])
        )
        results.append(search_result)

        if result["found"]:
            found_count += 1
        else:
            not_found_count += 1

    return BulkSearchResponse(
        results=results,
        total_queries=len(queries),
        found_count=found_count,
        not_found_count=not_found_count,
        calibre_server=settings.calibre_server_url
    )


@app.get("/api/book/{book_id}")
async def get_book_details(book_id: int):
    """
    Get detailed information about a specific book.

    Args:
        book_id: Calibre book ID

    Returns:
        Book details from Calibre
    """
    details = await calibre_client.get_book_details(book_id)

    if not details:
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")

    return details


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )

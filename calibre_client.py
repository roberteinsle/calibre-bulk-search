import httpx
import re
import asyncio
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, quote
from config import settings


class CalibreClient:
    def __init__(self):
        self.base_url = settings.calibre_server_url
        self.library_id = settings.calibre_library_id
        self.timeout = 10.0

    def _get_auth(self) -> Optional[httpx.Auth]:
        """
        Build the httpx auth object for the Calibre server, or None if no
        credentials are configured.
        """
        if not settings.calibre_username:
            return None
        if settings.calibre_auth_mode.lower() == "digest":
            return httpx.DigestAuth(settings.calibre_username, settings.calibre_password)
        return httpx.BasicAuth(settings.calibre_username, settings.calibre_password)

    async def search_book(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search for a book in Calibre using the AJAX search endpoint.

        Args:
            query: Search query (book title, author, etc.)

        Returns:
            Dict with search results or None if error occurred
        """
        if not query or not query.strip():
            return None

        encoded_query = quote(query.strip())
        search_url = f"{self.base_url}/ajax/search/{self.library_id}"
        params = {
            "query": query.strip(),
            "num": 10,
            "offset": 0,
            "sort": "title",
            "sort_order": "asc"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, auth=self._get_auth()) as client:
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP error occurred while searching for '{query}': {e}")
            return None
        except Exception as e:
            print(f"Error occurred while searching for '{query}': {e}")
            return None

    async def get_book_details(self, book_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a book.

        Args:
            book_id: Calibre book ID

        Returns:
            Dict with book details or None if error occurred
        """
        details_url = f"{self.base_url}/ajax/book/{book_id}/{self.library_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, auth=self._get_auth()) as client:
                response = await client.get(details_url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP error occurred while getting details for book {book_id}: {e}")
            return None
        except Exception as e:
            print(f"Error occurred while getting details for book {book_id}: {e}")
            return None

    def get_book_url(self, book_id: int) -> str:
        """
        Generate Calibre-Web URL for a specific book.

        Args:
            book_id: Calibre book ID

        Returns:
            Direct URL to the book in Calibre-Web
        """
        return f"{self.base_url}/#book_id={book_id}&library_id={self.library_id}&panel=book_details"

    def get_scenenzbs_url(self, query: str) -> str:
        """
        Generate SceneNZBs search URL for a book query.

        Args:
            query: Original search query

        Returns:
            SceneNZBs search URL with author and title
        """
        author = ""
        title = ""

        # Parse query to extract author and title
        if ':' in query:
            parts = query.split(':', 1)
            author = parts[0].strip()
            title = parts[1].strip()
        elif ' - ' in query or ' – ' in query or ' — ' in query:
            # Handle different dash types: hyphen, en-dash, em-dash
            separator = ' - ' if ' - ' in query else (' – ' if ' – ' in query else ' — ')
            parts = query.split(separator, 1)
            author = parts[0].strip()
            title = parts[1].strip()
        elif ' von ' in query.lower():
            # Find case-insensitive position
            match = re.search(r'\s+von\s+', query, re.IGNORECASE)
            if match:
                title = query[:match.start()].strip()
                author = query[match.end():].strip()
            else:
                title = query.strip()
        elif ' by ' in query.lower():
            # Find case-insensitive position
            match = re.search(r'\s+by\s+', query, re.IGNORECASE)
            if match:
                title = query[:match.start()].strip()
                author = query[match.end():].strip()
            else:
                title = query.strip()
        else:
            # Just use the whole query as title
            title = query.strip()

        # Remove year in parentheses if present
        title = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
        author = re.sub(r'\s*\(\d{4}\)\s*$', '', author)

        # URL encode for SceneNZBs
        author_encoded = quote(author) if author else ""
        title_encoded = quote(title) if title else ""

        if author_encoded and title_encoded:
            return f"https://scenenzbs.com/books?author={author_encoded}&title={title_encoded}"
        elif title_encoded:
            return f"https://scenenzbs.com/books?title={title_encoded}"
        else:
            return f"https://scenenzbs.com/books?q={quote(query)}"

    async def bulk_search(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Search for multiple books in parallel using multiple search strategies.

        Args:
            queries: List of search queries

        Returns:
            List of search results with metadata
        """
        results = []

        async with httpx.AsyncClient(timeout=self.timeout, auth=self._get_auth()) as client:
            tasks = []
            for query in queries:
                if query and query.strip():
                    tasks.append(self._smart_search(client, query.strip()))

            search_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(search_results):
                query = queries[i].strip()
                scenenzbs_url = self.get_scenenzbs_url(query)

                if isinstance(result, Exception):
                    results.append({
                        "query": query,
                        "found": False,
                        "error": str(result),
                        "book_ids": [],
                        "total_num": 0,
                        "scenenzbs_url": scenenzbs_url
                    })
                elif result and result.get("book_ids"):
                    first_book_id = result["book_ids"][0]
                    results.append({
                        "query": query,
                        "found": True,
                        "book_id": first_book_id,
                        "book_url": self.get_book_url(first_book_id),
                        "total_num": result.get("total_num", 0),
                        "all_book_ids": result.get("book_ids", []),
                        "scenenzbs_url": scenenzbs_url
                    })
                else:
                    results.append({
                        "query": query,
                        "found": False,
                        "book_ids": [],
                        "total_num": 0,
                        "scenenzbs_url": scenenzbs_url
                    })

        return results

    async def _smart_search(self, client: httpx.AsyncClient, query: str) -> Optional[Dict[str, Any]]:
        """
        Smart search with multiple strategies.
        Tries different search patterns until a result is found.
        """
        # Generate search strategies
        strategies = self._generate_search_strategies(query)

        # Try each strategy until we find results
        for strategy in strategies:
            result = await self._search_with_query(client, strategy)
            if result and result.get("book_ids"):
                return result

        # No results found with any strategy
        return None

    def _generate_search_strategies(self, query: str) -> List[str]:
        """
        Generate multiple search strategies from a query.

        Examples:
        "Carlo Masala: Weltunordnung" ->
            1. "Weltunordnung"  (title only)
            2. "Carlo Masala Weltunordnung" (author + title)
            3. "Weltunordnung Carlo Masala" (title + author)
            4. "Carlo Masala: Weltunordnung" (original)
        """
        strategies = []

        # Parse different formats
        # Format: "Author: Title" or "Author - Title" or "Author – Title"
        if ':' in query or ' - ' in query or ' – ' in query or ' — ' in query:
            # Handle different separators
            if ':' in query:
                separator = ':'
            elif ' - ' in query:
                separator = ' - '
            elif ' – ' in query:
                separator = ' – '
            else:
                separator = ' — '

            parts = query.split(separator, 1)
            if len(parts) == 2:
                author = parts[0].strip()
                title = parts[1].strip()

                # Strategy 1: Title only (most specific)
                strategies.append(title)

                # Strategy 2: "title:author" (Calibre format)
                strategies.append(f'title:"{title}" author:"{author}"')

                # Strategy 3: Title + Author (combined search)
                strategies.append(f"{title} {author}")

                # Strategy 4: Author + Title
                strategies.append(f"{author} {title}")

        # Format: "Title by Author" or "Title von Author"
        elif ' by ' in query.lower() or ' von ' in query.lower():
            # Try "by" first
            match = re.search(r'\s+by\s+', query, re.IGNORECASE)
            if not match:
                # Try "von"
                match = re.search(r'\s+von\s+', query, re.IGNORECASE)

            if match:
                title = query[:match.start()].strip()
                author = query[match.end():].strip()

                strategies.append(title)
                strategies.append(f'title:"{title}" author:"{author}"')
                strategies.append(f"{title} {author}")

        # Always add original query as fallback
        if query not in strategies:
            strategies.append(query)

        return strategies

    async def _search_with_query(self, client: httpx.AsyncClient, query: str) -> Optional[Dict[str, Any]]:
        """
        Internal method to search with a given httpx client.
        """
        search_url = f"{self.base_url}/ajax/search/{self.library_id}"
        params = {
            "query": query,
            "num": 10,
            "offset": 0,
            "sort": "title",
            "sort_order": "asc"
        }

        try:
            response = await client.get(search_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise e

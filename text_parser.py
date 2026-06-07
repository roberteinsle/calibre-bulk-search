import re
from typing import List


class BookTitleParser:
    """
    Parser for extracting book titles from various text formats.

    Supports formats like:
    - "Book Title"
    - "Author - Book Title"
    - "Book Title by Author"
    - "Book Title von Author"
    - Mixed text from web copy/paste
    """

    @staticmethod
    def parse_input(text: str) -> List[str]:
        """
        Parse multi-line text input and extract search queries.

        Args:
            text: Multi-line string with book titles

        Returns:
            List of cleaned search queries
        """
        if not text or not text.strip():
            return []

        lines = text.strip().split('\n')
        queries = []

        for line in lines:
            cleaned = BookTitleParser._clean_line(line)
            if cleaned:
                queries.append(cleaned)

        return queries

    @staticmethod
    def _clean_line(line: str) -> str:
        """
        Clean a single line into a search query.

        The author/title structure is intentionally preserved so that the
        smart search (CalibreClient._generate_search_strategies) can derive
        multiple search strategies from it. All of these formats are handled
        consistently downstream:
        - "Title"
        - "Author - Title"   (also en-dash "–" / em-dash "—")
        - "Author: Title"
        - "Title by Author" / "Title von Author"

        This method only strips list markers and normalizes whitespace.
        """
        if not line or not line.strip():
            return ""

        # Remove common list markers (bullets, numbers, dashes at start)
        line = re.sub(r'^[\s\-\*\•\d\.\)]+', '', line)

        # Remove extra whitespace
        line = ' '.join(line.split())

        return line.strip()

    @staticmethod
    def extract_title_only(query: str) -> str:
        """
        Extract only the title part from a query, removing author information.

        Args:
            query: Search query that may contain author info

        Returns:
            Title only
        """
        # Remove "by Author", "von Author" etc.
        patterns = [
            r'\s+by\s+.+$',
            r'\s+von\s+.+$',
            r'\s+from\s+.+$',
        ]

        result = query
        for pattern in patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        return result.strip()

"""
BaseCrawler - Abstract base class for all site-specific crawlers.

All plugins must inherit from this class and implement its abstract methods.
This ensures a consistent interface across all crawlers while allowing
site-specific customization.

Example:
    >>> from src.core.base_crawler import BaseCrawler
    >>> from bs4 import BeautifulSoup
    >>> import requests
    >>>
    >>> class MyCustomCrawler(BaseCrawler):
    ...     def fetch_page(self, url, params):
    ...         response = requests.get(url, params=params)
    ...         return BeautifulSoup(response.text, 'html.parser')
    ...
    ...     def parse_list(self, soup):
    ...         items = []
    ...         for row in soup.select('table tr'):
    ...             items.append({'title': row.select_one('a').text})
    ...         return items
    ...
    ...     def parse_detail(self, soup, item):
    ...         item['content'] = soup.select_one('.content').text
    ...         return item
    ...
    ...     def build_params(self, page, start_date, end_date):
    ...         return {'page': page, 'start': start_date, 'end': end_date}
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from bs4 import BeautifulSoup


class BaseCrawler(ABC):
    """
    Abstract base class for all site crawlers.

    All site-specific crawler plugins must inherit from this class and
    implement the four abstract methods: fetch_page, parse_list, parse_detail,
    and build_params.

    This abstraction allows the UI and data export logic to work with any
    crawler without knowing the implementation details.
    """

    @abstractmethod
    def fetch_page(self, url: str, params: Dict[str, Any]) -> Optional[BeautifulSoup]:
        """
        Fetch a web page and return parsed HTML.

        Args:
            url: The target URL to fetch
            params: Query parameters to include in the request

        Returns:
            BeautifulSoup object containing the parsed HTML, or None if the
            request fails

        Raises:
            RequestException: If HTTP request fails
            ConnectionError: If network connection is lost

        Example:
            >>> crawler = MyCustomCrawler()
            >>> soup = crawler.fetch_page(
            ...     'https://example.com/board',
            ...     {'page': 1, 'category': 'news'}
            ... )
            >>> print(soup.title.text)
            Example Board - Page 1
        """
        raise NotImplementedError("Subclasses must implement fetch_page()")

    @abstractmethod
    def parse_list(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Parse a list page and extract item metadata.

        This method should extract basic information from a board list page,
        such as post number, title, author, date, etc. It should NOT fetch
        detail pages - that's handled separately.

        Args:
            soup: BeautifulSoup object containing the list page HTML

        Returns:
            List of dictionaries, where each dict contains item metadata.
            Common keys include: 'number', 'title', 'date', 'url', 'author'

        Example:
            >>> soup = BeautifulSoup('<table>...</table>', 'html.parser')
            >>> items = crawler.parse_list(soup)
            >>> print(items[0])
            {
                'number': '12345',
                'title': 'Sample Post',
                'date': datetime(2025, 10, 5),
                'url': 'https://example.com/board/12345'
            }
        """
        raise NotImplementedError("Subclasses must implement parse_list()")

    @abstractmethod
    def parse_detail(self, soup: BeautifulSoup, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a detail page and enrich the item with additional data.

        This method receives an item dict from parse_list() and should add
        more detailed information by parsing the detail page HTML.

        Args:
            soup: BeautifulSoup object containing the detail page HTML
            item: The item dict from parse_list() to enrich

        Returns:
            The enriched item dict with additional fields like 'content',
            'attachments', 'contact_info', etc.

        Example:
            >>> item = {'title': 'Sample', 'url': 'https://...'}
            >>> soup = BeautifulSoup('<div class="content">...</div>', 'html.parser')
            >>> enriched = crawler.parse_detail(soup, item)
            >>> print(enriched['content'])
            This is the full post content...
        """
        raise NotImplementedError("Subclasses must implement parse_detail()")

    @abstractmethod
    def build_params(
        self,
        page: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Build query parameters for a page request.

        This method constructs the query parameters needed to fetch a specific
        page with optional date filtering. The parameter names and format are
        site-specific.

        Args:
            page: Page number (1-indexed)
            start_date: Filter posts from this date onwards (inclusive)
            end_date: Filter posts up to this date (inclusive)

        Returns:
            Dictionary of query parameters to pass to requests.get()

        Example:
            >>> params = crawler.build_params(
            ...     page=1,
            ...     start_date=date(2025, 1, 1),
            ...     end_date=date(2025, 10, 5)
            ... )
            >>> print(params)
            {
                'pageIndex': 1,
                'pageUnit': 10,
                'ntcStartDt': '2025-01-01',
                'ntcEndDt': '2025-10-05'
            }
        """
        raise NotImplementedError("Subclasses must implement build_params()")


if __name__ == "__main__":
    # Example usage demonstrating how to subclass BaseCrawler
    import requests

    class DemoCrawler(BaseCrawler):
        """Minimal example crawler for demonstration."""

        def fetch_page(self, url: str, params: Dict[str, Any]) -> Optional[BeautifulSoup]:
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.text, 'html.parser')
            except Exception as e:
                print(f"Error fetching page: {e}")
                return None

        def parse_list(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
            items = []
            for row in soup.select('table tbody tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    items.append({
                        'title': cells[1].get_text(strip=True),
                        'number': cells[0].get_text(strip=True)
                    })
            return items

        def parse_detail(self, soup: BeautifulSoup, item: Dict[str, Any]) -> Dict[str, Any]:
            content_elem = soup.select_one('.content')
            if content_elem:
                item['content'] = content_elem.get_text(strip=True)
            return item

        def build_params(
            self,
            page: int,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
        ) -> Dict[str, Any]:
            params = {'page': page}
            if start_date:
                params['start'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                params['end'] = end_date.strftime('%Y-%m-%d')
            return params

    # Test instantiation
    crawler = DemoCrawler()
    print("✓ DemoCrawler instantiated successfully")
    print(f"✓ build_params(1): {crawler.build_params(1)}")
    print(f"✓ build_params(2, date.today()): {crawler.build_params(2, date.today())}")

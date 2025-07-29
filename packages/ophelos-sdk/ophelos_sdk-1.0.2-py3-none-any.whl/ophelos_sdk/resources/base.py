"""
Base resource class for Ophelos API resources.
"""

from typing import Optional, Dict, Any, List, Union, Type, TypeVar, cast, Generator
from ..http_client import HTTPClient
from ..models import BaseOphelosModel, PaginatedResponse

T = TypeVar("T", bound=BaseOphelosModel)


class BaseResource:
    """Base class for all API resource managers."""

    def __init__(self, http_client: HTTPClient):
        """
        Initialize base resource.

        Args:
            http_client: HTTP client instance for making requests
        """
        self.http_client = http_client

    def _build_expand_params(self, expand: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Build expand parameters for API requests.

        Args:
            expand: List of fields to expand

        Returns:
            Dictionary with expand parameters
        """
        params: Dict[str, Any] = {}
        if expand:
            for i, field in enumerate(expand):
                params[f"expand[{i}]"] = field
        return params

    def _build_list_params(
        self,
        limit: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Build parameters for list requests.

        Args:
            limit: Maximum number of results to return
            after: Cursor for pagination (after this ID)
            before: Cursor for pagination (before this ID)
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Returns:
            Dictionary with query parameters
        """
        params: Dict[str, Any] = {}

        if limit is not None:
            params["limit"] = limit
        if after:
            params["after"] = after
        if before:
            params["before"] = before

        params.update(self._build_expand_params(expand))
        params.update(kwargs)

        return params

    def _build_search_params(
        self,
        query: str,
        limit: Optional[int] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Build parameters for search requests.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Returns:
            Dictionary with query parameters
        """
        params: Dict[str, Any] = {"query": query}

        if limit is not None:
            params["limit"] = limit

        params.update(self._build_expand_params(expand))
        params.update(kwargs)

        return params

    def _parse_response(
        self, response_data: Dict[str, Any], model_class: Optional[Type[T]] = None
    ) -> Union[T, Dict[str, Any]]:
        """
        Parse API response data into model instance.

        Args:
            response_data: Raw response data from API
            model_class: Pydantic model class to parse into

        Returns:
            Parsed model instance or raw data
        """
        if model_class and response_data:
            try:
                return model_class(**response_data)
            except Exception:
                # Fallback to raw data if parsing fails
                return response_data
        return response_data

    def _parse_model_response(self, response_data: Dict[str, Any], model_class: Type[T]) -> T:
        """
        Parse API response data into model instance, ensuring correct type.

        Args:
            response_data: Raw response data from API
            model_class: Pydantic model class to parse into

        Returns:
            Parsed model instance
        """
        result = self._parse_response(response_data, model_class)
        return cast(T, result)

    def _parse_list_response(
        self, response_data: Dict[str, Any], model_class: Optional[Type[BaseOphelosModel]] = None
    ) -> PaginatedResponse:
        """
        Parse paginated list response.

        Args:
            response_data: Raw response data from API
            model_class: Pydantic model class for list items

        Returns:
            Paginated response with parsed items
        """
        if not response_data:
            return PaginatedResponse(data=[])

        items = response_data.get("data", [])

        if model_class:
            parsed_items = []
            for i, item in enumerate(items):
                try:
                    if isinstance(item, dict):
                        parsed_items.append(model_class(**item))
                    else:
                        # Already a model object
                        parsed_items.append(item)
                except Exception as e:
                    # Better error handling - print debug info
                    print(f"Warning: Failed to parse item {i} to {model_class.__name__}: {e}")
                    print(f"Item data: {item}")
                    # Fallback to raw data if parsing fails
                    parsed_items.append(item)

            parsed_response = response_data.copy()
            parsed_response["data"] = parsed_items
            return PaginatedResponse(**parsed_response)

        return PaginatedResponse(**response_data)

    def iterate(
        self,
        limit_per_page: int = 50,
        max_pages: Optional[int] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Generator[Any, None, None]:
        """
        Generator that yields individual objects with automatic pagination.

        This method provides memory-efficient iteration over large datasets
        by fetching pages on-demand and yielding individual objects.

        Args:
            limit_per_page: Number of items per page (default: 50)
            max_pages: Maximum number of pages to fetch (None = unlimited)
            expand: List of fields to expand
            **kwargs: Additional query parameters for filtering

        Yields:
            Individual model objects

        Raises:
            AttributeError: If the resource doesn't implement list functionality

        Example:
            # Process first 200 items (4 pages of 50)
            for item in resource.iterate(limit_per_page=50, max_pages=4):
                process_item(item)

            # Process all items with specific filters
            for item in resource.iterate(expand=["related"], status="active"):
                process_item(item)
        """
        if not hasattr(self, "list"):
            raise AttributeError(f"{self.__class__.__name__} does not support list functionality")

        after_cursor = None
        pages_fetched = 0

        while True:
            # Check page limit
            if max_pages and pages_fetched >= max_pages:
                break

            # Fetch current page - using getattr to satisfy type checker
            list_method = getattr(self, "list")
            page = list_method(
                limit=limit_per_page, after=after_cursor, before=None, expand=expand, **kwargs
            )

            pages_fetched += 1

            # Yield individual items
            for item in page.data:
                yield item

            # Check if we have more pages
            if not page.has_more or not page.data:
                break

            last_item = page.data[-1]
            if hasattr(last_item, "id"):
                after_cursor = last_item.id
            elif isinstance(last_item, dict):
                after_cursor = last_item.get("id")
            else:
                break  # Can't get ID, stop iteration

    def iterate_search(
        self,
        query: str,
        limit_per_page: int = 50,
        max_pages: Optional[int] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Generator[Any, None, None]:
        """
        Generator that yields individual objects from search results with pagination.

        Note: This method requires the resource to implement a 'search' method.

        Args:
            query: Search query string
            limit_per_page: Number of items per page (default: 50)
            max_pages: Maximum number of pages to fetch (None = unlimited)
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Yields:
            Individual model objects matching the search criteria

        Raises:
            AttributeError: If the resource doesn't implement search functionality

        Example:
            # Search for specific items
            for item in resource.iterate_search("status:active", max_pages=5):
                process_item(item)
        """
        if not hasattr(self, "search"):
            raise AttributeError(f"{self.__class__.__name__} does not support search functionality")

        pages_fetched = 0

        while True:
            # Check page limit
            if max_pages and pages_fetched >= max_pages:
                break

            # Fetch current page of search results - using getattr to satisfy type checker
            search_method = getattr(self, "search")
            page = search_method(query=query, limit=limit_per_page, expand=expand, **kwargs)

            pages_fetched += 1

            # Yield individual items
            for item in page.data:
                yield item

            # Check if we have more pages
            if not page.has_more or not page.data:
                break

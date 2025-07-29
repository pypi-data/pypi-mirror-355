"""
Customers resource manager for Ophelos API.
"""

from typing import Optional, Dict, Any, List
from .base import BaseResource
from ..models import Customer, PaginatedResponse


class CustomersResource(BaseResource):
    """Resource manager for customer operations."""

    def list(
        self,
        limit: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> PaginatedResponse:
        """
        List customers.

        Args:
            limit: Maximum number of results to return
            after: Cursor for pagination (after this ID)
            before: Cursor for pagination (before this ID)
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Returns:
            Paginated response with customer data
        """
        params = self._build_list_params(limit, after, before, expand, **kwargs)
        response_data = self.http_client.get("customers", params=params)
        return self._parse_list_response(response_data, Customer)

    def search(
        self,
        query: str,
        limit: Optional[int] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> PaginatedResponse:
        """
        Search customers.

        Args:
            query: Search query string (e.g., "email:john@example.com")
            limit: Maximum number of results to return
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Returns:
            Paginated response with customer data
        """
        params = self._build_search_params(query, limit, expand, **kwargs)
        response_data = self.http_client.get("customers/search", params=params)
        return self._parse_list_response(response_data, Customer)

    def get(self, customer_id: str, expand: Optional[List[str]] = None) -> Customer:
        """
        Get a specific customer by ID.

        Args:
            customer_id: Customer ID
            expand: List of fields to expand

        Returns:
            Customer instance
        """
        params = self._build_expand_params(expand)
        response_data = self.http_client.get(f"customers/{customer_id}", params=params)
        return self._parse_model_response(response_data, Customer)

    def create(self, data: Dict[str, Any], expand: Optional[List[str]] = None) -> Customer:
        """
        Create a new customer.

        Args:
            data: Customer data
            expand: List of fields to expand

        Returns:
            Created customer instance
        """
        if expand:
            params = self._build_expand_params(expand)
            response_data = self.http_client.post("customers", data=data, params=params)
        else:
            response_data = self.http_client.post("customers", data=data)
        return self._parse_model_response(response_data, Customer)

    def update(
        self, customer_id: str, data: Dict[str, Any], expand: Optional[List[str]] = None
    ) -> Customer:
        """
        Update a customer.

        Args:
            customer_id: Customer ID
            data: Updated customer data
            expand: List of fields to expand

        Returns:
            Updated customer instance
        """
        if expand:
            params = self._build_expand_params(expand)
            response_data = self.http_client.put(
                f"customers/{customer_id}", data=data, params=params
            )
        else:
            response_data = self.http_client.put(f"customers/{customer_id}", data=data)
        return self._parse_model_response(response_data, Customer)

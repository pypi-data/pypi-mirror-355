"""
Payments resource for Ophelos API.
"""

from typing import List, Optional, Dict, Any
from .base import BaseResource
from ..models import Payment, PaginatedResponse


class PaymentsResource(BaseResource):
    """Manages payment operations."""

    def list(
        self,
        limit: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> PaginatedResponse:
        """
        List all payments.

        Args:
            limit: Maximum number of results to return
            after: Cursor for pagination (after this ID)
            before: Cursor for pagination (before this ID)
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Returns:
            Paginated list of payments
        """
        params = self._build_list_params(
            limit=limit, after=after, before=before, expand=expand, **kwargs
        )
        response_data = self.http_client.get("payments", params=params)
        return self._parse_list_response(response_data, Payment)

    def search(
        self,
        query: str,
        limit: Optional[int] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> PaginatedResponse:
        """
        Search payments.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Returns:
            Paginated search results
        """
        params = self._build_search_params(query, limit, expand, **kwargs)
        response_data = self.http_client.get("payments/search", params=params)
        return self._parse_list_response(response_data, Payment)

    def get(self, payment_id: str, expand: Optional[List[str]] = None) -> Payment:
        """
        Get a specific payment by ID.

        Args:
            payment_id: Payment ID
            expand: List of fields to expand

        Returns:
            Payment instance
        """
        params = self._build_expand_params(expand)
        response_data = self.http_client.get(f"payments/{payment_id}", params=params)
        return self._parse_model_response(response_data, Payment)

"""
Payouts resource for Ophelos API.
"""

from typing import List, Optional, Dict, Any
from .base import BaseResource
from ..models import Payout, PaginatedResponse


class PayoutsResource(BaseResource):
    """Manages payout operations."""

    def list(
        self,
        limit: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> PaginatedResponse:
        """
        List all payouts.

        Args:
            limit: Maximum number of results to return
            after: Cursor for pagination (after this ID)
            before: Cursor for pagination (before this ID)
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Returns:
            Paginated list of payouts
        """
        params = self._build_list_params(
            limit=limit, after=after, before=before, expand=expand, **kwargs
        )
        response_data = self.http_client.get("payouts", params=params)
        return self._parse_list_response(response_data, Payout)

    def search(
        self,
        query: str,
        limit: Optional[int] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> PaginatedResponse:
        """
        Search payouts.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Returns:
            Paginated search results
        """
        params = self._build_search_params(query, limit, expand, **kwargs)
        response_data = self.http_client.get("payouts/search", params=params)
        return self._parse_list_response(response_data, Payout)

    def get(self, payout_id: str, expand: Optional[List[str]] = None) -> Payout:
        """
        Get a specific payout by ID.

        Args:
            payout_id: Payout ID
            expand: List of fields to expand

        Returns:
            Payout instance
        """
        params = self._build_expand_params(expand)
        response_data = self.http_client.get(f"payouts/{payout_id}", params=params)
        return self._parse_model_response(response_data, Payout)

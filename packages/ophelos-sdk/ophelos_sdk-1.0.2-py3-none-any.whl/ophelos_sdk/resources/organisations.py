"""
Organisations resource for Ophelos API.
"""

from typing import List, Optional, Dict, Any
from .base import BaseResource
from ..models import Organisation, Payment, PaginatedResponse


class OrganisationsResource(BaseResource):
    """Manages organisation operations."""

    def list(
        self,
        limit: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> PaginatedResponse:
        """
        List all organisations.

        Args:
            limit: Maximum number of results to return
            after: Cursor for pagination (after this ID)
            before: Cursor for pagination (before this ID)
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Returns:
            Paginated list of organisations
        """
        params = self._build_list_params(
            limit=limit, after=after, before=before, expand=expand, **kwargs
        )
        response_data = self.http_client.get("organisations", params=params)
        return self._parse_list_response(response_data, Organisation)

    def get(self, org_id: str, expand: Optional[List[str]] = None) -> Organisation:
        """
        Get a specific organisation by ID.

        Args:
            org_id: Organisation ID
            expand: List of fields to expand

        Returns:
            Organisation instance
        """
        params = self._build_expand_params(expand)
        response_data = self.http_client.get(f"organisations/{org_id}", params=params)
        return self._parse_model_response(response_data, Organisation)

    def create(self, data: Dict[str, Any], expand: Optional[List[str]] = None) -> Organisation:
        """
        Create a new organisation.

        Args:
            data: Organisation data
            expand: List of fields to expand

        Returns:
            Created organisation instance
        """
        params = self._build_expand_params(expand)
        response_data = self.http_client.post("organisations", data=data, params=params)
        return self._parse_model_response(response_data, Organisation)

    def update(
        self, org_id: str, data: Dict[str, Any], expand: Optional[List[str]] = None
    ) -> Organisation:
        """
        Update an organisation.

        Args:
            org_id: Organisation ID
            data: Updated organisation data
            expand: List of fields to expand

        Returns:
            Updated organisation instance
        """
        params = self._build_expand_params(expand)
        response_data = self.http_client.patch(f"organisations/{org_id}", data=data, params=params)
        return self._parse_model_response(response_data, Organisation)

    def create_contact_detail(
        self, org_id: str, data: Dict[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Create a contact detail for an organisation.

        Args:
            org_id: Organisation ID
            data: Contact detail data

        Returns:
            Created contact detail
        """
        return self.http_client.post(f"organisations/{org_id}/contact_details", data=data)

    def list_payments(
        self,
        org_id: str,
        limit: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> PaginatedResponse:
        """
        List payments for an organisation.

        Args:
            org_id: Organisation ID
            limit: Maximum number of results to return
            after: Cursor for pagination (after this ID)
            before: Cursor for pagination (before this ID)
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Returns:
            Paginated response with payment data
        """
        params = self._build_list_params(limit, after, before, expand, **kwargs)
        response_data = self.http_client.get(f"organisations/{org_id}/payments", params=params)
        return self._parse_list_response(response_data, Payment)

    def search_payments(
        self,
        org_id: str,
        query: str,
        limit: Optional[int] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> PaginatedResponse:
        """
        Search payments for an organisation.

        Args:
            org_id: Organisation ID
            query: Search query string
            limit: Maximum number of results to return
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Returns:
            Paginated response with payment data
        """
        params = self._build_search_params(query, limit, expand, **kwargs)
        response_data = self.http_client.get(
            f"organisations/{org_id}/payments/search", params=params
        )
        return self._parse_list_response(response_data, Payment)

    def list_members(
        self,
        org_id: str,
        limit: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        expand: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> PaginatedResponse:
        """
        List organisation members.

        Args:
            org_id: Organisation ID
            limit: Maximum number of results to return
            after: Cursor for pagination (after this ID)
            before: Cursor for pagination (before this ID)
            expand: List of fields to expand
            **kwargs: Additional query parameters

        Returns:
            Paginated list of organisation members
        """
        params = self._build_list_params(
            limit=limit, after=after, before=before, expand=expand, **kwargs
        )
        response_data = self.http_client.get(f"organisations/{org_id}/members", params=params)
        return self._parse_list_response(response_data)

    def invite_member(
        self, org_id: str, data: Dict[str, Any], expand: Optional[List[str]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Invite a member to an organisation.

        Args:
            org_id: Organisation ID
            data: Invitation data (email, role, etc.)
            expand: List of fields to expand
            **kwargs: Additional parameters

        Returns:
            Invitation response data
        """
        params = self._build_expand_params(expand)
        params.update(kwargs)
        return self.http_client.post(f"organisations/{org_id}/members", data=data, params=params)

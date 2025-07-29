"""
Tenants resource manager for Ophelos API.
"""

from typing import Optional, Dict, Any, List
from .base import BaseResource
from ..models import Tenant


class TenantsResource(BaseResource):
    """Resource manager for tenant operations."""

    def get_me(self, expand: Optional[List[str]] = None) -> Tenant:
        """
        Get current tenant information.

        Args:
            expand: List of fields to expand

        Returns:
            Current tenant instance
        """
        params = self._build_expand_params(expand)
        response_data = self.http_client.get("tenants/me", params=params)
        return self._parse_model_response(response_data, Tenant)

    def update_me(self, data: Dict[str, Any], expand: Optional[List[str]] = None) -> Tenant:
        """
        Update current tenant information.

        Args:
            data: Updated tenant data
            expand: List of fields to expand

        Returns:
            Updated tenant instance
        """
        params = self._build_expand_params(expand)
        response_data = self.http_client.patch("tenants/me", data=data, params=params)
        return self._parse_model_response(response_data, Tenant)

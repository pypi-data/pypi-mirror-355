"""
Unit tests for Ophelos SDK client.
"""

import pytest
from unittest.mock import Mock, patch

from ophelos_sdk.client import OphelosClient
from ophelos_sdk.auth import OAuth2Authenticator
from ophelos_sdk.http_client import HTTPClient


class TestOphelosClient:
    """Test cases for OphelosClient."""

    @pytest.fixture
    def client_config(self):
        """Client configuration for testing."""
        return {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "audience": "test_audience",
            "environment": "staging",
        }

    @patch("ophelos_sdk.client.OAuth2Authenticator")
    @patch("ophelos_sdk.client.HTTPClient")
    def test_client_initialization_without_tenant_id(
        self, mock_http_client, mock_authenticator, client_config
    ):
        """Test client initialization without tenant_id."""
        mock_auth_instance = Mock(spec=OAuth2Authenticator)
        mock_authenticator.return_value = mock_auth_instance

        mock_http_instance = Mock(spec=HTTPClient)
        mock_http_client.return_value = mock_http_instance

        client = OphelosClient(**client_config)

        # Verify authenticator was created correctly
        mock_authenticator.assert_called_once_with(
            client_id="test_client_id",
            client_secret="test_client_secret",
            audience="test_audience",
            environment="staging",
        )

        # Verify HTTP client was created without tenant_id
        mock_http_client.assert_called_once_with(
            authenticator=mock_auth_instance,
            base_url="https://api.ophelos.dev",  # staging environment
            timeout=30,
            max_retries=3,
            tenant_id=None,
        )

        # Verify resource managers are initialized
        assert hasattr(client, "debts")
        assert hasattr(client, "customers")
        assert hasattr(client, "organisations")

    @patch("ophelos_sdk.client.OAuth2Authenticator")
    @patch("ophelos_sdk.client.HTTPClient")
    def test_client_initialization_with_tenant_id(
        self, mock_http_client, mock_authenticator, client_config
    ):
        """Test client initialization with tenant_id."""
        mock_auth_instance = Mock(spec=OAuth2Authenticator)
        mock_authenticator.return_value = mock_auth_instance

        mock_http_instance = Mock(spec=HTTPClient)
        mock_http_client.return_value = mock_http_instance

        tenant_id = "test-tenant-123"
        client = OphelosClient(**client_config, tenant_id=tenant_id)

        # Verify HTTP client was created with tenant_id
        mock_http_client.assert_called_once_with(
            authenticator=mock_auth_instance,
            base_url="https://api.ophelos.dev",  # staging environment
            timeout=30,
            max_retries=3,
            tenant_id=tenant_id,
        )

    @patch("ophelos_sdk.client.OAuth2Authenticator")
    @patch("ophelos_sdk.client.HTTPClient")
    def test_client_environment_urls(self, mock_http_client, mock_authenticator, client_config):
        """Test that different environments use correct URLs."""
        mock_auth_instance = Mock(spec=OAuth2Authenticator)
        mock_authenticator.return_value = mock_auth_instance

        mock_http_instance = Mock(spec=HTTPClient)
        mock_http_client.return_value = mock_http_instance

        # Test staging (default)
        client_config["environment"] = "staging"
        OphelosClient(**client_config)
        args, kwargs = mock_http_client.call_args
        assert kwargs["base_url"] == "https://api.ophelos.dev"

        # Test production
        mock_http_client.reset_mock()
        client_config["environment"] = "production"
        OphelosClient(**client_config)
        args, kwargs = mock_http_client.call_args
        assert kwargs["base_url"] == "https://api.ophelos.com"

        # Test development
        mock_http_client.reset_mock()
        client_config["environment"] = "development"
        OphelosClient(**client_config)
        args, kwargs = mock_http_client.call_args
        assert kwargs["base_url"] == "http://api.localhost:3000"

    @patch("ophelos_sdk.client.OAuth2Authenticator")
    @patch("ophelos_sdk.client.HTTPClient")
    def test_client_custom_timeout_and_retries(
        self, mock_http_client, mock_authenticator, client_config
    ):
        """Test client with custom timeout and retry settings."""
        mock_auth_instance = Mock(spec=OAuth2Authenticator)
        mock_authenticator.return_value = mock_auth_instance

        mock_http_instance = Mock(spec=HTTPClient)
        mock_http_client.return_value = mock_http_instance

        OphelosClient(**client_config, timeout=60, max_retries=5, tenant_id="custom-tenant")

        # Verify HTTP client was created with custom settings
        mock_http_client.assert_called_once_with(
            authenticator=mock_auth_instance,
            base_url="https://api.ophelos.dev",
            timeout=60,
            max_retries=5,
            tenant_id="custom-tenant",
        )

    @patch("ophelos_sdk.client.OAuth2Authenticator")
    @patch("ophelos_sdk.client.HTTPClient")
    def test_tenant_id_passed_to_all_requests(
        self, mock_http_client, mock_authenticator, client_config
    ):
        """Test that tenant_id is passed through to HTTP client for all resource operations."""
        mock_auth_instance = Mock(spec=OAuth2Authenticator)
        mock_authenticator.return_value = mock_auth_instance

        mock_http_instance = Mock(spec=HTTPClient)
        mock_http_client.return_value = mock_http_instance

        tenant_id = "integration-tenant-456"
        client = OphelosClient(**client_config, tenant_id=tenant_id)

        # Verify that the HTTP client instance used by resources has the tenant_id
        # All resources should use the same http_client instance
        assert client.debts.http_client == mock_http_instance
        assert client.customers.http_client == mock_http_instance
        assert client.payments.http_client == mock_http_instance

        # Verify the HTTP client was initialized with the tenant_id
        args, kwargs = mock_http_client.call_args
        assert kwargs["tenant_id"] == tenant_id

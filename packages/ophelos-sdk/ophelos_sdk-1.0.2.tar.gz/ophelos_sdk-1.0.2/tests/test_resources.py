"""
Unit tests for Ophelos SDK resource managers.
"""

import pytest
from unittest.mock import Mock

from ophelos_sdk.resources import DebtsResource, CustomersResource, PaymentsResource
from ophelos_sdk.http_client import HTTPClient
from ophelos_sdk.models import Debt, Customer, Payment, PaginatedResponse


class TestBaseResource:
    """Test cases for base resource functionality."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing."""
        return Mock(spec=HTTPClient)

    @pytest.fixture
    def debts_resource(self, mock_http_client):
        """Create debts resource for testing."""
        return DebtsResource(mock_http_client)

    def test_build_expand_params(self, debts_resource):
        """Test building expand parameters."""
        # No expand fields
        params = debts_resource._build_expand_params()
        assert params == {}

        # Single expand field
        params = debts_resource._build_expand_params(["customer"])
        assert params == {"expand[0]": "customer"}

        # Multiple expand fields
        params = debts_resource._build_expand_params(["customer", "payments"])
        assert params == {"expand[0]": "customer", "expand[1]": "payments"}

    def test_build_list_params(self, debts_resource):
        """Test building list parameters."""
        params = debts_resource._build_list_params(
            limit=10, after="debt_123", before="debt_456", expand=["customer"], extra_param="value"
        )

        expected = {
            "limit": 10,
            "after": "debt_123",
            "before": "debt_456",
            "expand[0]": "customer",
            "extra_param": "value",
        }
        assert params == expected

    def test_build_search_params(self, debts_resource):
        """Test building search parameters."""
        params = debts_resource._build_search_params(
            query="status:paying", limit=5, expand=["customer"], org_id="org_123"
        )

        expected = {
            "query": "status:paying",
            "limit": 5,
            "expand[0]": "customer",
            "org_id": "org_123",
        }
        assert params == expected


class TestDebtsResource:
    """Test cases for debts resource."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing."""
        return Mock(spec=HTTPClient)

    @pytest.fixture
    def debts_resource(self, mock_http_client):
        """Create debts resource for testing."""
        return DebtsResource(mock_http_client)

    def test_list_debts(
        self, debts_resource, mock_http_client, sample_debt_data, sample_paginated_response
    ):
        """Test listing debts."""
        # Mock response - keep data as raw dicts, not parsed objects
        mock_response = sample_paginated_response.copy()
        mock_response["data"] = [sample_debt_data]
        mock_http_client.get.return_value = mock_response

        result = debts_resource.list(limit=10, expand=["customer"])

        mock_http_client.get.assert_called_once_with(
            "debts", params={"limit": 10, "expand[0]": "customer"}
        )
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 1
        # First item should be parsed as Debt
        assert isinstance(result.data[0], Debt)

    def test_search_debts(
        self, debts_resource, mock_http_client, sample_debt_data, sample_paginated_response
    ):
        """Test searching debts."""
        mock_response = sample_paginated_response.copy()
        mock_response["data"] = [sample_debt_data]
        mock_http_client.get.return_value = mock_response

        result = debts_resource.search("status:paying", limit=5)

        mock_http_client.get.assert_called_once_with(
            "debts/search", params={"query": "status:paying", "limit": 5}
        )
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 1
        assert isinstance(result.data[0], Debt)

    def test_get_debt(self, debts_resource, mock_http_client, sample_debt_data):
        """Test getting a specific debt."""
        mock_http_client.get.return_value = sample_debt_data

        result = debts_resource.get("debt_123", expand=["customer"])

        mock_http_client.get.assert_called_once_with(
            "debts/debt_123", params={"expand[0]": "customer"}
        )
        assert isinstance(result, Debt)
        assert result.id == sample_debt_data["id"]

    def test_create_debt(self, debts_resource, mock_http_client, sample_debt_data):
        """Test creating a debt."""
        create_data = {
            "customer_id": "cust_123",
            "organisation_id": "org_123",
            "total_amount": 10000,
        }
        mock_http_client.post.return_value = sample_debt_data

        result = debts_resource.create(create_data)

        mock_http_client.post.assert_called_once_with("debts", data=create_data)
        assert isinstance(result, Debt)

    def test_update_debt(self, debts_resource, mock_http_client, sample_debt_data):
        """Test updating a debt."""
        update_data = {"metadata": {"updated": True}}
        mock_http_client.put.return_value = sample_debt_data

        result = debts_resource.update("debt_123", update_data)

        mock_http_client.put.assert_called_once_with("debts/debt_123", data=update_data)
        assert isinstance(result, Debt)

    def test_delete_debt(self, debts_resource, mock_http_client):
        """Test deleting a debt."""
        mock_http_client.delete.return_value = {"deleted": True}

        result = debts_resource.delete("debt_123")

        mock_http_client.delete.assert_called_once_with("debts/debt_123")
        assert result == {"deleted": True}

    def test_debt_lifecycle_operations(self, debts_resource, mock_http_client, sample_debt_data):
        """Test debt lifecycle operations."""
        mock_http_client.post.return_value = sample_debt_data

        # Test ready operation
        result = debts_resource.ready("debt_123")
        mock_http_client.post.assert_called_with("debts/debt_123/ready", data={})
        assert isinstance(result, Debt)

        # Test pause operation
        pause_data = {"reason": "customer request"}
        result = debts_resource.pause("debt_123", pause_data)
        mock_http_client.post.assert_called_with("debts/debt_123/pause", data=pause_data)

        # Test resume operation
        result = debts_resource.resume("debt_123")
        mock_http_client.post.assert_called_with("debts/debt_123/resume", data={})

        # Test withdraw operation
        withdraw_data = {"reason": "fraud"}
        result = debts_resource.withdraw("debt_123", withdraw_data)
        mock_http_client.post.assert_called_with("debts/debt_123/withdraw", data=withdraw_data)

        # Test dispute operation
        dispute_data = {"reason": "amount disputed", "details": "Customer claims incorrect amount"}
        result = debts_resource.dispute("debt_123", dispute_data)
        mock_http_client.post.assert_called_with("debts/debt_123/dispute", data=dispute_data)

    def test_debt_payments_operations(
        self, debts_resource, mock_http_client, sample_payment_data, sample_paginated_response
    ):
        """Test debt payment operations."""
        # Test list payments
        mock_response = sample_paginated_response.copy()
        mock_response["data"] = [sample_payment_data]
        mock_http_client.get.return_value = mock_response

        result = debts_resource.list_payments("debt_123", limit=5)
        mock_http_client.get.assert_called_with("debts/debt_123/payments", params={"limit": 5})
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 1
        assert isinstance(result.data[0], Payment)

        # Test create payment
        payment_data = {"amount": 5000, "transaction_at": "2024-01-15T10:00:00Z"}
        mock_http_client.post.return_value = sample_payment_data

        result = debts_resource.create_payment("debt_123", payment_data)
        mock_http_client.post.assert_called_with("debts/debt_123/payments", data=payment_data)
        assert isinstance(result, Payment)

        # Test get payment
        mock_http_client.get.return_value = sample_payment_data
        result = debts_resource.get_payment("debt_123", "pay_456")
        mock_http_client.get.assert_called_with("debts/debt_123/payments/pay_456")
        assert isinstance(result, Payment)

    def test_get_debt_summary(self, debts_resource, mock_http_client):
        """Test getting debt summary."""
        summary_data = {"total_amount": 10000, "paid_amount": 3000, "remaining": 7000}
        mock_http_client.get.return_value = summary_data

        result = debts_resource.get_summary("debt_123")

        mock_http_client.get.assert_called_once_with("debts/debt_123/summary")
        assert result == summary_data


class TestCustomersResource:
    """Test cases for customers resource."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing."""
        return Mock(spec=HTTPClient)

    @pytest.fixture
    def customers_resource(self, mock_http_client):
        """Create customers resource for testing."""
        return CustomersResource(mock_http_client)

    def test_list_customers(
        self, customers_resource, mock_http_client, sample_customer_data, sample_paginated_response
    ):
        """Test listing customers."""
        mock_response = sample_paginated_response.copy()
        mock_response["data"] = [sample_customer_data]
        mock_http_client.get.return_value = mock_response

        result = customers_resource.list(limit=10)

        mock_http_client.get.assert_called_once_with("customers", params={"limit": 10})
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 1
        assert isinstance(result.data[0], Customer)

    def test_search_customers(
        self, customers_resource, mock_http_client, sample_customer_data, sample_paginated_response
    ):
        """Test searching customers."""
        mock_response = sample_paginated_response.copy()
        mock_response["data"] = [sample_customer_data]
        mock_http_client.get.return_value = mock_response

        result = customers_resource.search("email:john@example.com")

        mock_http_client.get.assert_called_once_with(
            "customers/search", params={"query": "email:john@example.com"}
        )
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 1
        assert isinstance(result.data[0], Customer)

    def test_get_customer(self, customers_resource, mock_http_client, sample_customer_data):
        """Test getting a specific customer."""
        mock_http_client.get.return_value = sample_customer_data

        result = customers_resource.get("cust_123")

        mock_http_client.get.assert_called_once_with("customers/cust_123", params={})
        assert isinstance(result, Customer)
        assert result.id == sample_customer_data["id"]

    def test_create_customer(self, customers_resource, mock_http_client, sample_customer_data):
        """Test creating a customer."""
        create_data = {"first_name": "John", "last_name": "Doe", "organisation_id": "org_123"}
        mock_http_client.post.return_value = sample_customer_data

        result = customers_resource.create(create_data)

        mock_http_client.post.assert_called_once_with("customers", data=create_data)
        assert isinstance(result, Customer)

    def test_update_customer(self, customers_resource, mock_http_client, sample_customer_data):
        """Test updating a customer."""
        update_data = {"phone": "+447700900123"}
        mock_http_client.put.return_value = sample_customer_data

        result = customers_resource.update("cust_123", update_data)

        mock_http_client.put.assert_called_once_with("customers/cust_123", data=update_data)
        assert isinstance(result, Customer)


class TestPaymentsResource:
    """Test cases for payments resource."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing."""
        return Mock(spec=HTTPClient)

    @pytest.fixture
    def payments_resource(self, mock_http_client):
        """Create payments resource for testing."""
        return PaymentsResource(mock_http_client)

    def test_list_payments(
        self, payments_resource, mock_http_client, sample_payment_data, sample_paginated_response
    ):
        """Test listing payments."""
        mock_response = sample_paginated_response.copy()
        mock_response["data"] = [sample_payment_data]
        mock_http_client.get.return_value = mock_response

        result = payments_resource.list(limit=20)

        mock_http_client.get.assert_called_once_with("payments", params={"limit": 20})
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 1
        assert isinstance(result.data[0], Payment)

    def test_search_payments(
        self, payments_resource, mock_http_client, sample_payment_data, sample_paginated_response
    ):
        """Test searching payments."""
        mock_response = sample_paginated_response.copy()
        mock_response["data"] = [sample_payment_data]
        mock_http_client.get.return_value = mock_response

        result = payments_resource.search("status:succeeded")

        mock_http_client.get.assert_called_once_with(
            "payments/search", params={"query": "status:succeeded"}
        )
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 1
        assert isinstance(result.data[0], Payment)

    def test_get_payment(self, payments_resource, mock_http_client, sample_payment_data):
        """Test getting a specific payment."""
        mock_http_client.get.return_value = sample_payment_data

        result = payments_resource.get("pay_123")

        mock_http_client.get.assert_called_once_with("payments/pay_123", params={})
        assert isinstance(result, Payment)
        assert result.id == sample_payment_data["id"]


class TestResourceErrorHandling:
    """Test error handling in resource managers."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing."""
        return Mock(spec=HTTPClient)

    @pytest.fixture
    def debts_resource(self, mock_http_client):
        """Create debts resource for testing."""
        return DebtsResource(mock_http_client)

    def test_parsing_fallback_on_error(self, debts_resource, mock_http_client):
        """Test that parsing falls back to raw data on error."""
        # Return invalid data that can't be parsed into a Debt model
        invalid_debt_data = {"invalid": "data", "missing_required_fields": True}
        mock_http_client.get.return_value = invalid_debt_data

        result = debts_resource.get("debt_123")

        # Should return raw data instead of raising an error
        assert result == invalid_debt_data

    def test_list_parsing_fallback(self, debts_resource, mock_http_client):
        """Test that list parsing falls back to raw data on individual item errors."""
        # Mix of valid and invalid data
        response_data = {
            "object": "list",
            "data": [
                {  # Valid debt data
                    "id": "debt_123",
                    "object": "debt",
                    "status": {
                        "value": "prepared",
                        "whodunnit": "system",
                        "context": None,
                        "reason": None,
                        "updated_at": "2024-01-15T10:00:00Z",
                    },
                    "customer": "cust_123",
                    "organisation": "org_123",
                    "customer_id": "cust_123",
                    "organisation_id": "org_123",
                    "summary": {"amount_total": 10000, "amount_paid": 0, "amount_remaining": 10000},
                    "created_at": "2024-01-15T10:00:00Z",
                    "updated_at": "2024-01-15T10:00:00Z",
                },
                {"invalid": "data"},  # Invalid debt data
            ],
            "has_more": False,
        }
        mock_http_client.get.return_value = response_data

        result = debts_resource.list()

        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 2
        # First item should be parsed as Debt
        assert isinstance(result.data[0], Debt)
        # Second item should remain as raw dict
        assert isinstance(result.data[1], dict)
        assert result.data[1] == {"invalid": "data"}

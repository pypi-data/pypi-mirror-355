"""
Main Ophelos API client.
"""

from typing import Optional

from .auth import OAuth2Authenticator
from .http_client import HTTPClient
from .resources import (
    DebtsResource,
    CustomersResource,
    OrganisationsResource,
    PaymentsResource,
    InvoicesResource,
    WebhooksResource,
    PaymentPlansResource,
    CommunicationsResource,
    PayoutsResource,
    TenantsResource,
)


class OphelosClient:
    """
    Main client for the Ophelos API.

    This client provides access to all Ophelos API resources and handles
    authentication, HTTP requests, and response parsing.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        audience: str,
        environment: str = "development",
        timeout: int = 30,
        max_retries: int = 3,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize the Ophelos API client.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            audience: API audience/identifier
            environment: "development", "staging", or "production"
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            tenant_id: Optional tenant ID to include in all requests as OPHELOS_TENANT_ID header

        Note:
            Retry requests automatically use exponential backoff with jitter (0-1.5s randomness)
            to prevent thundering herd problems when multiple clients retry simultaneously.

        Example:
            ```python
            client = OphelosClient(
                client_id="your_client_id",
                client_secret="your_client_secret",
                audience="your_audience",
                environment="development",
                tenant_id="your_tenant_id"  # Optional: adds OPHELOS_TENANT_ID header
            )
            ```
        """
        if environment == "production":
            base_url = "https://api.ophelos.com"
        elif environment == "development":
            base_url = "http://api.localhost:3000"
        else:  # staging (default)
            base_url = "https://api.ophelos.dev"

        self.authenticator = OAuth2Authenticator(
            client_id=client_id,
            client_secret=client_secret,
            audience=audience,
            environment=environment,
        )

        self.http_client = HTTPClient(
            authenticator=self.authenticator,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            tenant_id=tenant_id,
        )
        self.debts = DebtsResource(self.http_client)
        self.customers = CustomersResource(self.http_client)
        self.organisations = OrganisationsResource(self.http_client)
        self.payments = PaymentsResource(self.http_client)
        self.invoices = InvoicesResource(self.http_client)
        self.webhooks = WebhooksResource(self.http_client)
        self.payment_plans = PaymentPlansResource(self.http_client)
        self.communications = CommunicationsResource(self.http_client)
        self.payouts = PayoutsResource(self.http_client)
        self.tenants = TenantsResource(self.http_client)

    def test_connection(self) -> bool:
        """
        Test the API connection by making a simple authenticated request.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.tenants.get_me()
            return True
        except Exception:
            return False

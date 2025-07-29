"""
Resource managers for Ophelos API endpoints.
"""

from .base import BaseResource
from .debts import DebtsResource
from .customers import CustomersResource
from .organisations import OrganisationsResource
from .payments import PaymentsResource
from .invoices import InvoicesResource
from .webhooks import WebhooksResource
from .payment_plans import PaymentPlansResource
from .communications import CommunicationsResource
from .payouts import PayoutsResource
from .tenants import TenantsResource

__all__ = [
    "BaseResource",
    "DebtsResource",
    "CustomersResource",
    "OrganisationsResource",
    "PaymentsResource",
    "InvoicesResource",
    "WebhooksResource",
    "PaymentPlansResource",
    "CommunicationsResource",
    "PayoutsResource",
    "TenantsResource",
]

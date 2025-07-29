"""
Ophelos Python SDK

Official Python SDK for the Ophelos API - a comprehensive debt management platform.
"""

from .client import OphelosClient
from .exceptions import (
    OphelosError,
    OphelosAPIError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ConflictError,
    ForbiddenError,
    ServerError,
)
from .webhooks import WebhookHandler, construct_event
from .models import (
    BaseOphelosModel,
    Debt,
    Customer,
    Organisation,
    Payment,
    PaymentPlan,
    Invoice,
    LineItem,
    Communication,
    Webhook,
    WebhookEvent,
    Tenant,
    Payout,
    PaginatedResponse,
    DebtStatus,
    PaymentStatus,
    ContactDetailType,
    Currency,
)

__version__ = "1.0.1"
__author__ = "Ophelos"
__email__ = "support@ophelos.com"

__all__ = [
    "OphelosClient",
    # Exceptions
    "OphelosError",
    "OphelosAPIError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    "ConflictError",
    "ForbiddenError",
    "ServerError",
    # Webhook handling
    "WebhookHandler",
    "construct_event",
    # Models
    "BaseOphelosModel",
    "Debt",
    "Customer",
    "Organisation",
    "Payment",
    "PaymentPlan",
    "Invoice",
    "LineItem",
    "Communication",
    "Webhook",
    "WebhookEvent",
    "Tenant",
    "Payout",
    "PaginatedResponse",
    # Enums
    "DebtStatus",
    "PaymentStatus",
    "ContactDetailType",
    "Currency",
]

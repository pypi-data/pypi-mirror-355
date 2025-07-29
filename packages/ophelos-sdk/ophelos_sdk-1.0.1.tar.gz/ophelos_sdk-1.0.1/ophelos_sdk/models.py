"""
Pydantic models for Ophelos API data structures.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List, Union
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class BaseOphelosModel(BaseModel):
    """Base model for all Ophelos API resources."""

    model_config = ConfigDict(
        extra="allow",
        use_enum_values=True,
    )


class DebtStatus(str, Enum):
    """Debt status enumeration."""

    # Client flow
    INITIALIZING = "initializing"  # Debt is being created
    PREPARED = "prepared"  # Client informs us that the debt is ready to process
    PAUSED = "paused"  # Client requests to pause the debt
    WITHDRAWN = "withdrawn"  # Client withdraws the debt
    DELETED = "deleted"  # Debt is deleted before being processed

    # Ophelos Flow
    ANALYSING = "analysing"  # Debt is being analysed by Data
    RESUMED = "resumed"  # Debt is resumed after being paused
    CONTACTED = "contacted"  # Communication has been sent to the customer regarding this debt
    CONTACT_ESTABLISHED = (
        "contact_established"  # Communication has been established with the customer
    )
    CONTACT_FAILED = "contact_failed"  # Communication with the customer has failed
    ENRICHING = "enriching"  # Debt is being enriched by Data
    RETURNED = "returned"  # Debt is returned to the client
    DISCHARGED = "discharged"  # Debt is discharged/written-off

    # Customer Flow
    ARRANGING = "arranging"  # Customer is arranging payment
    PAYING = "paying"  # Customer is paying
    SETTLED = "settled"  # Debt is settled (POSITIVE END)
    PAID = "paid"  # Debt is fully paid (POSITIVE END)

    # Action Required
    QUERIED = "queried"  # Customer has queried the debt
    DISPUTED = "disputed"  # Customer has disputed the debt
    DEFAULTED = "defaulted"  # Customer has defaulted on the debt
    FOLLOW_UP_REQUIRED = "follow_up_required"  # Follow up is required
    ADJUSTED = "adjusted"  # Client has adjusted the debt

    # Customer Operations
    ASSESSING = "assessing"  # Debt is being assessed by Customer Operations
    RECOVERING = "recovering"  # Customer has been given options to recover paying
    PROCESS_EXHAUSTED = "process_exhausted"  # Debt is closed due to process exhaustion

    # Legal flow
    LEGAL_PROTECTION = (
        "legal_protection"  # Debt is under legal protection (e.g., DRO, bankruptcy, sequestration)
    )

    # Legacy
    CLOSED = "closed"  # Debt is closed as paid in full
    OPEN = "open"  # DO NOT USE Legacy support


class StatusObject(BaseOphelosModel):
    """Status object with metadata."""

    value: DebtStatus
    whodunnit: Optional[str] = None
    context: Optional[str] = None
    reason: Optional[str] = None
    updated_at: datetime


class SummaryBreakdown(BaseOphelosModel):
    """Summary breakdown object."""

    principal: Optional[int] = None
    interest: Optional[int] = None
    fees: Optional[int] = None
    discounts: Optional[int] = None
    charges: Optional[int] = None
    value_added_tax: Optional[int] = None
    miscellaneous: Optional[int] = None
    refunds: Optional[int] = None


class DebtSummary(BaseOphelosModel):
    """Debt summary object."""

    amount_total: Optional[int] = None
    amount_paid: Optional[int] = None
    amount_remaining: Optional[int] = None
    breakdown: Optional[SummaryBreakdown] = None
    history: Optional[List[Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DISPUTED = "disputed"
    REFUNDED = "refunded"
    SCHEDULED = "scheduled"
    CANCELED = "canceled"


class ContactDetailType(str, Enum):
    """Contact detail type enumeration."""

    EMAIL = "email"
    PHONE = "phone"
    MOBILE = "mobile"
    ADDRESS = "address"


class Currency(str, Enum):
    """Currency enumeration."""

    GBP = "GBP"
    EUR = "EUR"
    USD = "USD"


class ContactDetail(BaseOphelosModel):
    """Contact detail model."""

    id: str
    object: str = "contact_detail"
    type: ContactDetailType
    value: str
    primary: Optional[bool] = None
    usage: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class PaymentOptionsConfiguration(BaseOphelosModel):
    """Payment options configuration model."""

    pay_later_permitted: Optional[bool] = None
    payment_plans_permitted: Optional[bool] = None


class Customer(BaseOphelosModel):
    """Customer model."""

    id: str
    object: str = "customer"
    kind: Optional[str] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_locale: Optional[str] = None
    date_of_birth: Optional[date] = None
    contact_details: Optional[List[Union[str, ContactDetail]]] = None  # Can be IDs or objects
    debts: Optional[List[Union[str, "Debt"]]] = None  # Can be IDs or objects
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class Organisation(BaseOphelosModel):
    """Organisation model."""

    id: str
    object: str = "organisation"
    name: str  # From item.internal_name in jbuilder
    internal_name: Optional[str] = (
        None  # From item.internal_name in jbuilder (optional for backward compatibility)
    )
    customer_facing_name: Optional[str] = None  # From item.customer_facing_name in jbuilder
    contact_details: Optional[List[Union[str, ContactDetail]]] = (
        None  # Can be contact detail IDs or expanded objects
    )
    configurations: Dict[str, Any] = {}  # Empty object from jbuilder
    deleted_at: Optional[datetime] = None  # Always null in jbuilder
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    payment_options_configuration: Optional[PaymentOptionsConfiguration] = (
        None  # Can be object or null
    )


class LineItem(BaseOphelosModel):
    """Line item model."""

    id: str
    object: str = "line_item"
    debt_id: str  # From item.debt.prefix_id in jbuilder
    invoice_id: Optional[str] = None  # From item.invoice&.prefix_id in jbuilder
    kind: str  # From item.kind in jbuilder
    description: Optional[str] = None  # From item.description in jbuilder
    amount: int  # Amount in cents (from item.amount_in_cents in jbuilder)
    currency: Optional[Currency] = None  # From item.amount_currency in jbuilder
    transaction_at: Optional[datetime] = None  # From item.transaction_at&.iso8601(3) in jbuilder
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class Invoice(BaseOphelosModel):
    """Invoice model."""

    id: str
    object: str = "invoice"
    debt: Union[str, "Debt"]  # Can be debt ID or expanded debt object
    currency: Optional[Currency] = None
    reference: Optional[str] = None
    status: Optional[str] = None
    invoiced_on: Optional[date] = None
    due_on: Optional[date] = None
    description: Optional[str] = None
    line_items: Optional[List[Union[str, LineItem]]] = (
        None  # Can be line_item IDs or expanded objects
    )
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class Payment(BaseOphelosModel):
    """Payment model."""

    id: str
    object: str = "payment"
    debt: Union[str, "Debt"]  # Can be debt ID or expanded debt object
    status: PaymentStatus
    transaction_at: datetime
    transaction_ref: Optional[str] = None
    amount: int  # Amount in cents (amount_in_cents from jbuilder)
    currency: Optional[Currency] = None  # amount_currency from jbuilder
    payment_provider: Optional[str] = None  # underscore.downcase from jbuilder
    payment_plan: Optional[Union[str, "PaymentPlan"]] = (
        None  # Can be payment_plan ID or expanded object
    )
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class PaymentPlan(BaseOphelosModel):
    """Payment plan model."""

    id: str
    object: str = "payment_plan"
    debt: Union[str, "Debt"]  # Can be debt ID or expanded debt object (from jbuilder)
    status: str  # From item.status in jbuilder
    schedule: Optional[List[Union[str, Any]]] = (
        None  # Can be schedule IDs or expanded objects (from jbuilder)
    )
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class Debt(BaseOphelosModel):
    """Debt model."""

    id: str
    object: str = "debt"
    status: StatusObject
    kind: Optional[str] = None
    reference_code: Optional[str] = None
    account_number: Optional[str] = None
    customer: Union[str, Customer]  # Can be customer ID or expanded customer object
    organisation: Union[str, Organisation]  # Can be organisation ID or expanded organisation object
    originator: Optional[Union[str, Any]] = None  # Can be originator ID, expanded object, or None
    currency: Optional[Currency] = None
    summary: DebtSummary
    invoices: Optional[List[Union[str, Invoice]]] = (
        None  # Can be invoice IDs or expanded invoice objects
    )
    line_items: Optional[List[Union[str, LineItem]]] = (
        None  # Can be line_item IDs or expanded objects
    )
    payments: Optional[List[Union[str, Payment]]] = (
        None  # Can be payment IDs or expanded payment objects
    )
    payment_plans: Optional[List[Union[str, PaymentPlan]]] = (
        None  # Can be payment_plan IDs or expanded objects
    )
    tags: Optional[List[str]] = None  # Array of tag names
    configurations: Dict[str, Any] = {}  # Empty object
    calculated_configurations: Dict[str, Any] = {}  # Empty object
    start_at: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class CommunicationTemplate(BaseOphelosModel):
    """Communication template model."""

    id: str
    object: str = "communication_template"
    name: str


class Communication(BaseOphelosModel):
    """Communication model."""

    id: str
    object: str = "communication"
    debt: Union[str, "Debt"]  # Can be debt ID or expanded debt object
    template: Optional[Union[str, CommunicationTemplate]] = (
        None  # Can be template ID, expanded object, or null
    )
    status: str
    provider: Optional[str] = None  # From item.provider.underscore.downcase
    provider_reference: Optional[str] = None
    direction: str = "outbound"  # Hardcoded as "outbound" in jbuilder
    delivery_method: Optional[str] = None  # From item.delivery_method if it responds to it
    contact_detail: Optional[Union[str, ContactDetail]] = (
        None  # Can be contact_detail ID, expanded object, or null
    )
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class Webhook(BaseOphelosModel):
    """Webhook model."""

    id: str
    object: str = "webhook"
    url: str  # From item.endpoint in jbuilder
    enabled: bool  # From item.enabled in jbuilder
    signing_key: Optional[str] = None  # From item.signing_key in jbuilder
    enabled_events: List[str]  # From item.enabled_events in jbuilder
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class WebhookEvent(BaseOphelosModel):
    """Webhook event model."""

    id: str
    object: str = "event"
    type: str
    data: Dict[str, Any]
    created_at: datetime
    livemode: bool = False


class PaginatedResponse(BaseOphelosModel):
    """Paginated response model."""

    object: str = "list"
    data: List[Union[Dict[str, Any], BaseOphelosModel]]
    has_more: bool = False
    total_count: Optional[int] = None


class Tenant(BaseOphelosModel):
    """Tenant model."""

    id: str
    object: str = "tenant"
    name: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class Payout(BaseOphelosModel):
    """Payout model."""

    id: str
    object: str = "payout"
    amount: int  # Amount in cents
    currency: Optional[Currency] = None
    status: str
    payout_date: Optional[date] = None
    organisation_id: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

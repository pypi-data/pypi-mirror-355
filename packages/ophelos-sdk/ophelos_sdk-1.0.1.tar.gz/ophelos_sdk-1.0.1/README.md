# Ophelos Python SDK

Official Python SDK for the Ophelos API - a comprehensive debt management and customer communication platform.

## Installation

### From PyPI (when published)

```bash
pip install ophelos-sdk
```

### From Local Distribution

```bash
# Install from wheel (recommended)
pip install dist/ophelos_sdk-1.0.1-py3-none-any.whl

# Or install from source distribution  
pip install dist/ophelos-sdk-1.0.1.tar.gz

# Or install in development mode
pip install -e .
```

## Quick Start

```python
from ophelos_sdk import OphelosClient

# Initialize client with your credentials
client = OphelosClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    audience="your_audience",
    environment="staging"  # or "production"
)

# Create a customer
customer = client.customers.create({
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com"
})

# Create a debt
debt = client.debts.create({
    "customer_id": customer.id,
    "organisation_id": "org_123",
    "total_amount": 10000,  # Amount in cents
    "currency": "GBP",
    "reference_code": "DEBT-001"
})

# Prepare the debt for processing
client.debts.ready(debt.id)
```

📋 **For comprehensive usage examples and advanced features, see [USAGE.md](USAGE.md)**

## Features

- **Complete API Coverage**: All Ophelos API endpoints supported
- **Type Safety**: Full type hints and Pydantic models
- **Authentication**: Automatic OAuth2 token management
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Pagination**: Built-in pagination support
- **Search**: Advanced search functionality
- **Webhooks**: Webhook event handling and validation

## API Resources

### Debt Management
- Create, update, and manage debts
- Debt lifecycle operations (ready, pause, resume, withdraw)
- Payment processing and tracking

### Customer Management
- Customer CRUD operations
- Search and filtering
- Contact detail management

### Payment Management
- Payment creation and tracking
- Payment plan management
- External payment recording

### Organisation Management
- Organisation setup and configuration
- Contact detail management

### Invoice Management
- Invoice creation and management
- Line item handling

### Communication Management
- Communication tracking
- Outbound communication management

## Authentication

The Ophelos API uses OAuth2 Client Credentials flow. You'll need:

1. **Client ID**: Your application's client identifier
2. **Client Secret**: Your application's client secret
3. **Audience**: Your API identifier

Contact Ophelos support to obtain these credentials.

```python
# Environment configuration
client = OphelosClient(
    client_id="your_client_id",
    client_secret="your_client_secret", 
    audience="your_audience",
    environment="production"  # "development", "staging", or "production"
)

# For local development (uses http://api.localhost:3000)
client = OphelosClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    audience="your_audience", 
    environment="development"
)
```

## Examples

### Working with Debts

```python
# List debts with pagination
debts = client.debts.list(limit=10)

# Search debts
results = client.debts.search("status:paying AND updated_at>=2024-01-01")

# Get debt details with expansions
debt = client.debts.get("debt_123", expand=["customer", "payments"])

# Update debt
updated_debt = client.debts.update("debt_123", {
    "metadata": {"case_id": "12345"}
})
```

### Working with Customers

```python
# Search customers by email
customers = client.customers.search("email:john@example.com")

# Update customer
customer = client.customers.update("cust_123", {
    "preferred_locale": "en-GB",
    "metadata": {"updated_reason": "customer request"}
})
```

### Working with Payments

```python
# Create external payment
payment = client.payments.create("debt_123", {
    "amount": 5000,
    "transaction_at": "2024-01-15T10:00:00Z",
    "payment_provider": "bank_transfer"
})

# List payments for a debt
payments = client.debts.payments.list("debt_123")
```

### Error Handling

```python
from ophelos_sdk.exceptions import OphelosAPIError, AuthenticationError

try:
    debt = client.debts.get("invalid_debt_id")
except OphelosAPIError as e:
    print(f"API Error: {e.message} (Status: {e.status_code})")
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
```

### Webhook Handling

```python
from ophelos_sdk.webhooks import WebhookHandler

# Initialize webhook handler
webhook_handler = WebhookHandler("your_webhook_secret")

# Validate and parse webhook
try:
    event = webhook_handler.verify_and_parse(
        payload=request.body,
        signature=request.headers.get("Ophelos-Signature")
    )
    
    if event.type == "debt.created":
        print(f"New debt created: {event.data.id}")
        
except Exception as e:
    print(f"Webhook validation failed: {e}")
```

## API Reference

### Client Configuration

```python
OphelosClient(
    client_id: str,
    client_secret: str, 
    audience: str,
    environment: str = "staging",  # "development", "staging", or "production"
    timeout: int = 30,
    max_retries: int = 3
)
```

### Resource Managers

- `client.debts` - Debt management operations
- `client.customers` - Customer management operations  
- `client.organisations` - Organisation management operations
- `client.payments` - Payment management operations
- `client.invoices` - Invoice management operations
- `client.webhooks` - Webhook management operations

## Development

```bash
# Clone the repository
git clone https://github.com/ophelos/ophelos-python-sdk.git
cd ophelos-python-sdk

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 ophelos_sdk/
mypy ophelos_sdk/
```

## Support

- **API Reference**: [https://api.ophelos.com](https://api.ophelos.com)
- **Support Email**: support@ophelos.com
- **Issues**: [GitHub Issues](https://github.com/tomasz-oph/ophelos_python_sdk/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
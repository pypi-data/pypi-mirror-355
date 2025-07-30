# Loglito Python Client

[![PyPI version](https://badge.fury.io/py/loglito.svg)](https://badge.fury.io/py/loglito)
[![Python Support](https://img.shields.io/pypi/pyversions/loglito.svg)](https://pypi.org/project/loglito/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The official Python client library for [Loglito](https://loglito.io), a powerful logging and observability platform.

## Installation

Install the Loglito Python client using pip:

```bash
pip install loglito
```

## Quick Start

```python
from loglito import Loglito

# Initialize the client with your API key
loglito = Loglito(api_key="your-api-key-here")

# Simple logging
loglito.log("Hello world!")

# Level, message, and data dictionary
loglito.log("info", "User subscribed", {"user_id": 123, "plan": "premium"})

# NEW: Convenient shortcut methods for different log levels
loglito.info("User logged in", {"user_id": 2132})
loglito.debug("API response", {"status": 200, "endpoint": "/users"})
loglito.warning("Rate limit approaching", {"current_usage": 85, "limit": 100})
loglito.error("Database connection failed", {"error": "timeout", "retries": 3})

# Traditional structured logging with data (still supported)
loglito.log(message="User logged in", data={
    "username": "john",
    "ip_address": "192.168.1.1"
})

# Log with specific level using new format
loglito.log("warning", "Low disk space", {
    "disk_usage": "85%",
    "server": "web-01"
})
```

## Shortcut Methods

For convenience, the client provides shortcut methods for common log levels:

```python
from loglito import Loglito

loglito = Loglito(api_key="your-api-key")

# Info level logging
loglito.info("User logged in", {"user_id": 2132})

# Debug level logging  
loglito.debug("SQL query executed", {
    "query": "SELECT * FROM users WHERE id = ?",
    "params": [123],
    "execution_time": 0.045
})

# Warning level logging
loglito.warning("Rate limit approaching", {
    "current_usage": 85,
    "limit": 100,
    "user_id": 456
})

# Error level logging
loglito.error("Payment processing failed", {
    "error": "card_declined",
    "order_id": "ORD-789",
    "amount": 99.99
})

# You can also pass additional keyword arguments
loglito.info("File uploaded", {"file_size": 1024}, file_type="image/jpeg", user_id=123)
```

These shortcut methods are equivalent to calling `loglito.log(level, message, data)` but provide a more convenient and readable interface.

## Configuration

### Basic Configuration

```python
from loglito import Loglito

loglito = Loglito(
    api_key="your-api-key",
    base_url="https://api.loglito.io",  # Custom API endpoint
    timeout=30.0,                        # Request timeout in seconds
    retries=3,                           # Number of retry attempts
    verify_ssl=True                      # SSL certificate verification
)
```

### Performance Configuration (Buffering)

The client uses intelligent buffering for optimal performance:

```python
loglito = Loglito(
    api_key="your-api-key",
    buffer_size=100,        # Flush after 100 logs
    flush_interval=2.0,     # Flush every 2 seconds
    immediate_mode=False    # Use buffering (default)
)

# For real-time logging (no buffering)
loglito_immediate = Loglito(
    api_key="your-api-key",
    immediate_mode=True
)
```

### Environment Variables

You can also configure the client using environment variables:

```bash
export LOGLITO_API_KEY="your-api-key"
export LOGLITO_BASE_URL="https://api.loglito.io"
```

```python
import os
from loglito import Loglito

loglito = Loglito(
    api_key=os.getenv("LOGLITO_API_KEY"),
    base_url=os.getenv("LOGLITO_BASE_URL", "https://loglito.io")
)
```

## Usage Examples

### Multiple Calling Patterns

The `log()` method supports several flexible calling patterns:

```python
from loglito import Loglito

loglito = Loglito(api_key="your-api-key")

# 1. Simple string message
loglito.log("Application started")

# 2. Level, message, and data dictionary (RECOMMENDED)
loglito.log("info", "User subscribed", {"user_id": 123, "plan": "premium"})

# 3. Level, message, and multiple data dictionaries
loglito.log("info", "User action", 
           {"user_id": 123}, 
           {"action": "file_upload"}, 
           {"file_size": 1024})

# 4. Traditional keyword arguments (still supported)
loglito.log(level="info", message="User authentication successful")

# 5. Mixed approach with additional keyword arguments
loglito.log("error", "Payment failed", 
           {"order_id": "12345", "amount": 99.99},
           retry_count=3,
           processor="stripe")

# 6. Just data without message
loglito.log("debug", "", {
    "function": "calculate_total",
    "execution_time": 0.045,
    "result": 1250.50
})
```

### API Payload Format

All logs are sent to the API in a consistent batch format:

```json
{
  "logs": [
    {
      "log": {
        "__date": "2024-01-15T10:30:00.123Z",
        "__message": "User subscribed",
        "__level": "info",
        "user_id": 123,
        "plan": "premium"
      }
    }
  ]
}
```

### Structured Logging

```python
# E-commerce example using new format
loglito.log(
    "info",
    "Order placed",
    {
        "order_id": "ORD-12345",
        "customer_id": "CUST-789",
        "total_amount": 99.99,
        "items": [
            {"product": "Widget A", "quantity": 2, "price": 29.99},
            {"product": "Widget B", "quantity": 1, "price": 39.99}
        ],
        "payment_method": "credit_card",
        "shipping_address": {
            "city": "New York",
            "state": "NY",
            "zip": "10001"
        }
    }
)

# Error logging with context
loglito.log(
    "error",
    "Database connection failed",
    {
        "error_type": "ConnectionTimeout",
        "database": "postgres", 
        "host": "db.example.com",
        "retry_count": 3, 
        "port": 5432
    }
)

# Debug logging for performance monitoring
loglito.log(
    "debug",
    "API response time",
    {
        "endpoint": "/api/users",
        "method": "GET",
        "response_time": 0.245,
        "status_code": 200,
        "user_id": 123
    }
)
```

### Batch Logging

For high-volume applications, use batch logging to send multiple logs in a single request:

```python
logs = [
    {
        "message": "User login",
        "level": "info",
        "data": {"user_id": 123, "ip": "192.168.1.1"}
    },
    {
        "message": "Page view",
        "level": "debug",
        "data": {"page": "/dashboard", "user_id": 123}
    },
    {
        "message": "API call",
        "level": "info",
        "data": {"endpoint": "/api/users", "method": "GET", "status": 200}
    }
]

loglito.log_batch(logs)
```

### Using Keyword Arguments

You can also pass additional fields directly as keyword arguments:

```python
# Using new format with keyword arguments
loglito.log(
    "info",
    "User action",
    {"user_id": 123, "action": "file_upload"},
    file_size=1024000,
    file_type="image/jpeg",
    success=True
)

# Traditional keyword approach (still supported)
loglito.log(
    message="User action",
    level="info",
    data={"user_id": 123},
    action="file_upload",
    file_size=1024000
)
```

### Context Manager

Use the client as a context manager to ensure proper cleanup:

```python
with Loglito(api_key="your-api-key") as loglito:
    loglito.log("info", "Application starting", {"version": "1.0.0"})
    # ... your application code ...
    loglito.log("info", "Application shutting down", {"uptime": 3600})
# Session is automatically closed
```

## API Reference

### Loglito Class

#### Constructor

```python
Loglito(
    api_key: str,
    base_url: str = "https://loglito.io",
    timeout: float = 30.0,
    retries: int = 3,
    verify_ssl: bool = True
)
```

**Parameters:**
- `api_key` (str): Your Loglito API key (required)
- `base_url` (str): Base URL for the Loglito API
- `timeout` (float): Request timeout in seconds
- `retries` (int): Number of retry attempts for failed requests
- `verify_ssl` (bool): Whether to verify SSL certificates

#### Methods

##### `log(*args, **kwargs)`

Send a single log entry to Loglito.

**Calling Patterns:**
- `log("message")` - Simple message
- `log("level", "message", data_dict)` - Level, message, and data (recommended)
- `log("level", "message", dict1, dict2, ...)` - Multiple data dictionaries
- `log(level="info", message="text", data={...})` - Keyword arguments (legacy)

**Parameters:**
- `*args`: Positional arguments - level, message, and data dictionaries
- `**kwargs`: Keyword arguments including:
  - `level` (str, optional): Log level (e.g., "info", "warning", "error", "debug")
  - `message` (str, optional): Log message
  - `data` (dict, optional): Additional structured data
  - Additional key-value pairs to include in the log

**Returns:** `bool` - True if successful, False otherwise

##### `log_batch(logs)`

Send multiple log entries in a single request.

**Parameters:**
- `logs` (list): List of log dictionaries

**Returns:** `bool` - True if successful, False otherwise

##### `test_connection()`

Test the connection to Loglito by sending a test log.

**Returns:** `bool` - True if connection is successful, False otherwise

##### `close()`

Close the underlying HTTP session.

##### `info(message, data=None, **kwargs)`

Send an info level log entry.

**Parameters:**
- `message` (str): Log message
- `data` (dict, optional): Additional structured data
- `**kwargs`: Additional key-value pairs to include in the log

**Returns:** `bool` - True if successful, False otherwise

##### `debug(message, data=None, **kwargs)`

Send a debug level log entry.

**Parameters:**
- `message` (str): Log message
- `data` (dict, optional): Additional structured data
- `**kwargs`: Additional key-value pairs to include in the log

**Returns:** `bool` - True if successful, False otherwise

##### `warning(message, data=None, **kwargs)`

Send a warning level log entry.

**Parameters:**
- `message` (str): Log message
- `data` (dict, optional): Additional structured data
- `**kwargs`: Additional key-value pairs to include in the log

**Returns:** `bool` - True if successful, False otherwise

##### `error(message, data=None, **kwargs)`

Send an error level log entry.

**Parameters:**
- `message` (str): Log message
- `data` (dict, optional): Additional structured data
- `**kwargs`: Additional key-value pairs to include in the log

**Returns:** `bool` - True if successful, False otherwise

##### `log_batch(logs)`

## Error Handling

The client provides specific exception types for different error scenarios:

```python
from loglito import Loglito, LoglitoError, LoglitoAuthenticationError, LoglitoConnectionError

try:
    loglito = Loglito(api_key="invalid-key")
    loglito.log("info", "Test message", {"test": True})
except LoglitoAuthenticationError:
    print("Invalid API key")
except LoglitoConnectionError:
    print("Connection failed")
except LoglitoError:
    print("General Loglito error")
```

## Integration Examples

### Flask Application

```python
from flask import Flask
from loglito import Loglito

app = Flask(__name__)
loglito = Loglito(api_key="your-api-key")

@app.route('/user/<int:user_id>')
def get_user(user_id):
    loglito.log(
        "info",
        "User profile accessed",
        {
            "user_id": user_id,
            "endpoint": "/user",
            "method": "GET"
        }
    )
    # ... your application logic ...
```

### Django Application

```python
# settings.py
LOGLITO_API_KEY = "your-api-key"

# views.py
from django.conf import settings
from loglito import Loglito

loglito = Loglito(api_key=settings.LOGLITO_API_KEY)

def user_login(request):
    # ... authentication logic ...
    
    loglito.log(
        "info",
        "User logged in",
        {
            "user_id": user.id,
            "username": user.username,
            "ip_address": request.META.get('REMOTE_ADDR')
        }
    )
```

### FastAPI Application

```python
from fastapi import FastAPI
from loglito import Loglito

app = FastAPI()
loglito = Loglito(api_key="your-api-key")

@app.post("/api/orders")
async def create_order(order_data: dict):
    loglito.log(
        "info",
        "Order created",
        {
            "order_id": order_data.get("id"),
            "customer_id": order_data.get("customer_id"),
            "total": order_data.get("total")
        }
    )
    # ... your application logic ...
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/loglito/loglito-python.git
cd loglito-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black loglito/
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://loglito.io/docs)   
- 💬 [Community Discord](https://discord.gg/loglito)
- 🐛 [Issue Tracker](https://github.com/loglito/loglito-python/issues)
- 📧 [Email Support](mailto:support@loglito.io)

## Changelog

### v0.1.0
- Initial release
- Basic logging functionality
- Batch logging support
- Error handling and retries
- Context manager support

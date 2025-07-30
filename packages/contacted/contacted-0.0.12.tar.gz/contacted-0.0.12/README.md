# Contacted Python API Library

Official Python SDK for the Contacted API.

[![PyPI version](https://badge.fury.io/py/contacted.svg)](https://badge.fury.io/py/contacted)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Support](https://img.shields.io/pypi/pyversions/contacted.svg)](https://pypi.org/project/contacted/)

## Getting Started

### 1. Get Your API Key

First, sign up and get your API key at [https://contacted.io](https://contacted.io)

### 2. Installation

```bash
pip install contacted
```

## Quick Start

```python
from contacted import ContactedAI

contacted = ContactedAI(api_key='your-api-key-here')

# Send a message
result = contacted.send(
    subject='Thank you for signing up with Example',
    from_email='sender@example.com',
    to_email='receiver@example.com',
    prompt='Generate a personalized welcome email',
    data={
        'name': 'John Doe',
        'link': 'https://example.com'
    }
)

print('Message sent:', result)

```

## Type Hints Support

The SDK includes comprehensive type hints for better IDE support:

```python
from contacted import ContactedAI
from typing import Dict, Any, Optional

contacted = ContactedAI(api_key='your-api-key-here')

# All parameters are strongly typed
result = contacted.send(
    subject="Email subject line",
    from_email="sender@example.com",
    to_email="receiver@example.com", 
    prompt="Generate email content",
    data={'name': 'John'},
    sending_profile="profile-id"  # Optional
)
```

## API Reference

### `ContactedAI(api_key, base_url=None, timeout=30)`

Creates a new ContactedAI client instance.

**Parameters:**
- `api_key` (str, required): Your ContactedAI API key
- `base_url` (str, optional): Custom API base URL
- `timeout` (int, optional): Request timeout in seconds (default: 30)

### `contacted.send(subject, from_email, to_email, prompt, data=None, sending_profile=None)`

Send a message through the ContactedAI API.

**Parameters:**
- `subject` (str, required): Email subject (2-256 characters)
- `from_email` (str, required): Valid sender email address
- `to_email` (str, required): Valid receiver email address
- `prompt` (str, required): AI prompt (10-2000 characters)
- `data` (dict, optional): Additional data for personalization
- `sending_profile` (str, optional): Sending profile ID

**Validation Rules:**
- Subject must be 2-256 characters
- Email addresses must be valid format
- Prompt must be 10-2000 characters
- Data keys cannot contain spaces
- Data keys must be non-empty strings

**Returns:** `dict` - API response

**Raises:** `ValueError` - If validation fails or API error occurs

### `contacted.get_message_status(message_id)`

Get the status of a sent message.

**Parameters:**
- `message_id` (str, required): The unique message ID returned from `send()`

**Returns:** `dict` - Message status information containing:
- `id` (str): Message ID
- `status` (str): Current status (`queued`, `sent`, `failed`)
- `message` (str): Human-readable status message
- `created_at` (str): Message creation timestamp
- `updated_at` (str): Last status update timestamp
- `sent_at` (str, optional): Delivery timestamp (when status is 'sent')
- `error_reason` (str, optional): Error description (when status is 'failed')

**Raises:** `ValueError` - If message_id is invalid or API error occurs

### `contacted.status()`

Check the API status and health.

**Returns:** `dict` - Status information

## Error Handling

The SDK provides detailed error messages for validation and API errors:

```python
try:
    contacted.send(
        subject='test error',
        from_email='invalid-email',
        to_email='user@example.com',
        prompt='short'
    )
except ValueError as e:
    print(f'Error: {e}')
    # "Invalid 'from' email address format"
```

## Examples

### Basic Usage
```python
from contacted import ContactedAI
import os

contacted = ContactedAI(api_key=os.getenv('CONTACTED_API_KEY'))

result = contacted.send(
    subject='A warm welcome from my service',
    from_email='noreply@myapp.com',
    to_email='user@example.com', 
    prompt='Create a welcome email for a new premium user',
    data={
        'username': 'john_doe',
        'plan': 'premium',
        'dashboard_url': 'https://app.myservice.com'
    }
)
```

### Send and Track Message Status
```python
from contacted import ContactedAI
import time

contacted = ContactedAI(api_key='your-api-key-here')

# Send message
result = contacted.send(
    subject='Your order confirmation',
    from_email='orders@mystore.com',
    to_email='customer@example.com',
    prompt='Generate an order confirmation email',
    data={
        'order_id': '12345',
        'total': '$99.99',
        'delivery_date': '2024-01-20'
    }
)

message_id = result['id']
print(f'✅ Message queued with ID: {message_id}')

# Check status
status = contacted.get_message_status(message_id)
print(f'📧 Status: {status["status"]} - {status["message"]}')

# Poll for completion (optional)
while status['status'] == 'queued':
    time.sleep(2)
    status = contacted.get_message_status(message_id)
    print(f'📧 Status: {status["status"]}')

if status['status'] == 'sent':
    print(f'✅ Message delivered at {status["sent_at"]}')
elif status['status'] == 'failed':
    print(f'❌ Message failed: {status["error_reason"]}')
```

### With Error Handling
```python
try:
    result = contacted.send(
        subject='Order confirmation',
        from_email='orders@mystore.com',
        to_email='customer@example.com',
        prompt='Generate order confirmation with tracking info',
        data={'order_id': '12345'}
    )
    print(f'✅ Email sent successfully: {result["id"]}')
    
    # Check status
    status = contacted.get_message_status(result['id'])
    print(f'📧 Current status: {status["status"]}')
    
except ValueError as e:
    if 'Invalid' in str(e):
        print(f'❌ Validation error: {e}')
    elif 'not found' in str(e):
        print(f'❌ Message not found: {e}')
    else:
        print(f'❌ API error: {e}')
```

### Environment Variables
```python
import os
from contacted import ContactedAI

# Use environment variable for API key
contacted = ContactedAI(
    api_key=os.getenv('CONTACTED_API_KEY'),
    timeout=60  # Custom timeout
)

result = contacted.send(
    subject='Weekly newsletter',
    from_email='newsletter@mycompany.com',
    to_email='subscriber@example.com',
    prompt='Create an engaging weekly newsletter',
    data={'subscriber_name': 'Alex'}
)
```

## License

MIT

## Support

- 📧 Email: support@contacted.io
- 🐛 Issues: [GitHub Issues](https://github.com/LawrenceGB/contacted-python/issues)
- 📖 Documentation: [contacted.gitbook.io](https://contacted.gitbook.io)
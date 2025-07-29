# Litewave Audit Library

Internal audit logging library for Litewave services.

## Usage

```python
from litewave_audit_lib import get_logger

# Get a logger with NATS backend
logger = get_logger(
    backend="nats",
    servers=["nats://your-nats-server:4222"],
    subject="audit.logs",
    username="your_username",
    password="your_password",
    max_retries=3,        # Optional: Maximum number of reconnection attempts
    retry_delay=1.0       # Optional: Delay between reconnection attempts in seconds
)

# Log an audit event
logger.log(
    who="user123",
    resource="document",
    action="view",
    location="office",
    request_context={"ip": "127.0.0.1"},
    context={"document_id": "doc123"},
    client="web"
)
```

## Features

- Automatic reconnection handling
- Connection retry logic
- Proper error handling and logging
- Type hints for better IDE support
- Automatic cleanup of NATS connections

## Dependencies

- nats-py (for NATS backend)

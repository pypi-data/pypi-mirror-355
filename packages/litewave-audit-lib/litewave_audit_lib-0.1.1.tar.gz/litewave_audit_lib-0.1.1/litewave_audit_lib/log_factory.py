from typing import Dict, Any
from .nats_logger import NATSAuditLogger


def get_logger(**kwargs: Dict[str, Any]) -> NATSAuditLogger:
    """
    Returns an audit logger for the specified backend.

    Raises:
        ValueError: if unsupported backend or missing parameters.
    """
    required = {"nats_connection_url"}
    missing = required - set(kwargs)
    if missing:
        raise ValueError(f"Missing args for NATS logger: {missing}")

    return NATSAuditLogger(subject='audit.logs', **kwargs)
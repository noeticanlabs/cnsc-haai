"""API module for NPE HTTP/Unix socket server."""

from .server import NPEServer, create_server
from .routes import setup_routes
from .wire import (
    parse_request,
    serialize_response,
    validate_schema,
    WIRE_SPECS,
)

__all__ = [
    "NPEServer",
    "create_server",
    "setup_routes",
    "parse_request",
    "serialize_response",
    "validate_schema",
    "WIRE_SPECS",
]

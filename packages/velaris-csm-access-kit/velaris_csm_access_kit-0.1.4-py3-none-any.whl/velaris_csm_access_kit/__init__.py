"""
Velaris CSM Access Kit

A Python library providing authentication, caching, database connection pooling,
service registry, and secrets management functionality for Velaris CSM applications.
"""

from .cache import TTLCache
from .secrets import get_secret
from .service_registry import ServiceRegistry
from .db import AsyncMultiDbConnectionPool
from .token import (
    validate_token,
    TokenService,
    AuthenticatedService,
    UserManagmentService,
    TOKEN_SERVICE_PARAMETER
)

try:
    from ._version import __version__
except ImportError:
    # Fallback for development
    __version__ = "0.0.0+unknown"

__author__ = "Velaris"
__email__ = "support@velaris.com"

__all__ = [
    "TTLCache",
    "get_secret",
    "ServiceRegistry",
    "AsyncMultiDbConnectionPool",
    "validate_token",
    "TokenService",
    "AuthenticatedService",
    "UserManagmentService",
    "TOKEN_SERVICE_PARAMETER",
]

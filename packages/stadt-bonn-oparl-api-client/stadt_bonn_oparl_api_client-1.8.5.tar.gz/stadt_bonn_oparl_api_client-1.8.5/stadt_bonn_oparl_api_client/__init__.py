"""A client library for accessing Stadt Bonn oparl API"""

from .client import AuthenticatedClient, Client

__all__ = (
    "AuthenticatedClient",
    "Client",
)

"""Registry module for NPE proposer management."""

from .loader import RegistryLoader, load_registry
from .dispatch import Dispatcher, get_dispatcher

__all__ = [
    "RegistryLoader",
    "load_registry",
    "Dispatcher",
    "get_dispatcher",
]

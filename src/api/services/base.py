"""Base service module for business logic."""

from abc import ABC


class BaseService(ABC):
    """Base service for business logic.

    All service classes should inherit from this base class.
    Services contain business logic and orchestrate repository operations.
    """
    pass

"""Base client class for Qlik Sense API clients."""

from abc import ABC, abstractmethod
from src.api.core.config import Settings


class BaseClient(ABC):
    """Abstract base class for Qlik Sense API clients."""

    def __init__(self, settings: Settings):
        """
        Initialize base client.

        Args:
            settings: Application settings containing Qlik Sense configuration
        """
        self.settings = settings

    @abstractmethod
    def connect(self):
        """
        Establish connection to Qlik Sense API.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement connect()")

    @abstractmethod
    def disconnect(self):
        """
        Close connection to Qlik Sense API.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement disconnect()")

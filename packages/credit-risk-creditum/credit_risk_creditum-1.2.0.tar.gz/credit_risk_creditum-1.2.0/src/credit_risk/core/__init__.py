"""Core functionality for credit risk assessment."""

from .application import CreditApplication
from .processor import ApplicationProcessor

__all__ = ["CreditApplication", "ApplicationProcessor"]

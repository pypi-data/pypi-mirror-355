"""
Credit Risk Assessment System
A comprehensive credit risk assessment system for individual and corporate applications.
"""

__version__ = "1.2.0"
__author__ = "Omoshola Owolabi"
__email__ = "omoshola@example.com"
__description__ = "A comprehensive credit risk assessment system"

# Import main classes for easy access
from .core.application import CreditApplication
from .models.risk_models import IndividualRiskModel, CorporateRiskModel
from .utils.economic_indicators import EconomicIndicators
from .utils.validators import validate_application
from .utils.helpers import calculate_dti_ratio

__all__ = [
    "CreditApplication",
    "IndividualRiskModel", 
    "CorporateRiskModel",
    "EconomicIndicators",
    "validate_application",
    "calculate_dti_ratio",
    "__version__",
    "__author__",
]

# Package metadata
__title__ = "credit-risk-creditum"
__license__ = "MIT"
__copyright__ = "Copyright 2025 Omoshola Owolabi"

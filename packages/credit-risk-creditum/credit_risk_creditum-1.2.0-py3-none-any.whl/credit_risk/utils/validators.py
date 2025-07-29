"""Validation functions for credit applications."""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def validate_application(data: Dict[str, Any], application_type: str) -> None:
    """
    Validate credit application data.
    
    Args:
        data: Application data dictionary
        application_type: Type of application ('individual' or 'corporate')
        
    Raises:
        ValueError: If validation fails
    """
    if application_type.lower() == 'individual':
        _validate_individual_application(data)
    elif application_type.lower() == 'corporate':
        _validate_corporate_application(data)
    else:
        raise ValueError(f"Unknown application type: {application_type}")


def _validate_individual_application(data: Dict[str, Any]) -> None:
    """Validate individual credit application."""
    required_fields = [
        'credit_score', 'monthly_income', 'monthly_debt', 'loan_amount'
    ]
    
    # Check required fields
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Validate field types and ranges
    validations = [
        ('credit_score', int, 300, 850),
        ('monthly_income', (int, float), 0, 1000000),
        ('monthly_debt', (int, float), 0, 500000),
        ('loan_amount', (int, float), 1000, 10000000),
    ]
    
    for field, field_type, min_val, max_val in validations:
        if field in data:
            value = data[field]
            
            # Type validation
            if not isinstance(value, field_type):
                try:
                    if field_type == int:
                        value = int(value)
                    elif field_type == float or field_type == (int, float):
                        value = float(value)
                    data[field] = value  # Update with converted value
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid type for {field}: expected {field_type}, got {type(value)}")
            
            # Range validation
            if not (min_val <= value <= max_val):
                raise ValueError(f"Invalid value for {field}: {value} (must be between {min_val} and {max_val})")
    
    # Business logic validations
    if data.get('monthly_income', 0) <= 0:
        raise ValueError("Monthly income must be greater than 0")
    
    if data.get('loan_amount', 0) <= 0:
        raise ValueError("Loan amount must be greater than 0")
    
    # DTI validation
    monthly_income = data.get('monthly_income', 0)
    monthly_debt = data.get('monthly_debt', 0)
    if monthly_income > 0:
        dti_ratio = monthly_debt / monthly_income
        if dti_ratio > 2.0:  # 200% DTI is clearly unrealistic
            raise ValueError(f"Unrealistic DTI ratio: {dti_ratio:.2f}")


def _validate_corporate_application(data: Dict[str, Any]) -> None:
    """Validate corporate credit application."""
    required_fields = [
        'annual_revenue', 'loan_amount', 'years_in_business'
    ]
    
    # Check required fields
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Validate field types and ranges
    validations = [
        ('annual_revenue', (int, float), 0, 100000000000),  # Up to 100B
        ('loan_amount', (int, float), 10000, 1000000000),   # 10K to 1B
        ('years_in_business', int, 0, 200),
        ('employee_count', int, 0, 1000000),
        ('assets', (int, float), 0, 1000000000000),  # Up to 1T
        ('liabilities', (int, float), 0, 1000000000000),
    ]
    
    for field, field_type, min_val, max_val in validations:
        if field in data and data[field] is not None:
            value = data[field]
            
            # Type validation
            if not isinstance(value, field_type):
                try:
                    if field_type == int:
                        value = int(value)
                    elif field_type == float or field_type == (int, float):
                        value = float(value)
                    data[field] = value  # Update with converted value
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid type for {field}: expected {field_type}, got {type(value)}")
            
            # Range validation
            if not (min_val <= value <= max_val):
                raise ValueError(f"Invalid value for {field}: {value} (must be between {min_val} and {max_val})")
    
    # Business logic validations
    if data.get('annual_revenue', 0) <= 0:
        raise ValueError("Annual revenue must be greater than 0")
    
    if data.get('loan_amount', 0) <= 0:
        raise ValueError("Loan amount must be greater than 0")
    
    # Validate industry if provided
    valid_industries = [
        'technology', 'healthcare', 'finance', 'manufacturing', 'retail',
        'hospitality', 'construction', 'energy', 'agriculture', 'real_estate', 'other'
    ]
    
    industry = data.get('industry', '').lower()
    if industry and industry not in valid_industries:
        logger.warning(f"Unknown industry: {industry}. Using 'other'.")
        data['industry'] = 'other'


def validate_numeric_field(
    value: Any, 
    field_name: str, 
    min_val: Optional[float] = None, 
    max_val: Optional[float] = None,
    allow_none: bool = False
) -> float:
    """
    Validate and convert a numeric field.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        allow_none: Whether None values are allowed
        
    Returns:
        Validated numeric value
        
    Raises:
        ValueError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        else:
            raise ValueError(f"{field_name} cannot be None")
    
    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid {field_name}: {value} (must be numeric)")
    
    if min_val is not None and numeric_value < min_val:
        raise ValueError(f"{field_name} must be at least {min_val}, got {numeric_value}")
    
    if max_val is not None and numeric_value > max_val:
        raise ValueError(f"{field_name} must be at most {max_val}, got {numeric_value}")
    
    return numeric_value


def validate_categorical_field(
    value: Any, 
    field_name: str, 
    valid_values: List[str],
    allow_none: bool = False
) -> str:
    """
    Validate a categorical field.
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        valid_values: List of valid values
        allow_none: Whether None values are allowed
        
    Returns:
        Validated categorical value
        
    Raises:
        ValueError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        else:
            raise ValueError(f"{field_name} cannot be None")
    
    str_value = str(value).lower().strip()
    
    if str_value not in [v.lower() for v in valid_values]:
        raise ValueError(f"Invalid {field_name}: {value}. Valid values: {', '.join(valid_values)}")
    
    # Return the properly cased version
    for valid_val in valid_values:
        if str_value == valid_val.lower():
            return valid_val
    
    return str_value


def sanitize_application_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize and clean application data.
    
    Args:
        data: Raw application data
        
    Returns:
        Sanitized application data
    """
    sanitized = {}
    
    for key, value in data.items():
        # Remove leading/trailing whitespace from strings
        if isinstance(value, str):
            value = value.strip()
        
        # Convert empty strings to None
        if value == "":
            value = None
        
        # Convert string representations of numbers
        if isinstance(value, str) and key in [
            'credit_score', 'monthly_income', 'monthly_debt', 'loan_amount',
            'employment_length', 'annual_revenue', 'years_in_business',
            'employee_count', 'assets', 'liabilities'
        ]:
            try:
                # Remove common formatting characters - FIXED LINE
                cleaned = value.replace(',', '').replace('$', '').replace('%', '')
                if '.' in cleaned:
                    value = float(cleaned)
                else:
                    value = int(cleaned)
            except ValueError:
                pass  # Keep original value if conversion fails
        
        sanitized[key] = value
    
    return sanitized
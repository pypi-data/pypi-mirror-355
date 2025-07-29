"""Helper utility functions."""

import logging
from typing import Any, Dict, Optional, Union
import re
from datetime import datetime

logger = logging.getLogger(__name__)


def calculate_dti_ratio(monthly_income: float, monthly_debt: float) -> float:
    """
    Calculate debt-to-income ratio.
    
    Args:
        monthly_income: Monthly gross income
        monthly_debt: Monthly debt payments
        
    Returns:
        DTI ratio (0.0 to 1.0+)
    """
    if not monthly_income or monthly_income <= 0:
        logger.warning("Invalid monthly income for DTI calculation")
        return 0.5  # Default conservative estimate
    
    return monthly_debt / monthly_income


def normalize_score(score: float, min_val: float, max_val: float) -> float:
    """
    Normalize a score to 0-1 range.
    
    Args:
        score: Score to normalize
        min_val: Minimum possible value
        max_val: Maximum possible value
        
    Returns:
        Normalized score between 0 and 1
    """
    if max_val <= min_val:
        logger.warning(f"Invalid range for normalization: min={min_val}, max={max_val}")
        return 0.5
    
    normalized = (score - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))  # Clamp to 0-1


def format_currency(amount: Union[int, float], currency: str = "USD") -> str:
    """
    Format amount as currency.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    try:
        if currency.upper() == "USD":
            return f"${amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"
    except (ValueError, TypeError):
        return str(amount)


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    Format value as percentage.
    
    Args:
        value: Value to format (0.05 = 5%)
        decimal_places: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    try:
        return f"{value * 100:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return str(value)


def calculate_loan_to_income_ratio(loan_amount: float, annual_income: float) -> float:
    """
    Calculate loan-to-income ratio.
    
    Args:
        loan_amount: Requested loan amount
        annual_income: Annual gross income
        
    Returns:
        Loan-to-income ratio
    """
    if not annual_income or annual_income <= 0:
        logger.warning("Invalid annual income for LTI calculation")
        return 5.0  # Conservative high value
    
    return loan_amount / annual_income


def extract_numeric_value(text: str) -> Optional[float]:
    """
    Extract numeric value from text.
    
    Args:
        text: Text containing numeric value
        
    Returns:
        Extracted numeric value or None
    """
    if not isinstance(text, str):
        return None
    
    # Remove common currency symbols and formatting
    cleaned = re.sub(r'[$,\s%]', '', text)
    
    try:
        return float(cleaned)
    except ValueError:
        return None


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(phone, str):
        return False
    
    # Remove formatting characters
    digits_only = re.sub(r'[^0-9]', '', phone)
    
    # Check for valid length (10-15 digits)
    return 10 <= len(digits_only) <= 15


def calculate_monthly_payment(
    principal: float, 
    annual_rate: float, 
    years: int
) -> float:
    """
    Calculate monthly loan payment using standard amortization formula.
    
    Args:
        principal: Loan amount
        annual_rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
        years: Loan term in years
        
    Returns:
        Monthly payment amount
    """
    try:
        if annual_rate == 0:
            return principal / (years * 12)
        
        monthly_rate = annual_rate / 12
        num_payments = years * 12
        
        payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                 ((1 + monthly_rate) ** num_payments - 1)
        
        return payment
    
    except (ValueError, ZeroDivisionError):
        logger.error(f"Error calculating monthly payment: principal={principal}, rate={annual_rate}, years={years}")
        return 0.0


def risk_grade_from_score(risk_score: float) -> str:
    """
    Convert numeric risk score to letter grade.
    
    Args:
        risk_score: Risk score (0.0 to 1.0)
        
    Returns:
        Risk grade (A+ to F)
    """
    if risk_score < 0.1:
        return "A+"
    elif risk_score < 0.2:
        return "A"
    elif risk_score < 0.3:
        return "B+"
    elif risk_score < 0.4:
        return "B"
    elif risk_score < 0.5:
        return "C+"
    elif risk_score < 0.6:
        return "C"
    elif risk_score < 0.7:
        return "D+"
    elif risk_score < 0.8:
        return "D"
    else:
        return "F"


def calculate_affordability_ratio(
    monthly_payment: float, 
    monthly_income: float
) -> float:
    """
    Calculate payment-to-income ratio for affordability assessment.
    
    Args:
        monthly_payment: Proposed monthly payment
        monthly_income: Monthly gross income
        
    Returns:
        Payment-to-income ratio
    """
    if not monthly_income or monthly_income <= 0:
        return 1.0  # Conservative high ratio
    
    return monthly_payment / monthly_income


def get_business_days_between(start_date: datetime, end_date: datetime) -> int:
    """
    Calculate number of business days between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Number of business days
    """
    current_date = start_date
    business_days = 0
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
            business_days += 1
        current_date = current_date.replace(day=current_date.day + 1)
    
    return business_days


def generate_application_id() -> str:
    """
    Generate unique application ID.
    
    Returns:
        Unique application ID string
    """
    from datetime import datetime
    import random
    import string
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    return f"APP-{timestamp}-{random_suffix}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, handling division by zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator  
        default: Default value if division by zero
        
    Returns:
        Result of division or default value
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value between minimum and maximum.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))

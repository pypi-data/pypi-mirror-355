"""Tests for utility functions."""

import pytest
from credit_risk.utils.helpers import (
    calculate_dti_ratio, normalize_score, format_currency, format_percentage,
    calculate_loan_to_income_ratio, extract_numeric_value, validate_email,
    validate_phone, calculate_monthly_payment, risk_grade_from_score
)
from credit_risk.utils.validators import (
    validate_application, validate_numeric_field, validate_categorical_field,
    sanitize_application_data
)
from credit_risk.utils.economic_indicators import EconomicIndicators


class TestHelperFunctions:
    """Test helper utility functions."""
    
    def test_calculate_dti_ratio(self):
        """Test DTI ratio calculation."""
        assert calculate_dti_ratio(5000, 1500) == 0.3
        assert calculate_dti_ratio(4000, 2000) == 0.5
        assert calculate_dti_ratio(0, 1000) == 0.5  # Default for zero income
        assert calculate_dti_ratio(-1000, 500) == 0.5  # Default for negative income
    
    def test_normalize_score(self):
        """Test score normalization."""
        assert normalize_score(75, 0, 100) == 0.75
        assert normalize_score(50, 0, 100) == 0.5
        assert normalize_score(0, 0, 100) == 0.0
        assert normalize_score(100, 0, 100) == 1.0
        
        # Test clamping
        assert normalize_score(150, 0, 100) == 1.0
        assert normalize_score(-50, 0, 100) == 0.0
        
        # Test invalid range
        assert normalize_score(50, 100, 0) == 0.5  # Should return default
    
    def test_format_currency(self):
        """Test currency formatting."""
        assert format_currency(1234.56) == "$1,234.56"
        assert format_currency(1000) == "$1,000.00"
        assert format_currency(1234.56, "EUR") == "1,234.56 EUR"
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        assert format_percentage(0.05) == "5.00%"
        assert format_percentage(0.1234, 1) == "12.3%"
        assert format_percentage(1.0) == "100.00%"
    
    def test_calculate_loan_to_income_ratio(self):
        """Test loan-to-income ratio calculation."""
        assert calculate_loan_to_income_ratio(100000, 50000) == 2.0
        assert calculate_loan_to_income_ratio(50000, 100000) == 0.5
        assert calculate_loan_to_income_ratio(100000, 0) == 5.0  # Default for zero income
    
    def test_extract_numeric_value(self):
        """Test numeric value extraction from text."""
        assert extract_numeric_value("5%") == 5.0
        assert extract_numeric_value("invalid") is None
        assert extract_numeric_value(123) is None  # Non-string input
    
    def test_validate_email(self):
        """Test email validation."""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name+tag@domain.co.uk") is True
        assert validate_email("invalid.email") is False
        assert validate_email("@domain.com") is False
        assert validate_email("user@") is False
        assert validate_email(None) is False
    
    def test_validate_phone(self):
        """Test phone number validation."""
        assert validate_phone("(555) 123-4567") is True
        assert validate_phone("555-123-4567") is True
        assert validate_phone("15551234567") is True
        assert validate_phone("555.123.4567") is True
        assert validate_phone("123") is False  # Too short
        assert validate_phone("123456789012345678") is False  # Too long
        assert validate_phone(None) is False
    
    def test_calculate_monthly_payment(self):
        """Test monthly payment calculation."""
        # Test standard loan
        payment = calculate_monthly_payment(100000, 0.05, 30)
        assert 500 < payment < 600  # Should be around $537
        
        # Test zero interest
        payment_zero = calculate_monthly_payment(120000, 0.0, 10)
        assert payment_zero == 1000.0  # 120000 / (10 * 12)
        
        # Test error cases
        payment_error = calculate_monthly_payment(100000, -0.05, 30)
        assert payment_error == 0.0
    
    def test_risk_grade_from_score(self):
        """Test risk grade conversion."""
        assert risk_grade_from_score(0.05) == "A+"
        assert risk_grade_from_score(0.15) == "A"
        assert risk_grade_from_score(0.25) == "B+"
        assert risk_grade_from_score(0.35) == "B"
        assert risk_grade_from_score(0.45) == "C+"
        assert risk_grade_from_score(0.55) == "C"
        assert risk_grade_from_score(0.65) == "D+"
        assert risk_grade_from_score(0.75) == "D"
        assert risk_grade_from_score(0.85) == "F"


class TestValidators:
    """Test validation functions."""
    
    def test_validate_individual_application_success(self):
        """Test successful individual application validation."""
        valid_data = {
            'credit_score': 720,
            'monthly_income': 5000,
            'monthly_debt': 1500,
            'loan_amount': 20000,
            'loan_purpose': 'home_improvement',
        }
        
        # Should not raise any exception
        validate_application(valid_data, 'individual')
    
    def test_validate_individual_application_missing_fields(self):
        """Test individual application with missing required fields."""
        invalid_data = {
            'credit_score': 720,
            # Missing monthly_income, monthly_debt, loan_amount
        }
        
        with pytest.raises(ValueError, match="Missing required fields"):
            validate_application(invalid_data, 'individual')
    
    def test_validate_individual_application_invalid_values(self):
        """Test individual application with invalid values."""
        # Invalid credit score
        invalid_data = {
            'credit_score': 900,  # Above max
            'monthly_income': 5000,
            'monthly_debt': 1500,
            'loan_amount': 20000,
        }
        
        with pytest.raises(ValueError):
            validate_application(invalid_data, 'individual')
        
        # Invalid DTI
        invalid_dti_data = {
            'credit_score': 720,
            'monthly_income': 1000,
            'monthly_debt': 3000,  # 300% DTI
            'loan_amount': 20000,
        }
        
        with pytest.raises(ValueError, match="Unrealistic DTI ratio"):
            validate_application(invalid_dti_data, 'individual')
    
    def test_validate_corporate_application_success(self):
        """Test successful corporate application validation."""
        valid_data = {
            'annual_revenue': 2000000,
            'loan_amount': 500000,
            'years_in_business': 8,
            'industry': 'technology',
        }
        
        # Should not raise any exception
        validate_application(valid_data, 'corporate')
    
    def test_validate_corporate_application_missing_fields(self):
        """Test corporate application with missing required fields."""
        invalid_data = {
            'annual_revenue': 2000000,
            # Missing loan_amount, years_in_business
        }
        
        with pytest.raises(ValueError, match="Missing required fields"):
            validate_application(invalid_data, 'corporate')
    
    def test_validate_numeric_field(self):
        """Test numeric field validation."""
        # Valid cases
        assert validate_numeric_field(100, "test_field", 0, 1000) == 100.0
        assert validate_numeric_field("50.5", "test_field", 0, 100) == 50.5
        assert validate_numeric_field(None, "test_field", allow_none=True) is None
        
        # Invalid cases
        with pytest.raises(ValueError, match="cannot be None"):
            validate_numeric_field(None, "test_field", allow_none=False)
        
        with pytest.raises(ValueError, match="must be numeric"):
            validate_numeric_field("invalid", "test_field")
        
        with pytest.raises(ValueError, match="must be at least"):
            validate_numeric_field(50, "test_field", min_val=100)
        
        with pytest.raises(ValueError, match="must be at most"):
            validate_numeric_field(150, "test_field", max_val=100)
    
    def test_validate_categorical_field(self):
        """Test categorical field validation."""
        valid_values = ['option1', 'option2', 'option3']
        
        # Valid cases
        assert validate_categorical_field('option1', 'test_field', valid_values) == 'option1'
        assert validate_categorical_field('OPTION2', 'test_field', valid_values) == 'option2'
        assert validate_categorical_field(None, 'test_field', valid_values, allow_none=True) is None
        
        # Invalid cases
        with pytest.raises(ValueError, match="cannot be None"):
            validate_categorical_field(None, 'test_field', valid_values, allow_none=False)
        
        with pytest.raises(ValueError, match="Invalid test_field"):
            validate_categorical_field('invalid_option', 'test_field', valid_values)
    
    def test_sanitize_application_data(self):
        """Test data sanitization."""
        raw_data = {
            'credit_score': '720',
            'monthly_income': '$5,000.00',
            'loan_amount': '20000',
            'name': '  John Doe  ',
            'empty_field': '',
            'purpose': 'home_improvement',
        }
        
        sanitized = sanitize_application_data(raw_data)
        
        assert sanitized['credit_score'] == 720
        assert sanitized['monthly_income'] == 5000.0
        assert sanitized['loan_amount'] == 20000
        assert sanitized['name'] == 'John Doe'
        assert sanitized['empty_field'] is None
        assert sanitized['purpose'] == 'home_improvement'


class TestEconomicIndicators:
    """Test economic indicators functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.indicators = EconomicIndicators()
    
    def test_initialization(self):
        """Test economic indicators initialization."""
        current = self.indicators.get_current_indicators()
        
        assert 'indicators' in current
        assert 'risk_adjustment' in current
        assert 'weights' in current
        assert 'last_updated' in current
        
        # Check that default indicators are present
        assert 'cpi' in current['indicators']
        assert 'gdp_growth' in current['indicators']
        assert 'unemployment_rate' in current['indicators']
    
    def test_update_indicators(self):
        """Test updating economic indicators."""
        new_indicators = {
            'cpi': 0.035,
            'gdp_growth': 0.02,
            'unemployment_rate': 0.06,
        }
        
        self.indicators.update_indicators(new_indicators)
        current = self.indicators.get_current_indicators()
        
        assert current['indicators']['cpi'] == 0.035
        assert current['indicators']['gdp_growth'] == 0.02
        assert current['indicators']['unemployment_rate'] == 0.06
    
    def test_risk_adjustment_calculation(self):
        """Test risk adjustment calculation."""
        # Test favorable conditions
        favorable = {
            'cpi': 0.02,  # Low inflation
            'gdp_growth': 0.04,  # Strong growth
            'unemployment_rate': 0.03,  # Low unemployment
            'interest_rate': 0.02,  # Low rates
        }
        
        self.indicators.update_indicators(favorable)
        favorable_adjustment = self.indicators.get_risk_adjustment()
        
        # Test unfavorable conditions
        unfavorable = {
            'cpi': 0.06,  # High inflation
            'gdp_growth': -0.01,  # Recession
            'unemployment_rate': 0.09,  # High unemployment
            'interest_rate': 0.08,  # High rates
        }
        
        self.indicators.update_indicators(unfavorable)
        unfavorable_adjustment = self.indicators.get_risk_adjustment()
        
        # Unfavorable conditions should lead to higher risk adjustment
        assert unfavorable_adjustment > favorable_adjustment
        
        # Risk adjustment should be bounded
        assert -0.5 <= favorable_adjustment <= 0.5
        assert -0.5 <= unfavorable_adjustment <= 0.5
    
    def test_economic_summary(self):
        """Test economic summary generation."""
        summary = self.indicators.get_economic_summary()
        
        assert 'outlook' in summary
        assert 'risk_adjustment' in summary
        assert 'description' in summary
        assert 'key_factors' in summary
        assert 'last_updated' in summary
        
        assert summary['outlook'] in ['Favorable', 'Neutral', 'Cautious', 'Unfavorable']
    
    def test_unknown_indicator_update(self):
        """Test updating with unknown indicators."""
        unknown_indicators = {
            'unknown_indicator': 0.5,
            'cpi': 0.03,  # This should still work
        }
        
        # Should not raise exception, but should log warning
        self.indicators.update_indicators(unknown_indicators)
        
        current = self.indicators.get_current_indicators()
        assert current['indicators']['cpi'] == 0.03
        assert 'unknown_indicator' not in current['indicators']


if __name__ == '__main__':
    pytest.main([__file__])

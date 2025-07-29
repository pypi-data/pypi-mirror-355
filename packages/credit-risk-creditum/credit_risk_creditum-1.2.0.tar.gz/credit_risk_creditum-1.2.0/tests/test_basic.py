"""Basic tests to ensure the package works."""

import pytest
from credit_risk import CreditApplication, EconomicIndicators
from credit_risk.models.risk_models import IndividualRiskModel, CorporateRiskModel
from credit_risk.utils.helpers import calculate_dti_ratio, normalize_score


def test_package_imports():
    """Test that main classes can be imported."""
    assert CreditApplication is not None
    assert EconomicIndicators is not None
    assert IndividualRiskModel is not None
    assert CorporateRiskModel is not None


def test_package_version():
    """Test that package version is accessible."""
    import credit_risk
    assert hasattr(credit_risk, '__version__')
    assert isinstance(credit_risk.__version__, str)


def test_basic_individual_application():
    """Test basic individual application processing."""
    app = CreditApplication()
    
    application_data = {
        'credit_score': 720,
        'monthly_income': 5000,
        'monthly_debt': 1500,
        'loan_amount': 20000,
        'loan_purpose': 'home_improvement',
        'employment_length': 5,
    }
    
    result = app.make_decision(application_data, 'individual')
    
    assert 'decision' in result
    assert 'reason' in result
    assert 'risk_score' in result
    assert result['decision'] in ['APPROVED', 'DECLINED', 'CONDITIONAL', 'ERROR']


def test_basic_corporate_application():
    """Test basic corporate application processing."""
    app = CreditApplication()
    
    application_data = {
        'annual_revenue': 2000000,
        'loan_amount': 500000,
        'years_in_business': 8,
        'employee_count': 25,
        'industry': 'technology',
    }
    
    result = app.make_decision(application_data, 'corporate')
    
    assert 'decision' in result
    assert 'reason' in result
    assert 'risk_score' in result
    assert result['decision'] in ['APPROVED', 'DECLINED', 'CONDITIONAL', 'ERROR']


def test_economic_indicators():
    """Test economic indicators functionality."""
    indicators = EconomicIndicators()
    
    # Test default indicators
    current = indicators.get_current_indicators()
    assert 'indicators' in current
    assert 'risk_adjustment' in current
    
    # Test updating indicators
    new_data = {
        'cpi': 0.03,
        'gdp_growth': 0.025,
        'unemployment_rate': 0.06,
    }
    
    indicators.update_indicators(new_data)
    updated = indicators.get_current_indicators()
    
    assert updated['indicators']['cpi'] == 0.03
    assert updated['indicators']['gdp_growth'] == 0.025
    assert updated['indicators']['unemployment_rate'] == 0.06


def test_helper_functions():
    """Test utility helper functions."""
    # Test DTI calculation
    dti = calculate_dti_ratio(5000, 1500)
    assert dti == 0.3
    
    # Test normalization
    normalized = normalize_score(75, 0, 100)
    assert normalized == 0.75
    
    # Test edge cases
    dti_zero_income = calculate_dti_ratio(0, 1500)
    assert dti_zero_income == 0.5  # Default value
    
    normalized_out_of_range = normalize_score(150, 0, 100)
    assert normalized_out_of_range == 1.0  # Clamped to max


def test_risk_models():
    """Test risk model calculations."""
    individual_model = IndividualRiskModel()
    corporate_model = CorporateRiskModel()
    
    # Test individual model
    individual_data = {
        'credit_score': 720,
        'monthly_income': 5000,
        'monthly_debt': 1500,
        'loan_amount': 20000,
        'employment_length': 5,
        'loan_purpose': 'home_improvement'
    }
    
    individual_risk = individual_model.calculate_risk_score(individual_data)
    assert 0 <= individual_risk <= 1
    
    # Test corporate model
    corporate_data = {
        'annual_revenue': 2000000,
        'net_income': 300000,
        'assets': 1500000,
        'liabilities': 800000,
        'years_in_business': 8,
        'employee_count': 25,
        'industry': 'technology'
    }
    
    corporate_risk = corporate_model.calculate_risk_score(corporate_data)
    assert 0 <= corporate_risk <= 1


def test_error_handling():
    """Test error handling for invalid inputs."""
    app = CreditApplication()
    
    # Test invalid application type
    result = app.make_decision({}, 'invalid_type')
    assert result['decision'] == 'ERROR'
    
    # Test missing required fields
    incomplete_data = {'credit_score': 720}
    result = app.make_decision(incomplete_data, 'individual')
    assert result['decision'] == 'ERROR'


if __name__ == '__main__':
    pytest.main([__file__])

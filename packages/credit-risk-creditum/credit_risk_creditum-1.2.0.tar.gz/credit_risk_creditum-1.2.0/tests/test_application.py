"""Tests for the main CreditApplication class."""

import pytest
from credit_risk.core.application import CreditApplication
from credit_risk.utils.economic_indicators import EconomicIndicators


class TestCreditApplication:
    """Test cases for CreditApplication class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = CreditApplication(min_credit_score=600, max_dti=0.43)
    
    def test_initialization(self):
        """Test CreditApplication initialization."""
        assert self.app.min_credit_score == 600
        assert self.app.max_dti == 0.43
        assert isinstance(self.app.economic_indicators, EconomicIndicators)
    
    def test_approved_individual_application(self):
        """Test individual application that should be approved."""
        data = {
            'credit_score': 750,
            'monthly_income': 6000,
            'monthly_debt': 1800,  # 30% DTI
            'loan_amount': 25000,
            'loan_purpose': 'home_improvement',
            'employment_length': 8,
            'annual_income': 72000,
        }
        
        result = self.app.make_decision(data, 'individual')
        
        assert result['decision'] == 'APPROVED'
        assert 'risk_score' in result
        assert result['risk_score'] < 0.5  # Should be low risk
        assert 'recommended_amount' in result
        assert 'interest_rate' in result
    
    def test_declined_individual_application_low_credit(self):
        """Test individual application declined for low credit score."""
        data = {
            'credit_score': 550,  # Below minimum
            'monthly_income': 4000,
            'monthly_debt': 1200,
            'loan_amount': 15000,
            'loan_purpose': 'personal',
            'employment_length': 2,
        }
        
        result = self.app.make_decision(data, 'individual')
        
        assert result['decision'] == 'DECLINED'
        assert 'Credit score' in result['reason']
    
    def test_declined_individual_application_high_dti(self):
        """Test individual application declined for high DTI."""
        data = {
            'credit_score': 720,
            'monthly_income': 4000,
            'monthly_debt': 2000,  # 50% DTI, above max
            'loan_amount': 20000,
            'loan_purpose': 'debt_consolidation',
            'employment_length': 5,
        }
        
        result = self.app.make_decision(data, 'individual')
        
        assert result['decision'] == 'DECLINED'
        assert 'DTI ratio' in result['reason']
    
    def test_conditional_approval(self):
        """Test application that gets conditional approval."""
        data = {
            'credit_score': 650,  # Borderline
            'monthly_income': 3500,
            'monthly_debt': 1400,  # ~40% DTI
            'loan_amount': 30000,  # High loan amount
            'loan_purpose': 'business',  # Higher risk purpose
            'employment_length': 2,
        }
        
        result = self.app.make_decision(data, 'individual')
        
        # Should be conditional or declined due to risk factors
        assert result['decision'] in ['CONDITIONAL', 'DECLINED']
    
    def test_corporate_application_approved(self):
        """Test corporate application that should be approved."""
        data = {
            'annual_revenue': 5000000,
            'net_income': 750000,  # 15% profit margin
            'loan_amount': 1000000,
            'years_in_business': 12,
            'employee_count': 85,
            'industry': 'technology',
            'assets': 3000000,
            'liabilities': 1200000,
            'business_credit_score': 720,
            'management_experience': 15,
        }
        
        result = self.app.make_decision(data, 'corporate')
        
        assert result['decision'] in ['APPROVED', 'CONDITIONAL']
        assert 'risk_score' in result
    
    def test_corporate_application_declined(self):
        """Test corporate application that should be declined."""
        data = {
            'annual_revenue': 200000,  # Low revenue
            'net_income': -50000,  # Losing money
            'loan_amount': 500000,  # High loan relative to revenue
            'years_in_business': 1,  # New business
            'employee_count': 3,
            'industry': 'retail',
            'assets': 100000,
            'liabilities': 200000,  # More debt than assets
            'business_credit_score': 550,
            'management_experience': 2,
        }
        
        result = self.app.make_decision(data, 'corporate')
        
        assert result['decision'] in ['DECLINED', 'CONDITIONAL']
        assert result['risk_score'] > 0.5  # Should be high risk
    
    def test_economic_indicators_impact(self):
        """Test that economic indicators affect decisions."""
        data = {
            'credit_score': 680,  # Borderline
            'monthly_income': 4500,
            'monthly_debt': 1800,
            'loan_amount': 25000,
            'loan_purpose': 'auto',
            'employment_length': 4,
        }
        
        # Test with favorable economic conditions
        favorable_economics = {
            'gdp_growth': 0.04,  # Strong growth
            'unemployment_rate': 0.03,  # Low unemployment
            'inflation_rate': 0.02,  # Moderate inflation
        }
        
        self.app.update_economic_indicators(favorable_economics)
        result_favorable = self.app.make_decision(data, 'individual')
        
        # Test with unfavorable economic conditions
        unfavorable_economics = {
            'gdp_growth': -0.01,  # Recession
            'unemployment_rate': 0.08,  # High unemployment
            'inflation_rate': 0.06,  # High inflation
        }
        
        self.app.update_economic_indicators(unfavorable_economics)
        result_unfavorable = self.app.make_decision(data, 'individual')
        
        # Economic conditions should affect risk scores
        if 'risk_score' in result_favorable and 'risk_score' in result_unfavorable:
            assert result_unfavorable['risk_score'] > result_favorable['risk_score']
    
    def test_risk_breakdown(self):
        """Test detailed risk breakdown functionality."""
        data = {
            'credit_score': 700,
            'monthly_income': 5000,
            'monthly_debt': 1500,
            'loan_amount': 20000,
            'loan_purpose': 'home_improvement',
            'employment_length': 6,
        }
        
        breakdown = self.app.get_risk_breakdown(data, 'individual')
        
        assert 'total_risk_score' in breakdown
        assert 'credit_score_risk' in breakdown
        assert 'dti_risk' in breakdown
        
        # Check that each component has required fields
        for component in ['credit_score_risk', 'dti_risk']:
            assert 'value' in breakdown[component]
            assert 'weight' in breakdown[component]
            assert 'contribution' in breakdown[component]
    
    def test_model_performance_metrics(self):
        """Test model performance metrics retrieval."""
        performance = self.app.get_model_performance()
        
        assert 'individual_model' in performance
        assert 'corporate_model' in performance
        assert 'economic_indicators' in performance
        
        # Check that models have version info
        assert 'model_version' in performance['individual_model']
        assert 'model_version' in performance['corporate_model']

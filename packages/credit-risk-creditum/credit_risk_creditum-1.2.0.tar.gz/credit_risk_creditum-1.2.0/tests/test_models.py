"""Tests for risk assessment models."""

import pytest
from credit_risk.models.risk_models import IndividualRiskModel, CorporateRiskModel
from credit_risk.models.ml_models import RandomForestModel, LogisticRegressionModel


class TestIndividualRiskModel:
    """Test cases for IndividualRiskModel."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.model = IndividualRiskModel()
    
    def test_low_risk_application(self):
        """Test application that should have low risk score."""
        data = {
            'credit_score': 800,
            'monthly_income': 8000,
            'monthly_debt': 1200,  # 15% DTI
            'loan_amount': 20000,
            'employment_length': 10,
            'loan_purpose': 'home_improvement',
        }
        
        risk_score = self.model.calculate_risk_score(data)
        assert 0 <= risk_score <= 1
        assert risk_score < 0.3  # Should be low risk
    
    def test_high_risk_application(self):
        """Test application that should have high risk score."""
        data = {
            'credit_score': 550,
            'monthly_income': 2500,
            'monthly_debt': 1800,  # 72% DTI
            'loan_amount': 35000,
            'employment_length': 0.5,
            'loan_purpose': 'vacation',  # High risk purpose
        }
        
        risk_score = self.model.calculate_risk_score(data)
        assert 0 <= risk_score <= 1
        assert risk_score > 0.6  # Should be high risk
    
    def test_risk_breakdown(self):
        """Test detailed risk breakdown."""
        data = {
            'credit_score': 700,
            'monthly_income': 5000,
            'monthly_debt': 1500,
            'loan_amount': 25000,
            'employment_length': 5,
            'loan_purpose': 'auto',
        }
        
        breakdown = self.model.get_risk_breakdown(data)
        
        assert 'total_risk_score' in breakdown
        assert 'credit_score_risk' in breakdown
        assert 'dti_risk' in breakdown
        assert 'employment_risk' in breakdown
        assert 'purpose_risk' in breakdown
        
        # Verify contributions sum correctly (approximately)
        total_contribution = sum(
            breakdown[key]['contribution'] 
            for key in breakdown 
            if isinstance(breakdown[key], dict) and 'contribution' in breakdown[key]
        )
        
        assert abs(total_contribution - breakdown['total_risk_score']) < 0.01


class TestCorporateRiskModel:
    """Test cases for CorporateRiskModel."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.model = CorporateRiskModel()
    
    def test_low_risk_corporate(self):
        """Test corporate application that should have low risk."""
        data = {
            'annual_revenue': 10000000,
            'net_income': 1500000,  # 15% margin
            'assets': 8000000,
            'liabilities': 2000000,  # 25% debt ratio
            'years_in_business': 20,
            'employee_count': 150,
            'industry': 'healthcare',
            'business_credit_score': 750,
            'management_experience': 25,
        }
        
        risk_score = self.model.calculate_risk_score(data)
        assert 0 <= risk_score <= 1
        assert risk_score < 0.4  # Should be low-medium risk
    
    def test_high_risk_corporate(self):
        """Test corporate application that should have high risk."""
        data = {
            'annual_revenue': 500000,
            'net_income': -100000,  # Losing money
            'assets': 200000,
            'liabilities': 400000,  # 200% debt ratio
            'years_in_business': 1,
            'employee_count': 5,
            'industry': 'hospitality',  # Higher risk industry
            'business_credit_score': 580,
            'management_experience': 2,
        }
        
        risk_score = self.model.calculate_risk_score(data)
        assert 0 <= risk_score <= 1
        assert risk_score > 0.6  # Should be high risk
    
    def test_industry_risk_scores(self):
        """Test that different industries have different risk scores."""
        base_data = {
            'annual_revenue': 2000000,
            'net_income': 200000,
            'assets': 1000000,
            'liabilities': 500000,
            'years_in_business': 8,
            'employee_count': 30,
            'business_credit_score': 680,
            'management_experience': 10,
        }
        
        # Test different industries
        tech_data = {**base_data, 'industry': 'technology'}
        hospitality_data = {**base_data, 'industry': 'hospitality'}
        
        tech_risk = self.model.calculate_risk_score(tech_data)
        hospitality_risk = self.model.calculate_risk_score(hospitality_data)
        
        # Hospitality should generally be higher risk than technology
        assert hospitality_risk > tech_risk


class TestMLModels:
    """Test cases for machine learning models."""
    
    def test_random_forest_model_init(self):
        """Test RandomForest model initialization."""
        model = RandomForestModel()
        assert model.model is not None
        assert not model.is_trained
        assert len(model.feature_names) > 0
    
    def test_logistic_regression_model_init(self):
        """Test LogisticRegression model initialization."""
        model = LogisticRegressionModel()
        assert model.model is not None
        assert not model.is_trained
        assert len(model.feature_names) > 0
    
    def test_feature_preparation(self):
        """Test feature preparation for ML models."""
        rf_model = RandomForestModel()
        lr_model = LogisticRegressionModel()
        
        test_data = {
            'credit_score': 720,
            'monthly_income': 5000,
            'monthly_debt': 1500,
            'loan_amount': 20000,
            'employment_length': 5,
        }
        
        rf_features = rf_model.prepare_features(test_data)
        lr_features = lr_model.prepare_features(test_data)
        
        assert rf_features.shape == (1, len(rf_model.feature_names))
        assert lr_features.shape == (1, len(lr_model.feature_names))
    
    def test_untrained_model_prediction(self):
        """Test prediction with untrained model."""
        model = RandomForestModel()
        
        test_data = {
            'credit_score': 720,
            'monthly_income': 5000,
            'monthly_debt': 1500,
            'loan_amount': 20000,
            'employment_length': 5,
        }
        
        result = model.predict(test_data)
        
        assert 'prediction' in result
        assert 'probability' in result
        assert 'confidence' in result
        assert result['confidence'] == 'low'
        assert result['model_used'] == 'default'

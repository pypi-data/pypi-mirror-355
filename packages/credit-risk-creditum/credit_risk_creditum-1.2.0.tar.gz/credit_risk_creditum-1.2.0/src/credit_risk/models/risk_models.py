"""Risk assessment models for individual and corporate applications."""

import logging
from typing import Dict, Any, Optional
import numpy as np
from ..utils.helpers import calculate_dti_ratio, normalize_score

logger = logging.getLogger(__name__)


class BaseRiskModel:
    """Base class for risk models."""
    
    def __init__(self):
        """Initialize base risk model."""
        self.model_version = "1.0"
        self.last_updated = None
    
    def calculate_risk_score(self, data: Dict[str, Any]) -> float:
        """Calculate risk score. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement calculate_risk_score")
    
    def get_risk_breakdown(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed risk breakdown. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement get_risk_breakdown")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get model performance metrics."""
        return {
            'model_version': self.model_version,
            'last_updated': self.last_updated,
            'model_type': self.__class__.__name__
        }


class IndividualRiskModel(BaseRiskModel):
    """Risk assessment model for individual credit applications."""
    
    def __init__(self):
        """Initialize individual risk model."""
        super().__init__()
        
        # Risk factor weights
        self.weights = {
            'credit_score': 0.35,
            'dti_ratio': 0.25,
            'employment_length': 0.15,
            'loan_to_income': 0.15,
            'purpose_risk': 0.10
        }
        
        # Risk categories for loan purposes
        self.purpose_risk_scores = {
            'debt_consolidation': 0.2,
            'home_improvement': 0.1,
            'auto': 0.15,
            'business': 0.4,
            'personal': 0.3,
            'medical': 0.25,
            'vacation': 0.5,
            'other': 0.35
        }
    
    def calculate_risk_score(self, data: Dict[str, Any]) -> float:
        """
        Calculate individual risk score.
        
        Args:
            data: Application data dictionary
            
        Returns:
            Risk score between 0 (low risk) and 1 (high risk)
        """
        try:
            total_score = 0.0
            
            # Credit score component (inverted - higher credit score = lower risk)
            credit_score = data.get('credit_score', 650)
            credit_risk = max(0, (850 - credit_score) / 250)  # Normalize to 0-1
            total_score += credit_risk * self.weights['credit_score']
            
            # DTI ratio component
            dti_ratio = calculate_dti_ratio(
                data.get('monthly_income', 0),
                data.get('monthly_debt', 0)
            )
            dti_risk = min(1.0, dti_ratio / 0.5)  # Normalize, cap at 50% DTI
            total_score += dti_risk * self.weights['dti_ratio']
            
            # Employment length component (longer = lower risk)
            employment_length = data.get('employment_length', 0)
            employment_risk = max(0, (10 - employment_length) / 10)  # Normalize to 0-1
            total_score += employment_risk * self.weights['employment_length']
            
            # Loan to income ratio component
            loan_amount = data.get('loan_amount', 0)
            annual_income = data.get('annual_income', data.get('monthly_income', 0) * 12)
            
            if annual_income > 0:
                loan_to_income = loan_amount / annual_income
                lti_risk = min(1.0, loan_to_income / 5.0)  # Normalize, cap at 5x income
                total_score += lti_risk * self.weights['loan_to_income']
            
            # Loan purpose risk
            loan_purpose = data.get('loan_purpose', 'other')
            purpose_risk = self.purpose_risk_scores.get(loan_purpose, 0.35)
            total_score += purpose_risk * self.weights['purpose_risk']
            
            return min(1.0, max(0.0, total_score))
            
        except Exception as e:
            logger.error(f"Error calculating individual risk score: {str(e)}")
            return 0.5  # Default medium risk
    
    def get_risk_breakdown(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed risk breakdown for individual application."""
        credit_score = data.get('credit_score', 650)
        dti_ratio = calculate_dti_ratio(
            data.get('monthly_income', 0),
            data.get('monthly_debt', 0)
        )
        employment_length = data.get('employment_length', 0)
        loan_purpose = data.get('loan_purpose', 'other')
        
        # Calculate individual components
        credit_risk = max(0, (850 - credit_score) / 250)
        dti_risk = min(1.0, dti_ratio / 0.5)
        employment_risk = max(0, (10 - employment_length) / 10)
        purpose_risk = self.purpose_risk_scores.get(loan_purpose, 0.35)
        
        return {
            'credit_score_risk': {
                'value': credit_risk,
                'weight': self.weights['credit_score'],
                'contribution': credit_risk * self.weights['credit_score'],
                'raw_score': credit_score
            },
            'dti_risk': {
                'value': dti_risk,
                'weight': self.weights['dti_ratio'],
                'contribution': dti_risk * self.weights['dti_ratio'],
                'raw_ratio': dti_ratio
            },
            'employment_risk': {
                'value': employment_risk,
                'weight': self.weights['employment_length'],
                'contribution': employment_risk * self.weights['employment_length'],
                'raw_length': employment_length
            },
            'purpose_risk': {
                'value': purpose_risk,
                'weight': self.weights['purpose_risk'],
                'contribution': purpose_risk * self.weights['purpose_risk'],
                'raw_purpose': loan_purpose
            },
            'total_risk_score': self.calculate_risk_score(data)
        }


class CorporateRiskModel(BaseRiskModel):
    """Risk assessment model for corporate credit applications."""
    
    def __init__(self):
        """Initialize corporate risk model."""
        super().__init__()
        
        # Risk factor weights for corporate applications
        self.weights = {
            'financial_strength': 0.40,
            'business_stability': 0.25,
            'industry_risk': 0.20,
            'management_quality': 0.15
        }
        
        # Industry risk scores
        self.industry_risk_scores = {
            'technology': 0.3,
            'healthcare': 0.2,
            'finance': 0.25,
            'manufacturing': 0.3,
            'retail': 0.4,
            'hospitality': 0.5,
            'construction': 0.45,
            'energy': 0.35,
            'agriculture': 0.4,
            'real_estate': 0.35,
            'other': 0.4
        }
    
    def calculate_risk_score(self, data: Dict[str, Any]) -> float:
        """
        Calculate corporate risk score.
        
        Args:
            data: Corporate application data dictionary
            
        Returns:
            Risk score between 0 (low risk) and 1 (high risk)
        """
        try:
            total_score = 0.0
            
            # Financial strength component
            financial_score = self._calculate_financial_strength(data)
            total_score += financial_score * self.weights['financial_strength']
            
            # Business stability component
            stability_score = self._calculate_business_stability(data)
            total_score += stability_score * self.weights['business_stability']
            
            # Industry risk component
            industry = data.get('industry', 'other').lower()
            industry_risk = self.industry_risk_scores.get(industry, 0.4)
            total_score += industry_risk * self.weights['industry_risk']
            
            # Management quality component
            management_score = self._calculate_management_quality(data)
            total_score += management_score * self.weights['management_quality']
            
            return min(1.0, max(0.0, total_score))
            
        except Exception as e:
            logger.error(f"Error calculating corporate risk score: {str(e)}")
            return 0.5  # Default medium risk
    
    def _calculate_financial_strength(self, data: Dict[str, Any]) -> float:
        """Calculate financial strength score."""
        # Revenue and profitability
        annual_revenue = data.get('annual_revenue', 0)
        net_income = data.get('net_income', 0)
        assets = data.get('assets', 0)
        liabilities = data.get('liabilities', 0)
        
        score = 0.0
        
        # Profitability ratio
        if annual_revenue > 0:
            profit_margin = net_income / annual_revenue
            if profit_margin > 0.15:
                score += 0.1
            elif profit_margin > 0.05:
                score += 0.2
            else:
                score += 0.4
        else:
            score += 0.5
        
        # Debt-to-asset ratio
        if assets > 0:
            debt_ratio = liabilities / assets
            if debt_ratio < 0.3:
                score += 0.1
            elif debt_ratio < 0.6:
                score += 0.3
            else:
                score += 0.5
        else:
            score += 0.5
        
        return min(1.0, score)
    
    def _calculate_business_stability(self, data: Dict[str, Any]) -> float:
        """Calculate business stability score."""
        years_in_business = data.get('years_in_business', 0)
        employee_count = data.get('employee_count', 0)
        
        score = 0.0
        
        # Years in business
        if years_in_business >= 10:
            score += 0.1
        elif years_in_business >= 5:
            score += 0.2
        elif years_in_business >= 2:
            score += 0.3
        else:
            score += 0.5
        
        # Company size (employee count)
        if employee_count >= 100:
            score += 0.1
        elif employee_count >= 20:
            score += 0.2
        elif employee_count >= 5:
            score += 0.3
        else:
            score += 0.4
        
        return min(1.0, score)
    
    def _calculate_management_quality(self, data: Dict[str, Any]) -> float:
        """Calculate management quality score."""
        # This would typically involve more complex analysis
        # For now, use simple heuristics
        
        management_experience = data.get('management_experience', 0)
        credit_history = data.get('business_credit_score', 650)
        
        score = 0.0
        
        # Management experience
        if management_experience >= 10:
            score += 0.1
        elif management_experience >= 5:
            score += 0.2
        else:
            score += 0.3
        
        # Business credit score
        credit_risk = max(0, (850 - credit_history) / 250)
        score += credit_risk * 0.7
        
        return min(1.0, score)
    
    def get_risk_breakdown(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed risk breakdown for corporate application."""
        financial_score = self._calculate_financial_strength(data)
        stability_score = self._calculate_business_stability(data)
        management_score = self._calculate_management_quality(data)
        
        industry = data.get('industry', 'other').lower()
        industry_risk = self.industry_risk_scores.get(industry, 0.4)
        
        return {
            'financial_strength': {
                'value': financial_score,
                'weight': self.weights['financial_strength'],
                'contribution': financial_score * self.weights['financial_strength']
            },
            'business_stability': {
                'value': stability_score,
                'weight': self.weights['business_stability'],
                'contribution': stability_score * self.weights['business_stability']
            },
            'industry_risk': {
                'value': industry_risk,
                'weight': self.weights['industry_risk'],
                'contribution': industry_risk * self.weights['industry_risk'],
                'industry': industry
            },
            'management_quality': {
                'value': management_score,
                'weight': self.weights['management_quality'],
                'contribution': management_score * self.weights['management_quality']
            },
            'total_risk_score': self.calculate_risk_score(data)
        }

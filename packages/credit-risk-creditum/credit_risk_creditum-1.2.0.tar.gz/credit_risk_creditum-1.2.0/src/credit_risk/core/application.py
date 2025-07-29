"""Main application class for credit risk assessment."""

import logging
from typing import Dict, Any, Union, Optional
from ..models.risk_models import IndividualRiskModel, CorporateRiskModel
from ..utils.economic_indicators import EconomicIndicators
from ..utils.validators import validate_application
from .processor import ApplicationProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CreditApplication:
    """
    Main class for processing credit applications.
    
    This class handles both individual and corporate credit applications,
    integrating economic indicators and machine learning models for risk assessment.
    """
    
    def __init__(
        self,
        min_credit_score: int = 600,
        max_dti: float = 0.43,
        use_ml_models: bool = True,
        economic_weight: float = 0.2
    ):
        """
        Initialize the CreditApplication processor.
        
        Args:
            min_credit_score: Minimum acceptable credit score
            max_dti: Maximum debt-to-income ratio
            use_ml_models: Whether to use machine learning models
            economic_weight: Weight given to economic indicators
        """
        self.min_credit_score = min_credit_score
        self.max_dti = max_dti
        self.use_ml_models = use_ml_models
        self.economic_weight = economic_weight
        
        # Initialize components
        self.economic_indicators = EconomicIndicators()
        self.individual_model = IndividualRiskModel()
        self.corporate_model = CorporateRiskModel()
        self.processor = ApplicationProcessor()
        
        logger.info(f"CreditApplication initialized with min_score={min_credit_score}, max_dti={max_dti}")
    
    def make_decision(
        self, 
        application_data: Dict[str, Any], 
        application_type: str = 'individual'
    ) -> Dict[str, Any]:
        """
        Make a credit decision based on application data.
        
        Args:
            application_data: Dictionary containing application information
            application_type: Type of application ('individual' or 'corporate')
            
        Returns:
            Dictionary containing decision and risk assessment
        """
        try:
            # Validate input
            validate_application(application_data, application_type)
            
            # Process application based on type
            if application_type.lower() == 'individual':
                result = self._process_individual_application(application_data)
            elif application_type.lower() == 'corporate':
                result = self._process_corporate_application(application_data)
            else:
                raise ValueError(f"Unknown application type: {application_type}")
            
            logger.info(f"Decision made for {application_type} application: {result['decision']}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing application: {str(e)}")
            return {
                'decision': 'ERROR',
                'reason': str(e),
                'risk_score': None,
                'timestamp': self.processor.get_timestamp()
            }
    
    def _process_individual_application(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual credit application."""
        # Calculate basic risk score
        risk_score = self.individual_model.calculate_risk_score(data)
        
        # Apply economic indicators
        economic_adjustment = self.economic_indicators.get_risk_adjustment()
        adjusted_score = risk_score * (1 + economic_adjustment * self.economic_weight)
        
        # Make decision
        decision = self._make_credit_decision(data, adjusted_score, 'individual')
        
        return {
            'decision': decision['status'],
            'reason': decision['reason'],
            'risk_score': adjusted_score,
            'base_risk_score': risk_score,
            'economic_adjustment': economic_adjustment,
            'recommended_amount': decision.get('recommended_amount'),
            'interest_rate': decision.get('interest_rate'),
            'timestamp': self.processor.get_timestamp()
        }
    
    def _process_corporate_application(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process corporate credit application."""
        # Calculate corporate risk score
        risk_score = self.corporate_model.calculate_risk_score(data)
        
        # Apply economic indicators
        economic_adjustment = self.economic_indicators.get_risk_adjustment()
        adjusted_score = risk_score * (1 + economic_adjustment * self.economic_weight)
        
        # Make decision
        decision = self._make_credit_decision(data, adjusted_score, 'corporate')
        
        return {
            'decision': decision['status'],
            'reason': decision['reason'],
            'risk_score': adjusted_score,
            'base_risk_score': risk_score,
            'economic_adjustment': economic_adjustment,
            'recommended_amount': decision.get('recommended_amount'),
            'interest_rate': decision.get('interest_rate'),
            'timestamp': self.processor.get_timestamp()
        }
    
    def _make_credit_decision(
        self, 
        data: Dict[str, Any], 
        risk_score: float, 
        app_type: str
    ) -> Dict[str, Any]:
        """Make final credit decision based on risk score and criteria."""
        credit_score = data.get('credit_score', 0)
        requested_amount = data.get('loan_amount', 0)
        
        # Basic approval criteria
        if credit_score < self.min_credit_score:
            return {
                'status': 'DECLINED',
                'reason': f'Credit score {credit_score} below minimum {self.min_credit_score}'
            }
        
        # Calculate DTI for individuals
        if app_type == 'individual':
            monthly_income = data.get('monthly_income', 0)
            monthly_debt = data.get('monthly_debt', 0)
            
            if monthly_income > 0:
                dti_ratio = monthly_debt / monthly_income
                if dti_ratio > self.max_dti:
                    return {
                        'status': 'DECLINED',
                        'reason': f'DTI ratio {dti_ratio:.2f} exceeds maximum {self.max_dti}'
                    }
        
        # Risk-based decision
        if risk_score < 0.3:
            status = 'APPROVED'
            interest_rate = 0.05 + (risk_score * 0.1)  # 5-8% based on risk
            recommended_amount = requested_amount
        elif risk_score < 0.6:
            status = 'APPROVED'
            interest_rate = 0.08 + (risk_score * 0.15)  # 8-17% based on risk
            recommended_amount = min(requested_amount, requested_amount * 0.8)
        elif risk_score < 0.8:
            status = 'CONDITIONAL'
            interest_rate = 0.15 + (risk_score * 0.1)  # 15-25%
            recommended_amount = min(requested_amount, requested_amount * 0.5)
        else:
            status = 'DECLINED'
            return {
                'status': status,
                'reason': f'High risk score: {risk_score:.2f}'
            }
        
        return {
            'status': status,
            'reason': f'Risk score: {risk_score:.2f}',
            'interest_rate': round(interest_rate, 4),
            'recommended_amount': recommended_amount
        }
    
    def get_risk_breakdown(self, application_data: Dict[str, Any], application_type: str) -> Dict[str, Any]:
        """Get detailed risk breakdown for an application."""
        if application_type.lower() == 'individual':
            return self.individual_model.get_risk_breakdown(application_data)
        elif application_type.lower() == 'corporate':
            return self.corporate_model.get_risk_breakdown(application_data)
        else:
            raise ValueError(f"Unknown application type: {application_type}")
    
    def update_economic_indicators(self, indicators: Dict[str, float]) -> None:
        """Update economic indicators."""
        self.economic_indicators.update_indicators(indicators)
        logger.info("Economic indicators updated")
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get performance metrics for the models."""
        return {
            'individual_model': self.individual_model.get_performance_metrics(),
            'corporate_model': self.corporate_model.get_performance_metrics(),
            'economic_indicators': self.economic_indicators.get_current_indicators()
        }

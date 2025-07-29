"""Application processing utilities."""

import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ApplicationProcessor:
    """Utility class for processing credit applications."""
    
    def __init__(self):
        """Initialize the processor."""
        self.processed_count = 0
        self.start_time = datetime.datetime.now()
    
    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.datetime.now().isoformat()
    
    def preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess application data.
        
        Args:
            data: Raw application data
            
        Returns:
            Preprocessed data
        """
        processed_data = data.copy()
        
        # Convert string numbers to float/int
        numeric_fields = [
            'credit_score', 'monthly_income', 'monthly_debt', 'loan_amount',
            'annual_income', 'employment_length', 'assets', 'liabilities'
        ]
        
        for field in numeric_fields:
            if field in processed_data and isinstance(processed_data[field], str):
                try:
                    if '.' in processed_data[field]:
                        processed_data[field] = float(processed_data[field])
                    else:
                        processed_data[field] = int(processed_data[field])
                except ValueError:
                    logger.warning(f"Could not convert {field} to numeric: {processed_data[field]}")
        
        # Standardize categorical fields
        categorical_mappings = {
            'loan_purpose': {
                'home': 'home_improvement',
                'car': 'auto',
                'debt_consolidation': 'debt_consolidation',
                'business': 'business',
                'personal': 'personal'
            },
            'employment_status': {
                'employed': 'employed',
                'self_employed': 'self_employed',
                'unemployed': 'unemployed',
                'retired': 'retired'
            }
        }
        
        for field, mapping in categorical_mappings.items():
            if field in processed_data:
                value = str(processed_data[field]).lower()
                processed_data[field] = mapping.get(value, value)
        
        self.processed_count += 1
        return processed_data
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        Validate that required fields are present.
        
        Args:
            data: Application data
            required_fields: List of required field names
            
        Returns:
            List of missing fields
        """
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        return missing_fields
    
    def calculate_derived_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate derived fields from base data.
        
        Args:
            data: Application data
            
        Returns:
            Data with derived fields added
        """
        result = data.copy()
        
        # Calculate DTI ratio
        if 'monthly_income' in data and 'monthly_debt' in data:
            monthly_income = data['monthly_income']
            monthly_debt = data['monthly_debt']
            if monthly_income and monthly_income > 0:
                result['dti_ratio'] = monthly_debt / monthly_income
        
        # Calculate loan-to-income ratio
        if 'loan_amount' in data and 'annual_income' in data:
            loan_amount = data['loan_amount']
            annual_income = data['annual_income']
            if annual_income and annual_income > 0:
                result['loan_to_income_ratio'] = loan_amount / annual_income
        
        # Calculate net worth (for corporate applications)
        if 'assets' in data and 'liabilities' in data:
            assets = data['assets'] or 0
            liabilities = data['liabilities'] or 0
            result['net_worth'] = assets - liabilities
        
        return result
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        uptime = datetime.datetime.now() - self.start_time
        
        return {
            'processed_applications': self.processed_count,
            'uptime_seconds': uptime.total_seconds(),
            'start_time': self.start_time.isoformat(),
            'current_time': datetime.datetime.now().isoformat()
        }

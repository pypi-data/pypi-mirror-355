"""Economic indicators management and integration."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EconomicIndicators:
    """Class for managing and applying economic indicators to risk assessment."""
    
    def __init__(self):
        """Initialize economic indicators with default values."""
        self.indicators = {
            'cpi': 0.025,  # Consumer Price Index (inflation)
            'gdp_growth': 0.025,  # GDP growth rate
            'unemployment_rate': 0.05,  # Unemployment rate
            'interest_rate': 0.05,  # Federal funds rate
            'inflation_rate': 0.025,  # Inflation rate
            'housing_price_index': 0.03,  # Housing price growth
            'consumer_confidence': 100,  # Consumer confidence index
            'market_volatility': 0.15,  # Market volatility index
        }
        
        self.last_updated = datetime.now()
        self.update_frequency = timedelta(days=1)  # Daily updates recommended
        
        # Weights for different economic factors
        self.weights = {
            'cpi': 0.15,
            'gdp_growth': 0.20,
            'unemployment_rate': 0.25,
            'interest_rate': 0.20,
            'inflation_rate': 0.10,
            'housing_price_index': 0.05,
            'consumer_confidence': 0.03,
            'market_volatility': 0.02,
        }
    
    def update_indicators(self, new_indicators: Dict[str, float]) -> None:
        """
        Update economic indicators.
        
        Args:
            new_indicators: Dictionary of indicator name -> value
        """
        try:
            for key, value in new_indicators.items():
                if key in self.indicators:
                    self.indicators[key] = float(value)
                    logger.debug(f"Updated {key}: {value}")
                else:
                    logger.warning(f"Unknown economic indicator: {key}")
            
            self.last_updated = datetime.now()
            logger.info(f"Economic indicators updated at {self.last_updated}")
            
        except Exception as e:
            logger.error(f"Error updating economic indicators: {str(e)}")
    
    def get_risk_adjustment(self) -> float:
        """
        Calculate risk adjustment factor based on current economic conditions.
        
        Returns:
            Risk adjustment factor (-1 to 1, where negative = lower risk, positive = higher risk)
        """
        try:
            total_adjustment = 0.0
            
            # CPI/Inflation impact (higher inflation = higher risk)
            cpi_impact = (self.indicators['cpi'] - 0.02) * 2  # Normalize around 2% target
            total_adjustment += cpi_impact * self.weights['cpi']
            
            # GDP growth impact (higher growth = lower risk)
            gdp_impact = -(self.indicators['gdp_growth'] - 0.025) * 2  # Normalize around 2.5%
            total_adjustment += gdp_impact * self.weights['gdp_growth']
            
            # Unemployment impact (higher unemployment = higher risk)
            unemployment_impact = (self.indicators['unemployment_rate'] - 0.05) * 2
            total_adjustment += unemployment_impact * self.weights['unemployment_rate']
            
            # Interest rate impact (higher rates = higher risk for borrowers)
            interest_impact = (self.indicators['interest_rate'] - 0.025) * 1.5
            total_adjustment += interest_impact * self.weights['interest_rate']
            
            # Inflation rate impact
            inflation_impact = (self.indicators['inflation_rate'] - 0.02) * 2
            total_adjustment += inflation_impact * self.weights['inflation_rate']
            
            # Housing price index impact
            housing_impact = (self.indicators['housing_price_index'] - 0.03) * 1
            total_adjustment += housing_impact * self.weights['housing_price_index']
            
            # Consumer confidence impact (higher confidence = lower risk)
            confidence_impact = -(self.indicators['consumer_confidence'] - 100) / 100
            total_adjustment += confidence_impact * self.weights['consumer_confidence']
            
            # Market volatility impact (higher volatility = higher risk)
            volatility_impact = (self.indicators['market_volatility'] - 0.15) * 2
            total_adjustment += volatility_impact * self.weights['market_volatility']
            
            # Cap adjustment between -0.5 and 0.5 (50% max adjustment)
            return max(-0.5, min(0.5, total_adjustment))
            
        except Exception as e:
            logger.error(f"Error calculating risk adjustment: {str(e)}")
            return 0.0  # Default to no adjustment
    
    def get_current_indicators(self) -> Dict[str, Any]:
        """Get current economic indicators with metadata."""
        return {
            'indicators': self.indicators.copy(),
            'last_updated': self.last_updated.isoformat(),
            'risk_adjustment': self.get_risk_adjustment(),
            'weights': self.weights.copy(),
            'is_stale': self._is_data_stale()
        }
    
    def _is_data_stale(self) -> bool:
        """Check if economic data is stale and needs updating."""
        return datetime.now() - self.last_updated > self.update_frequency
    
    def get_economic_summary(self) -> Dict[str, Any]:
        """Get summary of economic conditions."""
        risk_adjustment = self.get_risk_adjustment()
        
        if risk_adjustment < -0.2:
            economic_outlook = "Favorable"
            risk_description = "Economic conditions are favorable for lending"
        elif risk_adjustment < 0.1:
            economic_outlook = "Neutral"
            risk_description = "Economic conditions are neutral"
        elif risk_adjustment < 0.3:
            economic_outlook = "Cautious"
            risk_description = "Economic conditions suggest increased caution"
        else:
            economic_outlook = "Unfavorable"
            risk_description = "Economic conditions are unfavorable for lending"
        
        return {
            'outlook': economic_outlook,
            'risk_adjustment': risk_adjustment,
            'description': risk_description,
            'key_factors': self._get_key_economic_factors(),
            'last_updated': self.last_updated.isoformat()
        }
    
    def _get_key_economic_factors(self) -> Dict[str, str]:
        """Identify key economic factors affecting risk."""
        factors = {}
        
        if self.indicators['unemployment_rate'] > 0.07:
            factors['unemployment'] = f"High unemployment at {self.indicators['unemployment_rate']:.1%}"
        
        if self.indicators['inflation_rate'] > 0.05:
            factors['inflation'] = f"High inflation at {self.indicators['inflation_rate']:.1%}"
        
        if self.indicators['gdp_growth'] < 0:
            factors['gdp'] = f"Negative GDP growth at {self.indicators['gdp_growth']:.1%}"
        
        if self.indicators['interest_rate'] > 0.08:
            factors['interest_rates'] = f"High interest rates at {self.indicators['interest_rate']:.1%}"
        
        return factors

# API Reference

## Core Classes

### CreditApplication

Main class for processing credit applications.

```python
class CreditApplication:
    def __init__(self, min_credit_score=600, max_dti=0.43, use_ml_models=True, economic_weight=0.2)
    def make_decision(self, application_data: Dict[str, Any], application_type: str) -> Dict[str, Any]
    def get_risk_breakdown(self, application_data: Dict[str, Any], application_type: str) -> Dict[str, Any]
    def update_economic_indicators(self, indicators: Dict[str, float]) -> None
    def get_model_performance(self) -> Dict[str, Any]
```

#### Methods

##### make_decision(application_data, application_type)

Process a credit application and return a decision.

**Parameters:**
- `application_data` (Dict): Application information
- `application_type` (str): 'individual' or 'corporate'

**Returns:**
- Dict containing decision, risk_score, reason, and recommended terms

##### get_risk_breakdown(application_data, application_type)

Get detailed risk factor breakdown.

**Parameters:**
- `application_data` (Dict): Application information
- `application_type` (str): 'individual' or 'corporate'

**Returns:**
- Dict with detailed risk factor contributions

##### update_economic_indicators(indicators)

Update economic indicators used in risk assessment.

**Parameters:**
- `indicators` (Dict): Economic indicator values

## Risk Models

### IndividualRiskModel

Risk assessment model for individual applications.

```python
class IndividualRiskModel:
    def calculate_risk_score(self, data: Dict[str, Any]) -> float
    def get_risk_breakdown(self, data: Dict[str, Any]) -> Dict[str, Any]
    def get_performance_metrics(self) -> Dict[str, Any]
```

### CorporateRiskModel

Risk assessment model for corporate applications.

```python
class CorporateRiskModel:
    def calculate_risk_score(self, data: Dict[str, Any]) -> float
    def get_risk_breakdown(self, data: Dict[str, Any]) -> Dict[str, Any]
    def get_performance_metrics(self) -> Dict[str, Any]
```

## Machine Learning Models

### RandomForestModel

Random Forest classifier for credit risk prediction.

```python
class RandomForestModel:
    def __init__(self, n_estimators=100, random_state=42)
    def train(self, training_data: List[Dict], labels: List[int]) -> None
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]
    def prepare_features(self, data: Dict[str, Any]) -> np.ndarray
```

### LogisticRegressionModel

Logistic Regression classifier for credit risk prediction.

```python
class LogisticRegressionModel:
    def __init__(self, random_state=42)
    def train(self, training_data: List[Dict], labels: List[int]) -> None
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]
    def prepare_features(self, data: Dict[str, Any]) -> np.ndarray
```

## Utility Classes

### EconomicIndicators

Manages economic indicators and their impact on risk assessment.

```python
class EconomicIndicators:
    def update_indicators(self, new_indicators: Dict[str, float]) -> None
    def get_risk_adjustment(self) -> float
    def get_current_indicators(self) -> Dict[str, Any]
    def get_economic_summary(self) -> Dict[str, Any]
```

## Utility Functions

### Helpers

```python
def calculate_dti_ratio(monthly_income: float, monthly_debt: float) -> float
def normalize_score(score: float, min_val: float, max_val: float) -> float
def format_currency(amount: Union[int, float], currency: str = "USD") -> str
def format_percentage(value: float, decimal_places: int = 2) -> str
def calculate_loan_to_income_ratio(loan_amount: float, annual_income: float) -> float
def calculate_monthly_payment(principal: float, annual_rate: float, years: int) -> float
def risk_grade_from_score(risk_score: float) -> str
```

### Validators

```python
def validate_application(data: Dict[str, Any], application_type: str) -> None
def validate_numeric_field(value: Any, field_name: str, min_val: float = None, max_val: float = None, allow_none: bool = False) -> float
def validate_categorical_field(value: Any, field_name: str, valid_values: List[str], allow_none: bool = False) -> str
def sanitize_application_data(data: Dict[str, Any]) -> Dict[str, Any]
```

## Data Structures

### Application Data (Individual)

```python
{
    'credit_score': int,           # 300-850
    'monthly_income': float,       # Monthly gross income
    'monthly_debt': float,         # Monthly debt payments
    'loan_amount': float,          # Requested loan amount
    'loan_purpose': str,           # Optional: loan purpose
    'employment_length': int,      # Optional: years employed
    'annual_income': float,        # Optional: annual income
}
```

### Application Data (Corporate)

```python
{
    'annual_revenue': float,       # Annual company revenue
    'loan_amount': float,          # Requested loan amount
    'years_in_business': int,      # Years in business
    'net_income': float,           # Optional: annual net income
    'assets': float,               # Optional: total assets
    'liabilities': float,          # Optional: total liabilities
    'employee_count': int,         # Optional: number of employees
    'industry': str,               # Optional: industry sector
    'business_credit_score': int,  # Optional: business credit score
    'management_experience': int,  # Optional: years of management experience
}
```

### Decision Response

```python
{
    'decision': str,               # APPROVED, DECLINED, CONDITIONAL, ERROR
    'reason': str,                 # Explanation for decision
    'risk_score': float,           # Risk score (0-1)
    'base_risk_score': float,      # Risk score before economic adjustment
    'economic_adjustment': float,  # Economic adjustment factor
    'recommended_amount': float,   # Approved loan amount
    'interest_rate': float,        # Recommended interest rate
    'timestamp': str,              # Decision timestamp
}
```

### Economic Indicators

```python
{
    'cpi': float,                  # Consumer Price Index
    'gdp_growth': float,           # GDP growth rate
    'unemployment_rate': float,    # Unemployment rate
    'interest_rate': float,        # Interest rate
    'inflation_rate': float,       # Inflation rate
    'housing_price_index': float,  # Housing price index
    'consumer_confidence': float,  # Consumer confidence index
    'market_volatility': float,    # Market volatility index
}
```

## Constants

### Industry Risk Scores

```python
INDUSTRY_RISK_SCORES = {
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
```

### Loan Purpose Risk Scores

```python
LOAN_PURPOSE_RISK_SCORES = {
    'debt_consolidation': 0.2,
    'home_improvement': 0.1,
    'auto': 0.15,
    'business': 0.4,
    'personal': 0.3,
    'medical': 0.25,
    'vacation': 0.5,
    'other': 0.35
}
```

## Error Handling

The package includes comprehensive error handling with specific exception types:

- **ValueError**: For invalid input data or parameters
- **TypeError**: For incorrect data types
- **Generic Exception**: For unexpected errors

All functions that can fail return appropriate error information in their response dictionaries.

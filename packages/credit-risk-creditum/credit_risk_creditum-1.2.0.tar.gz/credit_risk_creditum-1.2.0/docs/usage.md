# Usage Guide

## Quick Start

```python
from credit_risk import CreditApplication

# Initialize the credit application processor
credit_app = CreditApplication()

# Process an individual application
application_data = {
    'credit_score': 720,
    'monthly_income': 5000,
    'monthly_debt': 1500,
    'loan_amount': 20000,
    'loan_purpose': 'home_improvement',
    'employment_length': 5,
}

result = credit_app.make_decision(application_data, 'individual')
print(f"Decision: {result['decision']}")
print(f"Risk Score: {result['risk_score']:.3f}")
```

## Individual Applications

### Required Fields

- `credit_score`: Credit score (300-850)
- `monthly_income`: Monthly gross income
- `monthly_debt`: Monthly debt payments
- `loan_amount`: Requested loan amount

### Optional Fields

- `employment_length`: Years of employment
- `loan_purpose`: Purpose of loan
- `annual_income`: Annual income (calculated from monthly if not provided)

### Example

```python
individual_app = {
    'credit_score': 680,
    'monthly_income': 4500,
    'monthly_debt': 1800,
    'loan_amount': 25000,
    'loan_purpose': 'auto',
    'employment_length': 3,
}

result = credit_app.make_decision(individual_app, 'individual')
```

## Corporate Applications

### Required Fields

- `annual_revenue`: Annual company revenue
- `loan_amount`: Requested loan amount
- `years_in_business`: Years company has been operating

### Optional Fields

- `net_income`: Annual net income
- `assets`: Total assets
- `liabilities`: Total liabilities
- `employee_count`: Number of employees
- `industry`: Industry sector
- `business_credit_score`: Business credit score
- `management_experience`: Years of management experience

### Example

```python
corporate_app = {
    'annual_revenue': 2000000,
    'net_income': 300000,
    'loan_amount': 500000,
    'years_in_business': 8,
    'employee_count': 25,
    'industry': 'technology',
    'assets': 1500000,
    'liabilities': 800000,
}

result = credit_app.make_decision(corporate_app, 'corporate')
```

## Economic Indicators

Update economic conditions to affect risk assessment:

```python
economic_data = {
    'cpi': 0.025,                    # Consumer Price Index
    'gdp_growth': 0.03,              # GDP growth rate
    'unemployment_rate': 0.045,      # Unemployment rate
    'interest_rate': 0.05,           # Interest rate
    'inflation_rate': 0.025,         # Inflation rate
}

credit_app.update_economic_indicators(economic_data)
```

## Risk Analysis

Get detailed risk breakdown:

```python
breakdown = credit_app.get_risk_breakdown(application_data, 'individual')

for factor, details in breakdown.items():
    if isinstance(details, dict) and 'contribution' in details:
        print(f"{factor}: {details['contribution']:.3f}")
```

## Configuration Options

Customize the credit application processor:

```python
credit_app = CreditApplication(
    min_credit_score=600,     # Minimum acceptable credit score
    max_dti=0.43,            # Maximum debt-to-income ratio
    use_ml_models=True,      # Use machine learning models
    economic_weight=0.2      # Weight of economic factors
)
```

## Decision Types

The system returns one of four decision types:

- **APPROVED**: Application approved with recommended terms
- **CONDITIONAL**: Approved with conditions or reduced amount
- **DECLINED**: Application declined
- **ERROR**: Error processing application

## Command Line Interface

Use the CLI for quick assessments:

```bash
# Interactive mode
credit-risk --interactive --type individual

# From JSON file
credit-risk --file application.json --type corporate

# From JSON string
credit-risk --data '{"credit_score": 720, "monthly_income": 5000}' --type individual

# Different output formats
credit-risk --file app.json --output json
credit-risk --file app.json --output detailed
```

## Error Handling

The system includes comprehensive error handling:

```python
try:
    result = credit_app.make_decision(application_data, 'individual')
    if result['decision'] == 'ERROR':
        print(f"Error: {result['reason']}")
    else:
        print(f"Decision: {result['decision']}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

- **Validate Input**: Always validate application data before processing
- **Handle Errors**: Implement proper error handling
- **Update Economics**: Regularly update economic indicators
- **Monitor Performance**: Track model performance over time
- **Log Decisions**: Keep audit trails of credit decisions

## Advanced Usage

### Custom Risk Models

```python
from credit_risk.models.risk_models import IndividualRiskModel

# Use risk models directly
risk_model = IndividualRiskModel()
risk_score = risk_model.calculate_risk_score(application_data)
breakdown = risk_model.get_risk_breakdown(application_data)
```

### Machine Learning Models

```python
from credit_risk.models.ml_models import RandomForestModel

# Train and use ML models
ml_model = RandomForestModel()
# ml_model.train(training_data, labels)  # When you have training data
prediction = ml_model.predict(application_data)
```

### Economic Analysis

```python
from credit_risk.utils.economic_indicators import EconomicIndicators

indicators = EconomicIndicators()
summary = indicators.get_economic_summary()
print(f"Economic outlook: {summary['outlook']}")
```

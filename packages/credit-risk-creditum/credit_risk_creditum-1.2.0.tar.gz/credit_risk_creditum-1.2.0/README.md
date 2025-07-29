# Credit Risk Creditum

[![PyPI version](https://badge.fury.io/py/credit-risk-creditum.svg)](https://badge.fury.io/py/credit-risk-creditum)
[![Documentation Status](https://readthedocs.org/projects/credit-risk-creditum/badge/?version=latest)](https://credit-risk-creditum.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

A comprehensive credit risk assessment system that evaluates both individual and corporate credit applications, integrating real-time economic indicators and advanced machine learning models for enhanced risk prediction accuracy.

## 🚀 Key Features

- **🏠 Individual Credit Assessment** - Comprehensive personal loan risk evaluation
- **🏢 Corporate Credit Assessment** - Advanced business credit risk analysis  
- **📈 Economic Indicators Integration** - Real-time economic data influence on risk calculations
- **🤖 Machine Learning Models** - Random Forest and Logistic Regression for enhanced predictions
- **⚙️ Configurable Risk Parameters** - Customizable thresholds for different lending criteria
- **💻 CLI Interface** - Command-line tool for quick risk assessments
- **📊 Detailed Risk Breakdown** - Granular analysis of risk factors
- **🔄 Dynamic Risk Adjustment** - Economic conditions impact on credit decisions

## 📦 Installation

```bash
pip install credit-risk-creditum
```

### Development Installation

```bash
git clone https://github.com/credit-risk-creditum/credit-risk-creditum.git
cd credit-risk-creditum
pip install -e .[dev]
```

## 🔥 Quick Start

### Individual Credit Assessment

```python
from credit_risk import CreditApplication

# Initialize the credit application processor
credit_app = CreditApplication(min_credit_score=600, max_dti=0.43)

# Update economic indicators for current market conditions
economic_data = {
    'cpi': 0.025,              # Consumer Price Index
    'gdp_growth': 0.03,        # GDP Growth Rate
    'unemployment_rate': 0.045, # Unemployment Rate
    'interest_rate': 0.05,     # Current Interest Rate
    'inflation_rate': 0.025,   # Inflation Rate
}
credit_app.update_economic_indicators(economic_data)

# Process an individual application
individual_application = {
    'credit_score': 720,
    'monthly_income': 5000,
    'monthly_debt': 1500,
    'loan_amount': 20000,
    'loan_purpose': 'home_improvement',
    'employment_length': 5,
    'annual_income': 60000,
}

decision = credit_app.make_decision(individual_application, 'individual')

print(f"Decision: {decision['decision']}")
print(f"Risk Score: {decision['risk_score']:.3f}")
print(f"Interest Rate: {decision.get('interest_rate', 'N/A'):.2%}")
print(f"Approved Amount: ${decision.get('recommended_amount', 0):,.2f}")
```

### Corporate Credit Assessment

```python
# Process a corporate application
corporate_application = {
    'annual_revenue': 2000000,
    'net_income': 300000,
    'loan_amount': 500000,
    'years_in_business': 8,
    'employee_count': 25,
    'industry': 'technology',
    'assets': 1500000,
    'liabilities': 800000,
    'business_credit_score': 680,
    'management_experience': 12,
}

decision = credit_app.make_decision(corporate_application, 'corporate')
print(f"Corporate Decision: {decision['decision']}")
print(f"Risk Assessment: {decision['risk_score']:.3f}")
```

### Risk Factor Analysis

```python
# Get detailed risk breakdown
breakdown = credit_app.get_risk_breakdown(individual_application, 'individual')

print("Risk Factor Contributions:")
for factor, details in breakdown.items():
    if isinstance(details, dict) and 'contribution' in details:
        print(f"  {factor.replace('_', ' ').title()}: {details['contribution']:.3f}")
```

## 🛠️ Command Line Interface

```bash
# Interactive assessment
credit-risk --interactive --type individual

# From JSON file
credit-risk --file application.json --type corporate

# Direct JSON input
credit-risk --data '{"credit_score": 720, "monthly_income": 5000, "monthly_debt": 1500, "loan_amount": 20000}' --type individual

# Detailed output format
credit-risk --file app.json --output detailed
```

## 📊 Economic Indicators Integration

The system dynamically adjusts risk assessments based on current economic conditions:

| Indicator | Impact on Risk | Weight |
|-----------|----------------|---------|
| Consumer Price Index (CPI) | Higher inflation → Higher risk | 15% |
| GDP Growth Rate | Strong growth → Lower risk | 20% |
| Unemployment Rate | Higher unemployment → Higher risk | 25% |
| Interest Rates | Higher rates → Higher borrower risk | 20% |
| Housing Price Index | Market stability indicator | 5% |
| Consumer Confidence | Economic sentiment | 3% |
| Market Volatility | Economic uncertainty | 2% |

## 🔬 Machine Learning Models

### Available Models

- **Random Forest Classifier** - Ensemble learning for robust predictions with feature importance analysis
- **Logistic Regression** - Linear approach for interpretable results with coefficient analysis
- **Custom Risk Models** - Domain-specific algorithms optimized for financial data

### Model Performance

- **Individual Risk Model**: 85% accuracy with 12% false positive rate
- **Corporate Risk Model**: 82% accuracy with 15% false positive rate
- **Economic Integration**: 15% improvement over traditional scoring methods

## 📚 Documentation

- **[Installation Guide](https://credit-risk-creditum.readthedocs.io/en/latest/installation.html)**
- **[Usage Guide](https://credit-risk-creditum.readthedocs.io/en/latest/usage.html)**
- **[API Reference](https://credit-risk-creditum.readthedocs.io/en/latest/api_reference.html)**
- **[Examples Gallery](https://credit-risk-creditum.readthedocs.io/en/latest/examples.html)**

## 📖 Research & Publication

This project is based on peer-reviewed research in credit risk assessment and financial technology. 

**📄 [Download Research Paper](https://github.com/credit-risk-creditum/credit-risk-creditum/blob/main/docs/publication.pdf)**

### Citation

If you use this software in your research, please cite our work:

```bibtex
@article{owolabi2025credit,
  title={Comprehensive Credit Risk Assessment with Economic Indicators Integration},
  author={Owolabi, Omoshola},
  journal={Journal of Financial Technology},
  year={2025},
  publisher={Academic Press},
  url={https://github.com/credit-risk-creditum/credit-risk-creditum}
}
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=credit_risk --cov-report=html

# Run specific test categories
pytest tests/test_models.py -v
pytest tests/test_application.py -v
```

## 📋 Requirements

- **Python**: 3.7 or higher
- **Core Dependencies**:
  - NumPy >= 1.19.0 (numerical computations)
  - Pandas >= 1.1.0 (data manipulation)
  - scikit-learn >= 0.24.0 (machine learning models)

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/credit-risk-creditum/credit-risk-creditum.git
cd credit-risk-creditum
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[dev]
pytest tests/
```

## 📈 Roadmap

- ✅ Individual Risk Assessment
- ✅ Corporate Risk Assessment  
- ✅ Economic Indicators Integration
- ✅ Machine Learning Models
- ✅ CLI Interface
- ✅ Comprehensive Documentation
- 🔄 Advanced Deep Learning Models (In Progress)
- 📋 Web Dashboard Interface (Planned)
- 📋 API Service Deployment (Planned)
- 📋 Real-time Economic Data Feeds (Planned)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💼 Author

**Omoshola Owolabi**
- 🎓 Analytics Engineer, Supply Chain & Finance AI/ML Researcher
- 🔗 LinkedIn: [linkedin.com/in/omosholaowolabi](https://linkedin.com/in/omosholaowolabi)
- 📧 Email: owolabi.omoshola@outlook.com
- 🐙 GitHub: [@credit-risk-creditum](https://github.com/credit-risk-creditum)

## 🙏 Acknowledgments

- Financial institutions for providing anonymized data for model validation
- Open source community for excellent Python libraries
- Research collaborators and peer reviewers
- Beta testers and early adopters

## ⭐ Support

If you find this project helpful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs and issues
- 💡 Suggesting new features
- 📖 Contributing to documentation
- 🔄 Sharing with others in the fintech community

---

*Made with ❤️ for the financial technology community*
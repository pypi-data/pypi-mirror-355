"""
Example focused on corporate credit risk assessment.
"""

from credit_risk import CreditApplication
from credit_risk.models.risk_models import CorporateRiskModel
from credit_risk.utils.helpers import format_currency, format_percentage


def main():
    """Demonstrate corporate credit risk assessment."""
    print("Corporate Credit Risk Assessment Example")
    print("=" * 50)
    
    # Initialize application processor
    credit_app = CreditApplication()
    
    # Example corporate applications with different risk profiles
    companies = [
        {
            'name': 'TechStart Inc.',
            'data': {
                'annual_revenue': 500000,  # $500K revenue
                'net_income': 50000,  # $50K profit (10% margin)
                'loan_amount': 200000,  # $200K loan
                'years_in_business': 2,
                'employee_count': 8,
                'industry': 'technology',
                'assets': 300000,
                'liabilities': 150000,
                'business_credit_score': 650,
                'management_experience': 5,
            }
        },
        {
            'name': 'Established Manufacturing Co.',
            'data': {
                'annual_revenue': 10000000,  # $10M revenue
                'net_income': 1500000,  # $1.5M profit (15% margin)
                'loan_amount': 2000000,  # $2M loan
                'years_in_business': 15,
                'employee_count': 120,
                'industry': 'manufacturing',
                'assets': 8000000,
                'liabilities': 3000000,
                'business_credit_score': 750,
                'management_experience': 20,
            }
        },
        {
            'name': 'Struggling Retail Store',
            'data': {
                'annual_revenue': 800000,  # $800K revenue
                'net_income': -50000,  # $50K loss
                'loan_amount': 300000,  # $300K loan
                'years_in_business': 5,
                'employee_count': 15,
                'industry': 'retail',
                'assets': 400000,
                'liabilities': 500000,  # More debt than assets
                'business_credit_score': 580,
                'management_experience': 8,
            }
        }
    ]
    
    # Process each application
    for i, company in enumerate(companies, 1):
        print(f"\n{i}. Analyzing {company['name']}")
        print("-" * 40)
        
        try:
            # Get decision
            decision = credit_app.make_decision(company['data'], 'corporate')
            print_corporate_decision(decision, company['name'])
            
            # Get detailed breakdown
            breakdown = credit_app.get_risk_breakdown(company['data'], 'corporate')
            print_corporate_breakdown(company['data'], breakdown)
            
        except Exception as e:
            print(f"Error processing {company['name']}: {e}")
    
    # Demonstrate risk model directly
    print(f"\n4. Direct Risk Model Analysis")
    print("-" * 40)
    
    corporate_model = CorporateRiskModel()
    
    # Test different scenarios
    scenarios = [
        {
            'name': 'High Revenue, Low Profit',
            'data': {
                'annual_revenue': 5000000,
                'net_income': 100000,  # 2% margin
                'assets': 3000000,
                'liabilities': 2800000,  # High debt
                'years_in_business': 10,
                'employee_count': 50,
                'industry': 'retail',
                'business_credit_score': 600,
                'management_experience': 12,
            }
        },
        {
            'name': 'Growing Tech Company',
            'data': {
                'annual_revenue': 2000000,
                'net_income': 400000,  # 20% margin
                'assets': 1500000,
                'liabilities': 500000,  # Low debt
                'years_in_business': 4,
                'employee_count': 30,
                'industry': 'technology',
                'business_credit_score': 720,
                'management_experience': 8,
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario['name']}")
        risk_score = corporate_model.calculate_risk_score(scenario['data'])
        print(f"Risk Score: {risk_score:.3f}")
        
        breakdown = corporate_model.get_risk_breakdown(scenario['data'])
        for factor, details in breakdown.items():
            if isinstance(details, dict) and 'contribution' in details:
                print(f"  {factor}: {details['contribution']:.3f}")


def print_corporate_decision(decision, company_name):
    """Print corporate credit decision."""
    print(f"Decision for {company_name}:")
    print(f"  Status: {decision['decision']}")
    print(f"  Reason: {decision['reason']}")
    
    if 'risk_score' in decision and decision['risk_score'] is not None:
        print(f"  Risk Score: {decision['risk_score']:.3f}")
        
        # Risk grade
        risk_score = decision['risk_score']
        if risk_score < 0.3:
            grade = "Low Risk (A)"
        elif risk_score < 0.5:
            grade = "Medium Risk (B)"
        elif risk_score < 0.7:
            grade = "High Risk (C)"
        else:
            grade = "Very High Risk (D)"
        
        print(f"  Risk Grade: {grade}")
    
    if 'recommended_amount' in decision and decision['recommended_amount']:
        print(f"  Approved Amount: {format_currency(decision['recommended_amount'])}")
    
    if 'interest_rate' in decision and decision['interest_rate']:
        print(f"  Interest Rate: {format_percentage(decision['interest_rate'])}")


def print_corporate_breakdown(data, breakdown):
    """Print detailed corporate risk breakdown."""
    print("  Financial Analysis:")
    
    # Calculate key ratios
    annual_revenue = data.get('annual_revenue', 0)
    net_income = data.get('net_income', 0)
    assets = data.get('assets', 0)
    liabilities = data.get('liabilities', 0)
    
    if annual_revenue > 0:
        profit_margin = (net_income / annual_revenue) * 100
        print(f"    Profit Margin: {profit_margin:.1f}%")
    
    if assets > 0:
        debt_ratio = (liabilities / assets) * 100
        print(f"    Debt-to-Asset Ratio: {debt_ratio:.1f}%")
    
    net_worth = assets - liabilities
    print(f"    Net Worth: {format_currency(net_worth)}")
    
    print("  Risk Factor Contributions:")
    for factor, details in breakdown.items():
        if isinstance(details, dict) and 'contribution' in details:
            contribution = details['contribution']
            weight = details.get('weight', 0)
            factor_name = factor.replace('_', ' ').title()
            print(f"    {factor_name}: {contribution:.3f} (weight: {weight:.2f})")


if __name__ == "__main__":
    main()

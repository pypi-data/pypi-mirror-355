"""
Example usage of the credit-risk-creditum package.
Run this after installing: pip install credit-risk-creditum
"""

from credit_risk import CreditApplication, EconomicIndicators
from credit_risk.utils.helpers import format_currency, format_percentage


def main():
    """Demonstrate basic usage of the credit risk assessment system."""
    print("Credit Risk Assessment Example")
    print("=" * 50)
    
    # Initialize application processor
    credit_app = CreditApplication(min_credit_score=600, max_dti=0.43)
    
    # Update economic indicators
    print("\n1. Updating Economic Indicators...")
    economic_data = {
        'cpi': 0.025,  # 2.5% inflation
        'gdp_growth': 0.03,  # 3% GDP growth
        'unemployment_rate': 0.045,  # 4.5% unemployment
        'interest_rate': 0.05,  # 5% interest rate
        'inflation_rate': 0.025,  # 2.5% inflation
    }
    credit_app.update_economic_indicators(economic_data)
    print("Economic indicators updated successfully")
    
    # Example 1: Individual application (should be approved)
    print("\n2. Processing Individual Application (Good Credit)...")
    individual_application = {
        'credit_score': 720,
        'monthly_income': 5000,
        'monthly_debt': 1500,
        'loan_amount': 20000,
        'loan_purpose': 'home_improvement',
        'employment_length': 5,
        'annual_income': 60000,
    }
    
    try:
        decision = credit_app.make_decision(individual_application, 'individual')
        print_decision(decision, "Individual Application")
        
        # Get detailed risk breakdown
        breakdown = credit_app.get_risk_breakdown(individual_application, 'individual')
        print_risk_breakdown(breakdown)
        
    except Exception as e:
        print(f"Error processing individual application: {e}")
    
    # Example 2: Individual application (poor credit)
    print("\n3. Processing Individual Application (Poor Credit)...")
    poor_credit_application = {
        'credit_score': 550,
        'monthly_income': 3000,
        'monthly_debt': 2000,
        'loan_amount': 15000,
        'loan_purpose': 'debt_consolidation',
        'employment_length': 1,
        'annual_income': 36000,
    }
    
    try:
        decision = credit_app.make_decision(poor_credit_application, 'individual')
        print_decision(decision, "Poor Credit Individual")
        
    except Exception as e:
        print(f"Error processing poor credit application: {e}")
    
    # Example 3: Corporate application
    print("\n4. Processing Corporate Application...")
    corporate_application = {
        'annual_revenue': 2000000,  # $2M revenue
        'net_income': 300000,  # $300K profit
        'loan_amount': 500000,  # $500K loan
        'years_in_business': 8,
        'employee_count': 25,
        'industry': 'technology',
        'assets': 1500000,
        'liabilities': 800000,
        'business_credit_score': 680,
        'management_experience': 12,
    }
    
    try:
        decision = credit_app.make_decision(corporate_application, 'corporate')
        print_decision(decision, "Corporate Application")
        
        # Get detailed risk breakdown
        breakdown = credit_app.get_risk_breakdown(corporate_application, 'corporate')
        print_risk_breakdown(breakdown)
        
    except Exception as e:
        print(f"Error processing corporate application: {e}")
    
    # Example 4: Get economic summary
    print("\n5. Economic Conditions Summary...")
    economic_summary = credit_app.economic_indicators.get_economic_summary()
    print(f"Economic Outlook: {economic_summary['outlook']}")
    print(f"Risk Adjustment: {economic_summary['risk_adjustment']:+.3f}")
    print(f"Description: {economic_summary['description']}")
    
    # Example 5: Model performance
    print("\n6. Model Performance Metrics...")
    performance = credit_app.get_model_performance()
    print(f"Individual Model Version: {performance['individual_model']['model_version']}")
    print(f"Corporate Model Version: {performance['corporate_model']['model_version']}")
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")


def print_decision(decision, title):
    """Print credit decision in formatted way."""
    print(f"\n{title} Decision:")
    print(f"  Status: {decision['decision']}")
    print(f"  Reason: {decision['reason']}")
    
    if 'risk_score' in decision and decision['risk_score'] is not None:
        print(f"  Risk Score: {decision['risk_score']:.3f}")
    
    if 'recommended_amount' in decision and decision['recommended_amount']:
        print(f"  Approved Amount: {format_currency(decision['recommended_amount'])}")
    
    if 'interest_rate' in decision and decision['interest_rate']:
        print(f"  Interest Rate: {format_percentage(decision['interest_rate'])}")


def print_risk_breakdown(breakdown):
    """Print risk breakdown in formatted way."""
    print("\n  Risk Factor Breakdown:")
    
    total_risk = breakdown.get('total_risk_score', 0)
    print(f"    Total Risk Score: {total_risk:.3f}")
    
    for factor, details in breakdown.items():
        if isinstance(details, dict) and 'contribution' in details:
            contribution = details['contribution']
            weight = details.get('weight', 0)
            print(f"    {factor.replace('_', ' ').title()}: {contribution:.3f} (weight: {weight:.2f})")


if __name__ == "__main__":
    main()

"""Command line interface for credit risk assessment."""

import argparse
import json
import sys
from typing import Dict, Any
from .core.application import CreditApplication
from .utils.validators import validate_application


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Credit Risk Assessment CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  credit-risk --file application.json --type individual
  credit-risk --interactive --type corporate
  credit-risk --data '{"credit_score": 720, "monthly_income": 5000}' --type individual
        """
    )
    
    parser.add_argument(
        '--file', '-f',
        help='JSON file containing application data'
    )
    
    parser.add_argument(
        '--data', '-d',
        help='JSON string containing application data'
    )
    
    parser.add_argument(
        '--type', '-t',
        choices=['individual', 'corporate'],
        default='individual',
        help='Application type (default: individual)'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive mode'
    )
    
    parser.add_argument(
        '--output', '-o',
        choices=['json', 'text', 'detailed'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        # Get application data
        if args.interactive:
            data = get_interactive_input(args.type)
        elif args.file:
            with open(args.file, 'r') as f:
                data = json.load(f)
        elif args.data:
            data = json.loads(args.data)
        else:
            parser.print_help()
            sys.exit(1)
        
        # Process application
        credit_app = CreditApplication()
        result = credit_app.make_decision(data, args.type)
        
        # Output result
        if args.output == 'json':
            print(json.dumps(result, indent=2))
        elif args.output == 'detailed':
            print_detailed_result(result, data, args.type, credit_app)
        else:
            print_text_result(result)
        
        # Exit with appropriate code
        sys.exit(0 if result['decision'] in ['APPROVED', 'CONDITIONAL'] else 1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def get_interactive_input(app_type: str) -> Dict[str, Any]:
    """Get application data interactively."""
    print(f"Credit Risk Assessment - {app_type.title()} Application")
    print("-" * 50)
    
    data = {}
    
    if app_type == 'individual':
        data['credit_score'] = int(input("Credit Score (300-850): "))
        data['monthly_income'] = float(input("Monthly Income ($): "))
        data['monthly_debt'] = float(input("Monthly Debt Payments ($): "))
        data['loan_amount'] = float(input("Requested Loan Amount ($): "))
        data['employment_length'] = int(input("Employment Length (years): "))
        
        loan_purpose = input("Loan Purpose (home_improvement/auto/debt_consolidation/business/personal): ")
        data['loan_purpose'] = loan_purpose or 'personal'
        
    else:  # corporate
        data['annual_revenue'] = float(input("Annual Revenue ($): "))
        data['loan_amount'] = float(input("Requested Loan Amount ($): "))
        data['years_in_business'] = int(input("Years in Business: "))
        data['employee_count'] = int(input("Number of Employees: "))
        
        industry = input("Industry (technology/healthcare/finance/manufacturing/retail/other): ")
        data['industry'] = industry or 'other'
        
        # Optional fields
        try:
            data['assets'] = float(input("Total Assets ($) [optional]: ") or 0)
            data['liabilities'] = float(input("Total Liabilities ($) [optional]: ") or 0)
            data['net_income'] = float(input("Net Income ($) [optional]: ") or 0)
        except ValueError:
            pass
    
    return data


def print_text_result(result: Dict[str, Any]) -> None:
    """Print result in text format."""
    status = result['decision']
    
    print(f"\nCredit Decision: {status}")
    print(f"Reason: {result['reason']}")
    
    if 'risk_score' in result and result['risk_score'] is not None:
        print(f"Risk Score: {result['risk_score']:.3f}")
    
    if 'recommended_amount' in result:
        print(f"Recommended Amount: ${result['recommended_amount']:,.2f}")
    
    if 'interest_rate' in result:
        print(f"Interest Rate: {result['interest_rate']:.2%}")


def print_detailed_result(
    result: Dict[str, Any], 
    data: Dict[str, Any], 
    app_type: str,
    credit_app: CreditApplication
) -> None:
    """Print detailed result."""
    print(f"\n{'='*60}")
    print(f"CREDIT RISK ASSESSMENT REPORT - {app_type.upper()}")
    print(f"{'='*60}")
    
    print(f"\nAPPLICATION SUMMARY:")
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")
    print(f"Timestamp: {result['timestamp']}")
    
    if 'risk_score' in result and result['risk_score'] is not None:
        print(f"\nRISK ANALYSIS:")
        print(f"Final Risk Score: {result['risk_score']:.3f}")
        
        if 'base_risk_score' in result:
            print(f"Base Risk Score: {result['base_risk_score']:.3f}")
        
        if 'economic_adjustment' in result:
            print(f"Economic Adjustment: {result['economic_adjustment']:+.3f}")
    
    if result['decision'] in ['APPROVED', 'CONDITIONAL']:
        print(f"\nLOAN TERMS:")
        if 'recommended_amount' in result:
            print(f"Approved Amount: ${result['recommended_amount']:,.2f}")
        if 'interest_rate' in result:
            print(f"Interest Rate: {result['interest_rate']:.2%}")
    
    # Get risk breakdown
    try:
        breakdown = credit_app.get_risk_breakdown(data, app_type)
        print(f"\nRISK BREAKDOWN:")
        for factor, details in breakdown.items():
            if isinstance(details, dict) and 'contribution' in details:
                print(f"  {factor}: {details['contribution']:.3f} (weight: {details['weight']:.2f})")
    except Exception:
        pass  # Skip if breakdown fails
    
    print(f"\n{'='*60}")


if __name__ == '__main__':
    main()

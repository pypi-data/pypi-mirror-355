Examples
========

This section provides comprehensive examples of using the Credit Risk Creditum package.

Individual Applications
-----------------------

Basic Individual Assessment
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../examples/example_usage.py
   :language: python
   :lines: 1-30

Corporate Applications
----------------------

Corporate Risk Assessment
~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../examples/corporate_example.py
   :language: python
   :lines: 1-40

Command Line Interface
----------------------

The package includes a command-line interface for quick assessments:

.. code-block:: bash

   # Interactive mode
   credit-risk --interactive --type individual
   
   # From JSON file
   credit-risk --file application.json --type corporate
   
   # Direct JSON input
   credit-risk --data '{"credit_score": 720, "monthly_income": 5000}' --type individual

Advanced Usage
--------------

Economic Indicators Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from credit_risk import CreditApplication
   
   app = CreditApplication()
   
   # Update economic conditions
   economic_data = {
       'cpi': 0.025,
       'gdp_growth': 0.03,
       'unemployment_rate': 0.045,
       'interest_rate': 0.05,
   }
   
   app.update_economic_indicators(economic_data)
   
   # Get economic summary
   summary = app.economic_indicators.get_economic_summary()
   print(f"Economic outlook: {summary['outlook']}")

Risk Breakdown Analysis
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get detailed risk factor breakdown
   breakdown = app.get_risk_breakdown(application_data, 'individual')
   
   for factor, details in breakdown.items():
       if isinstance(details, dict) and 'contribution' in details:
           print(f"{factor}: {details['contribution']:.3f}")

Credit Risk Creditum Documentation
==================================

A comprehensive credit risk assessment system that evaluates both individual and corporate credit applications.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   api_reference
   examples
   publication

Features
--------

* Individual credit risk assessment
* Corporate credit risk assessment  
* Economic indicators integration
* Machine learning model integration
* Configurable risk thresholds and weights

Quick Start
-----------

.. code-block:: python

   from credit_risk import CreditApplication
   
   app = CreditApplication()
   result = app.make_decision({
       'credit_score': 720,
       'monthly_income': 5000,
       'monthly_debt': 1500,
       'loan_amount': 20000
   }, 'individual')
   
   print(f"Decision: {result['decision']}")

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

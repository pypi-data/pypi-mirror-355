# Installation Guide

## Requirements

- Python 3.7 or higher
- pip (Python package installer)

## Installation from PyPI

The easiest way to install credit-risk-creditum is using pip:

```bash
pip install credit-risk-creditum
```

## Installation from Source

If you want to install from source or contribute to the project:

1. Clone the repository:

```bash
git clone https://github.com/credit-risk-creditum.git
cd credit-risk-creditum
```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:

```bash
pip install -e .
```

## Development Installation

For development work, install with development dependencies:

```bash
pip install -e .[dev]
```

This includes testing tools, code formatting, and documentation tools.

## Verification

Verify your installation by running:

```bash
python -c "from credit_risk import CreditApplication; print('Installation successful!')"
```

Or run the example:

```bash
python -m credit_risk.examples.example_usage
```

## Dependencies

The package automatically installs these dependencies:

- numpy >= 1.19.0
- pandas >= 1.1.0
- scikit-learn >= 0.24.0
- typing-extensions >= 3.7.4 (for Python < 3.8)

## Troubleshooting

### Import Errors

If you encounter import errors after installation:

- Make sure you're in the correct Python environment
- Verify the installation: `pip show credit-risk-creditum`
- Try reinstalling: `pip uninstall credit-risk-creditum && pip install credit-risk-creditum`

### Permission Errors

If you get permission errors during installation:

- Use a virtual environment (recommended)
- Or install with user flag: `pip install --user credit-risk-creditum`

### Version Conflicts

If you have dependency conflicts:

- Create a fresh virtual environment
- Or use: `pip install credit-risk-creditum --force-reinstall`
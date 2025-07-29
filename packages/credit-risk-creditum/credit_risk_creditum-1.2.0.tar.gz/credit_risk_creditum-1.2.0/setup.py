from setuptools import setup, find_packages
import os

def read_long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    try:
        with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "A comprehensive credit risk assessment system"

def read_requirements():
    here = os.path.abspath(os.path.dirname(__file__))
    try:
        with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return [
            "numpy>=1.19.0",
            "pandas>=1.1.0",
            "scikit-learn>=0.24.0"
        ]

setup(
    name="credit-risk-creditum",
    version="1.2.0",
    author="Omoshola Owolabi",
    author_email="owolabi.omoshola@outlook.com",
    description="A comprehensive credit risk assessment system",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/credit-risk-creditum",
    project_urls={
        "Bug Tracker": "https://github.com/credit-risk-creditum/issues",
        "Documentation": "https://github.com/credit-risk-creditum/docs",
        "Source Code": "https://github.com/credit-risk-creditum",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="credit-risk finance machine-learning risk-assessment banking fintech",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "twine>=3.0",
            "build>=0.7.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "credit-risk=credit_risk.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
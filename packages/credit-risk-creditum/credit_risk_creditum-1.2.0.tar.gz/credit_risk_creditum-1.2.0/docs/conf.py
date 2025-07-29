import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Credit Risk Creditum'
copyright = '2025, Omoshola Owolabi'
author = 'Omoshola Owolabi'
release = '0.1.1'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx_rtd_theme',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

source_suffix = {
    '.rst': None,
    '.md': 'myst_parser',
}

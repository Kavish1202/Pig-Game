# -- Project information -----------------------------------------------------
project = 'Pig Game'
copyright = '2025'
author = 'Shahzaib Khan'
release = '1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',     # Generate docs from docstrings
    'sphinx.ext.napoleon',    # Support for Google/NumPy docstrings
    'sphinx.ext.viewcode'     # Add “View Source” links
]

# Add your src path so autodoc can import your code
import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))

# -- Options for HTML output -------------------------------------------------
html_theme = 'alabaster'
html_static_path = ['_static']

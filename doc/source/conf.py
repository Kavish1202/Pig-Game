project = 'Pig Game'
copyright = '2025'
author = 'Your Name'
release = '1.0'

# Extensions (Napoleon is built-in, so use 'sphinx.ext.napoleon')
extensions = [
    'sphinx.ext.autodoc',      # Auto-generate from docstrings
    'sphinx.ext.napoleon',     # Built-in support for Google/NumPy docstrings
    'sphinx.ext.viewcode'      # Show source code links
]

# Add your source path (adjust if needed)
import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))

# HTML theme and static files
html_theme = 'alabaster'
html_static_path = ['_static']
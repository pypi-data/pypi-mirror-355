# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add your source code to the path so Sphinx can find your modules
sys.path.insert(0, os.path.abspath('../../src'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'gnarly'
copyright = '2025, K. LeBryce'
author = 'K. LeBryce'
release = '0.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      # Automatically generate docs from docstrings
    'sphinx.ext.viewcode',     # Add [source] links to documentation
    'sphinx.ext.napoleon',     # Support for Google and NumPy style docstrings
    'sphinx.ext.intersphinx',  # Link to other project's documentation
    'myst_parser',             # MyST Markdown parser
    'sphinx_design'
]

# MyST parser configuration
myst_enable_extensions = [
    "colon_fence",     # ::: fenced code blocks
    "deflist",         # Definition lists
    "html_admonition", # HTML-style admonitions
    "html_image",      # HTML images with attributes
    "replacements",    # Text replacements like (c) -> ©
    "smartquotes",     # Smart quotes
    "substitution",    # Variable substitutions
    "tasklist",        # GitHub-style task lists
]

# Templates path
templates_path = ['_templates']

# Files to exclude from processing
exclude_patterns = []

# Source file suffixes and their parsers
source_suffix = {
    '.txt': 'restructuredtext',
    '.rst': 'restructuredtext',
    '.md': 'markdown',
    '.mdx': 'markdown'
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------

# Autodoc configuration
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'private-members': False,
    'special-members': False,
}

# Napoleon configuration (for Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# Intersphinx mapping (links to other documentation)
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

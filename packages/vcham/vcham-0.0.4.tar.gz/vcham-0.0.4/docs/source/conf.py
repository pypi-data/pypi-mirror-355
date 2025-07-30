import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PyVCHAM'
copyright = '2025, Emilio Rodríguez Cuenca'
author = 'Emilio Rodríguez Cuenca'
release = "0.0.3"
# import vcham
# release = vcham.__version__
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      # Generate docs from docstrings
    'sphinx.ext.napoleon',     # Support Google/NumPy docstrings
    'sphinx.ext.viewcode',     # Add links to source code
    'sphinx.ext.autosummary',  # Create summary tables
    'nbsphinx',                # Support Jupyter Notebooks
]

autodoc_typehints = 'description'
templates_path = ['_templates']
exclude_patterns = []

# nbsphinx_execute = 'always'  # Options: 'always', 'never', 'auto'
nbsphinx_execute = 'never'
# nbsphinx_timeout = 300  # 5 minutes



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

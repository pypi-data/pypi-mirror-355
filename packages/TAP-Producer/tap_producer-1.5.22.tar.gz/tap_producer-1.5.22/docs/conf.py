# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from importlib.metadata import version as _version

project = 'TAP-Producer'
copyright = '2024, Eden Ross Duff MSc'
author = 'Eden Ross Duff MSc'
release = '.'.join(_version('TAP-Producer').split('.')[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.duration',
    'sphinx.ext.extlinks',
    'sphinx.ext.githubpages',
    'sphinx.ext.ifconfig',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx_design',
    'sphinx_last_updated_by_git',
    'sphinx_sitemap',
    'sphinxawesome_theme.highlighting',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
today_fmt = '%d-%b-%Y'
python_display_short_literal_types = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_extra_path = ['robots.txt']
html_static_path = ['_static']
html_theme = 'sphinxawesome_theme'
html_css_files = ['css/custom.css']
html_logo = 'assets/TAP-Producer-logo.png'
html_context = {'mode': 'production'}
# Set canonical URL from the Read the Docs Domain
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")

# Tell Jinja2 templates the build is running on Read the Docs
if os.environ.get("READTHEDOCS", "") == "True":
    html_context["READTHEDOCS"] = True

latex_elements = {'fncychap': r'\usepackage[Sonny]{fncychap}'}
latex_show_pagerefs = True
latex_show_urls = 'inline'
latex_logo = html_logo
autodoc_preserve_defaults = True
autodoc_typehints_format = 'short'
myst_enable_extensions = ['colon_fence']

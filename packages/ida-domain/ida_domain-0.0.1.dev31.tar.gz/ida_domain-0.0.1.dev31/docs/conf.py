# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from pathlib import Path

# Add the project root to the Python path so Sphinx can find the ida_domain package
sys.path.insert(0, os.path.abspath('..'))

# Add extensions directory to Python path
sys.path.insert(0, str(Path(__file__).parent / '_extensions'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'IDA Domain API'
copyright = '2025, Hex-Rays SA'
author = 'Hex-Rays SA'
release = '1.0.0'
version = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.graphviz',
    # Add the inject_examples extension to the extensions list
    'inject_examples',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
autodoc_mock_imports = [
    'idapro',
    'ida_allins',
    'ida_auto',
    'ida_bitrange',
    'ida_bytes',
    'ida_dbg',
    'ida_dirtree',
    'ida_diskio',
    'ida_entry',
    'ida_enum',
    'ida_expr',
    'ida_fixup',
    'ida_fpro',
    'ida_frame',
    'ida_funcs',
    'ida_gdl',
    'ida_graph',
    'ida_hexrays',
    'ida_ida',
    'ida_idaapi',
    'ida_idc',
    'ida_idd',
    'ida_idp',
    'ida_ieee',
    'ida_kernwin',
    'ida_libfuncs',
    'ida_lines',
    'ida_loader',
    'ida_merge',
    'ida_mergemod',
    'ida_moves',
    'ida_nalt',
    'ida_name',
    'ida_netnode',
    'ida_offset',
    'ida_pro',
    'ida_problems',
    'ida_range',
    'ida_regfinder',
    'ida_registry',
    'ida_search',
    'ida_segment',
    'ida_segregs',
    'ida_srclang',
    'ida_strlist',
    'ida_tryblks',
    'ida_typeinf',
    'ida_ua',
    'ida_undo',
    'ida_xref',
    'idadex',
]

language = 'en'

# -- Autodoc configuration --------------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
}

# -- Autosummary settings ---------------------------------------------------
autosummary_generate = True
autosummary_imported_members = True

# -- Napoleon settings -------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# -- Intersphinx mapping -----------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Theme options
html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
}

# Custom CSS
html_css_files = [
    'custom.css',
]

# Project logo
html_logo = 'themes/hex-rays-theme/images/ida_domain.png'

# Favicon
html_favicon = 'themes/hex-rays-theme/images/ida_domain.png'

inheritance_node_attrs = dict(
    fontsize=16,
    height=0.75,
    width=2.75,
)

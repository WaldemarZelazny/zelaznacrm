# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add project root and apps/ to path
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../apps"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Mock heavy dependencies to allow autodoc to import modules
autodoc_mock_imports = [
    "django",
    "crispy_forms",
    "crispy_bootstrap5",
    "environ",
    "weasyprint",
    "openpyxl",
    "requests",
    "psycopg2",
    "debug_toolbar",
]

# -- Project information -----------------------------------------------------

project = "ZelaznaCRM"
copyright = "2026, Waldemar Zelazny"
author = "Waldemar Zelazny"

version = "1.0"
release = "1.0"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# autodoc settings
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_member_order = "bysource"

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

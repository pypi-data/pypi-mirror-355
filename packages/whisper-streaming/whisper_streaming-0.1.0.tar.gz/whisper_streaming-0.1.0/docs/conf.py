# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import sys
from pathlib import Path

PROJECT_PATH = Path().absolute().parent
SRC_PATH = PROJECT_PATH / "src"

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "whisper-streaming"
copyright = "2025-%Y, Niklas Kaaf <nkaaf@protonmail.com>"
author = "Niklas Kaaf"
release = (PROJECT_PATH / "VERSION").read_text().strip()

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.apidoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.napoleon",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "ctranslate2": ("https://opennmt.net/CTranslate2", None),
    "websockets": ("https://websockets.readthedocs.io/en/stable/", None),
}

# Modify Path for autodoc to find the module to document
sys.path.insert(0, str(SRC_PATH.resolve()))
apidoc_modules = [
    {
        "path": SRC_PATH / project.lower(),
        "destination": "apidoc",
    },
]

# noinspection PyUnresolvedReferences
if "Internal" in tags:
    apidoc_modules[0]["include_private"] = True
    todo_include_todos = True

templates_path = ["_templates"]
exclude_patterns = []

napoleon_google_docstring = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

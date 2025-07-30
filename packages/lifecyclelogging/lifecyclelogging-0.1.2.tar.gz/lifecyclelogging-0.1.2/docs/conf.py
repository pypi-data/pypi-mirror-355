import os

project = "LifecycleLogging"
author = "Jon Bogaty"
copyright_notice = f"2025, {author}"
version = "0.1.2"

extensions = [
    "autodoc2",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "myst_parser",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Default role
default_role = "py:obj"

# HTML output settings
html_theme = "sphinxawesome_theme"
html_static_path = ["_static"]
html_baseurl = "https://jbcom.github.io/lifecyclelogging/"

html_context = {
    "display_github": True,
    "github_user": "jbcom",
    "github_repo": "lifecyclelogging",
    "github_version": "main",
}

html_logo = "_static/logo.png"

html_permalinks_icon = "<span>⚓</span>"

autodoc2_render_plugin = "myst"

autodoc2_packages = [
    {"path": "../src/lifecyclelogging", "auto_mode": True, "module": "lifecyclelogging"}
]

# Add annotation replacements for common type hints
autodoc2_replace_annotations = [
    ("typing.Literal", "Literal"),
    ("typing.TypeAlias", "TypeAlias"),
    ("typing_extensions.TypeAlias", "TypeAlias"),
]

# Override docstring parser for specific modules
autodoc2_docstring_parser_regexes = [
    (r"lifecyclelogging\.log_types", "rst"),  # Ensure RST parsing for type modules
]

# Include all docstrings, not just direct ones
autodoc2_docstrings = "all"

# Show class inheritance
autodoc2_class_inheritance = True

# Always show annotations
autodoc2_annotations = True

nitpick_ignore = [
    ("py:class", "lifecyclelogging.log_types.LogLevel"),
]

# Also add a regex pattern to catch any similar type references
nitpick_ignore_regex = [
    (r"py:class", r"lifecyclelogging\.log_types\..*"),
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

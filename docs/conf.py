"""Sphinx configuration for the AB SDK documentation."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

project = "AB SDK"
copyright = "2026, AnnexBrands"
author = "AnnexBrands"

# Read from package metadata rather than hand-maintained here: this was pinned
# at 0.1.12 while the package shipped 0.1.14.
try:
    release = _pkg_version("annex-abconnect")
except PackageNotFoundError:  # pragma: no cover - docs built without an install
    release = "0.0.0+unknown"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_favicon = "_static/favicon.ico"
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

autodoc_member_order = "bysource"
autodoc_typehints = "description"

# CI builds with -W (warning-as-error), so every remaining warning must be a
# real defect. Ambiguous Python cross-references are the one exception: many
# models legitimately share short field names (``date``, ``id``, ``name``), so
# a bare reference resolves to several py:attribute targets — e.g. ``date`` on
# QuoteRequestServiceInfo, WorkTimeLogRequest and OnHoldNoteDetails. That is
# inherent to mirroring the upstream swagger field names and is not fixable by
# editing docs; renaming domain fields to satisfy the doc builder would be the
# tail wagging the dog. Scoped to this one warning class so genuine problems
# (broken toctrees, missing references, bad syntax) still fail the build.
suppress_warnings = ["ref.python"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest", None),
}

myst_enable_extensions = [
    "colon_fence",
    "fieldlist",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

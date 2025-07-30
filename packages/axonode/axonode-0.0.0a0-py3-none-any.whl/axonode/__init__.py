"""
Axonode
=======

Graph-structured long-term memory layer for retrieval-augmented
LLM agents (work-in-progress).

This stub only exposes a version string today; real symbols will be
re-exported here as the public API firms up.
"""

from importlib.metadata import version as _version

__all__: list[str] = ["__version__"]

try:  # Runtime version comes from the installed wheel
    __version__: str = _version(__name__)
except Exception:                 # during editable install or CI
    __version__ = "0.0.0a0"       # keep in sync with pyproject.toml

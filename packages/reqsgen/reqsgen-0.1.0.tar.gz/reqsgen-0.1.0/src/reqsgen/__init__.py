"""
reqsgen - Generate requirements.txt from your Python imports

A zero-config, offline-only Python tool that scans your project's .py files
for external imports and generates a minimal, sorted requirements.txt.
"""

__version__ = "0.1.0"
__author__ = "Ritik Patil"
__email__ = "ritik.patil@example.com"

# Export main API functions
from .scanner import (
    find_imports,
    filter_stdlib,
    generate_requirements,
    get_installed_version
)

__all__ = [
    "find_imports",
    "filter_stdlib", 
    "generate_requirements",
    "get_installed_version"
]

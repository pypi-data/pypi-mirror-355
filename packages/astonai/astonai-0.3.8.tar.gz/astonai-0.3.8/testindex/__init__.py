"""
Deprecation shim for testindex package.

This module provides backward compatibility for the renamed package.
The 'testindex' package has been renamed to 'aston'.
"""

import warnings
import importlib
import sys

# Issue deprecation warning
warnings.warn(
    "⚠️  Package 'testindex' has been renamed to 'aston'. "
    "Please update your imports from 'testindex' to 'aston'. "
    "This compatibility shim will be removed in v0.5.0.",
    DeprecationWarning,
    stacklevel=2
)

# Redirect module access to aston
sys.modules[__name__] = importlib.import_module("aston") 
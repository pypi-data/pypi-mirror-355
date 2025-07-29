"""
Aston Suggestion Engine - Multi-Purpose Code Intelligence.

This package provides comprehensive suggestion functionality for:
- Test generation (pytest, unit tests, integration tests)
- UAT (User Acceptance Test) scenarios  
- Documentation suggestions (docstrings, README, comments)
- Code improvement suggestions
- Refactoring recommendations

Future-ready architecture for Aston's expanding suggestion surface.
"""

from .engine import SuggestionEngine
from .exceptions import SuggestionError

__all__ = ["SuggestionEngine", "SuggestionError"] 
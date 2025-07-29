"""
Suggestion Generators - Pluggable Intelligence Modules.

This package contains specialized generators for different types of suggestions:
- heuristic.py: AST-based pattern analysis for test generation
- llm.py: LLM-powered suggestion generation

Future generators:
- uat.py: User Acceptance Test scenario generation
- doc.py: Documentation and comment suggestions  
- refactor.py: Code improvement recommendations
- comment.py: Inline comment suggestions
"""

from .heuristic import HeuristicGenerator
from .llm import LLMGenerator

__all__ = ["HeuristicGenerator", "LLMGenerator"] 
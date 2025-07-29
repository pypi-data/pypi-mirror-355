"""Coverage analysis module.

This module provides functionality for analyzing test coverage.
"""

from aston.analysis.coverage.models import (
    CoverageModel,
    ModuleCoverageModel,
    CoverageGap,
)

# Skip problematic imports temporarily
# from aston.analysis.coverage.mapping import get_coverage_for_function, get_coverage_for_module
from aston.analysis.coverage.reports import generate_coverage_report
from aston.analysis.coverage.gap_detector import GapDetector
from aston.analysis.coverage.utils import SimpleNeo4jClient

__all__ = [
    "CoverageModel",
    "ModuleCoverageModel",
    "CoverageGap",
    # "get_coverage_for_function",
    # "get_coverage_for_module",
    "generate_coverage_report",
    "GapDetector",
    "SimpleNeo4jClient",
]

"""
Heuristic test generation based on AST analysis.
"""

import ast
import os
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from aston.core.logging import get_logger
from aston.core.path_resolution import PathResolver

logger = get_logger(__name__)


class HeuristicGenerator:
    """Generates test suggestions using heuristic rules based on AST analysis."""

    @staticmethod
    def generate_suggestions(node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test suggestions using heuristic rules.

        Args:
            node: Node dictionary

        Returns:
            List of test suggestions
        """
        suggestions = []

        try:
            # Get node information
            node_id = node.get("id", "")
            name = node.get("name", "")
            file_path = node.get("file_path", "")

            if not name or not file_path:
                logger.warning(f"Node missing name or file path: {node_id}")
                return []

            # Find and read source file
            found_path = SourceFileResolver.resolve_source_file(file_path)
            if not found_path:
                logger.warning(f"Source file not found for: {file_path}")
                return []

            # Read content
            try:
                with open(found_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                logger.debug(f"Error reading {found_path}: {e}")
                return []

            if not content:
                return []

            # Parse and analyze
            tree = ast.parse(content)
            node_ast = ASTNodeFinder.find_node_ast(tree, name)
            if not node_ast:
                logger.warning(f"Could not find AST for node: {name}")
                return []

            # Extract parameters and generate test cases
            params, type_hints = ParameterExtractor.extract_params_and_hints(node_ast)
            test_cases = TestCaseGenerator.generate_test_cases(name, params, type_hints)

            # Convert to suggestions
            for test_case in test_cases:
                test_name = f"test_{name}_{test_case['scenario']}"
                test_file = Path(file_path).name

                suggestion = {
                    "test_name": f"{test_file}::{test_name}",
                    "target_node": f"{file_path}::{name}",
                    "estimated_coverage_gain": CoverageEstimator.estimate_coverage_gain(node),
                    "skeleton": PytestSkeletonGenerator.generate_pytest_skeleton(test_name, test_case),
                    "description": test_case["description"],
                    "scenario": test_case["scenario"],
                    "llm": False,
                }
                suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.warning(f"Error generating heuristic suggestions: {e}")
            logger.debug(f"Error details: {traceback.format_exc()}")
            return []


class SourceFileResolver:
    """Handles robust source file resolution."""

    @staticmethod
    def resolve_source_file(file_path: str) -> Optional[Path]:
        """Robust file resolution with multiple fallback strategies."""
        if not file_path:
            return None

        # Handle mock paths in tests
        if file_path.startswith("/mock/"):
            return Path(file_path)

        resolver = PathResolver()

        # Strategy 1: Direct resolution
        try:
            resolved_path = resolver.to_absolute(file_path)
            if resolved_path.exists():
                return resolved_path
        except Exception:
            pass

        # Strategy 2: Repository-relative
        try:
            repo_root = resolver.repo_root()
            repo_relative = repo_root / file_path
            if repo_relative.exists():
                return repo_relative
        except Exception:
            pass

        # Strategy 3: Common patterns
        try:
            repo_root = resolver.repo_root()
            for pattern in ["src/", "lib/", "app/", "testindex/", ""]:
                candidate = repo_root / pattern / file_path
                if candidate.exists():
                    return candidate
        except Exception:
            pass

        return None


class ASTNodeFinder:
    """Finds AST nodes for functions and methods."""

    @staticmethod
    def find_node_ast(tree: ast.AST, name: str) -> Optional[ast.AST]:
        """Find AST node for function or method."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == name:
                    return node
            elif isinstance(node, ast.ClassDef):
                for subnode in node.body:
                    if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if subnode.name == name:
                            return subnode
        return None


class ParameterExtractor:
    """Extracts function parameters and type hints."""

    @staticmethod
    def extract_params_and_hints(node_ast: ast.AST) -> Tuple[List[str], Dict[str, str]]:
        """Extract function parameters and type hints."""
        if not isinstance(node_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return [], {}

        params = [arg.arg for arg in node_ast.args.args]
        type_hints = {}

        for arg in node_ast.args.args:
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    type_hints[arg.arg] = arg.annotation.id
                elif isinstance(arg.annotation, ast.Subscript):
                    type_hints[arg.arg] = "complex"
                else:
                    type_hints[arg.arg] = "unknown"

        return params, type_hints


class TestCaseGenerator:
    """Generates test cases based on parameter analysis."""

    @staticmethod
    def generate_test_cases(func_name: str, params: List[str], type_hints: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate test cases based on parameter types."""
        test_cases = []

        # Skip self/cls parameters
        if params and params[0] in ("self", "cls"):
            params = params[1:]

        # Basic test case if no parameters
        if not params:
            test_cases.append({
                "scenario": "basic",
                "params": {},
                "expected": "expected_result",
                "description": f"Basic test for {func_name}",
            })
            return test_cases

        # Generate test cases for each parameter
        for param in params:
            param_type = type_hints.get(param, "unknown")
            
            # Positive case
            test_cases.append({
                "scenario": f"{param}_positive",
                "params": {param: "valid_value"},
                "expected": "expected_result",
                "description": f"Test {func_name} with valid {param}",
            })
            
            # Edge cases based on type
            if param_type in ["int", "float", "Decimal"]:
                test_cases.extend([
                    {
                        "scenario": f"{param}_zero",
                        "params": {param: "0"},
                        "expected": "expected_result",
                        "description": f"Test {func_name} with zero {param}",
                    },
                    {
                        "scenario": f"{param}_negative",
                        "params": {param: "-1"},
                        "expected": "expected_result", 
                        "description": f"Test {func_name} with negative {param}",
                    }
                ])
            elif param_type in ["str", "String"]:
                test_cases.extend([
                    {
                        "scenario": f"{param}_empty",
                        "params": {param: '""'},
                        "expected": "expected_result",
                        "description": f"Test {func_name} with empty string {param}",
                    }
                ])
            elif param_type in ["List", "Array", "list"]:
                test_cases.extend([
                    {
                        "scenario": f"{param}_empty_list",
                        "params": {param: "[]"},
                        "expected": "expected_result",
                        "description": f"Test {func_name} with empty list {param}",
                    }
                ])

        return test_cases


class BoundaryCaseGenerator:
    """Generates boundary test cases for different parameter types."""

    @staticmethod
    def generate_boundary_cases(param_name: str, param_type: str) -> List[Dict]:
        """Generate boundary test cases for a parameter."""
        cases = []
        
        if param_type == "int":
            cases = [
                {"value": 0, "description": "Zero value"},
                {"value": -1, "description": "Negative value"},
                {"value": 1, "description": "Positive value"},
                {"value": 100, "description": "Large value"}
            ]
        elif param_type == "float":
            cases = [
                {"value": 0.0, "description": "Zero value"},
                {"value": -1.0, "description": "Negative value"},
                {"value": 1.0, "description": "Positive value"},
                {"value": 100.0, "description": "Large value"}
            ]
        elif param_type == "str":
            cases = [
                {"value": "", "description": "Empty string"},
                {"value": "x" * 100, "description": "Long string"},
                {"value": "test", "description": "Normal string"}
            ]
        elif param_type == "list":
            cases = [
                {"value": [], "description": "Empty list"},
                {"value": None, "description": "None value"},
                {"value": [1, 2, 3], "description": "Normal list"}
            ]
        else:
            cases = [
                {"value": None, "description": "None value"},
                {"value": "", "description": "Empty value"}
            ]
            
        return cases


class PytestSkeletonGenerator:
    """Generates pytest test skeletons."""

    @staticmethod
    def generate_pytest_skeleton(test_name: str, test_case: Dict[str, Any]) -> str:
        """Generate a pytest test skeleton."""
        description = test_case.get("description", "Basic test case")
        params = test_case.get("params", {})
        expected = test_case.get("expected", "expected_result")
        lines = [
            f"def {test_name}():",
            '    """',
            f"    {description}",
            '    """',
            "    # Arrange",
            ""
        ]
        for param_name, param_value in params.items():
            if isinstance(param_value, str):
                lines.append(f"    {param_name} = '{param_value}'")
            elif isinstance(param_value, (list, dict, bool, int, float)):
                lines.append(f"    {param_name} = {param_value}")
            else:
                lines.append(f"    {param_name} = {repr(param_value)}")
        lines.extend([
            "",
            "    # Act",
            "    result = # Call the function under test",
            "",
            "    # Assert",
            f"    expected = {repr(expected) if isinstance(expected, str) else expected}",
            f"    assert result == expected"
        ])
        return "\n".join(lines)


class CoverageEstimator:
    """Estimates test coverage gain for suggestions."""

    @staticmethod
    def estimate_coverage_gain(node: Dict[str, Any]) -> float:
        """Estimate coverage gain for a test suggestion.
        
        Returns a value between 0.0 and 1.0 representing the estimated
        coverage gain from implementing the test.
        """
        # Base coverage gain
        base_gain = 0.5
        
        # Adjust based on node properties
        if node.get("is_critical", False):
            base_gain += 0.2
            
        if node.get("complexity", 0) > 5:
            base_gain += 0.1
            
        if node.get("test_count", 0) == 0:
            base_gain += 0.2
            
        # Ensure value is between 0 and 1
        return min(max(base_gain, 0.0), 1.0) 
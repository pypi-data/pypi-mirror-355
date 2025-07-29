"""
LLM-based test generation - extracted from original test_suggest.py.
"""

from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any

from aston.core.logging import get_logger
from aston.core.path_resolution import PathResolver

logger = get_logger(__name__)


class LLMGenerator:
    """Generates test suggestions using LLM - extracted from original SuggestionEngine."""

    def __init__(self, model: str = "gpt-4o", budget: float = 0.03):
        """Initialize LLM generator.
        
        Args:
            model: LLM model to use
            budget: Maximum cost per suggestion in dollars
        """
        self.model = model
        self.budget = Decimal(str(budget))

    def generate_suggestions(self, node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test suggestions using LLM - extracted method.

        Args:
            node: Node dictionary

        Returns:
            List of test suggestions
        """
        try:
            # Check if OpenAI client is available
            try:
                from aston.llm.clients.openai_client import OpenAIClient
            except ImportError:
                logger.error(
                    "OpenAI client not available. Install with: pip install openai"
                )
                return []

            # Get node information
            node_id = node.get("id", "")
            name = node.get("name", "")
            file_path = node.get("file_path", "")

            if not name or not file_path:
                logger.warning(f"Node missing name or file path: {node_id}")
                return []

            # Read the file
            full_path = PathResolver.to_absolute(file_path)
            if not full_path.exists():
                logger.warning(f"File not found: {full_path}")
                return []

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Initialize client
            client = OpenAIClient(model=self.model, budget=self.budget)

            # Generate prompt
            prompt = self._generate_llm_prompt(node, name, file_path, content)

            # Call LLM
            suggestions = client.generate_test_suggestions(prompt, name, file_path)

            # Add LLM attribution
            for suggestion in suggestions:
                suggestion["llm"] = True
                suggestion["model"] = self.model

            return suggestions

        except Exception as e:
            logger.error(f"Failed to generate LLM suggestions: {e}")
            return []

    def _generate_llm_prompt(
        self, node: Dict[str, Any], name: str, file_path: str, content: str
    ) -> str:
        """Generate a prompt for the LLM - extracted method.

        Args:
            node: Node dictionary
            name: Function name
            file_path: File path
            content: File content

        Returns:
            Prompt string
        """
        return f"""
You are a test expert. Your task is to generate pytest test cases for the function named '{name}' in the file '{file_path}'.

Here's the file content:
```python
{content}
```

Focus on the function '{name}' and generate up to 3 high-quality test cases.
For each test case, provide:
1. A descriptive test name
2. A brief explanation of what the test verifies
3. A complete pytest function implementation with arrange-act-assert pattern

Prioritize test cases that would:
- Test edge cases and boundary conditions
- Maximize code coverage
- Verify error handling
- Test important business logic paths

Return each test case as a JSON object with the following structure:
{{
  "test_name": "test_function_name_scenario",
  "description": "Brief description of what this test verifies",
  "skeleton": "def test_name():\\n    # Arrange\\n    ...\\n    # Act\\n    ...\\n    # Assert\\n    ..."
}}

Return a list of these test case objects. Skip any explanatory text or comments.
""" 
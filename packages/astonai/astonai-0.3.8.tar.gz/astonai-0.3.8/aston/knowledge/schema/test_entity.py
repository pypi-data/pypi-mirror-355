"""Test entity schema interfaces."""
from pydantic import Field, ConfigDict
from typing import List, Dict, Optional, Any
from enum import Enum
from aston.knowledge.schema.base import Node, Property


class TestFramework(str, Enum):
    """Supported test frameworks."""

    PYTEST = "pytest"
    UNITTEST = "unittest"
    CUSTOM = "custom"


class TestEntity(Node):
    """Schema for test entities shared between pods."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Test function/method name")
    file_path: str = Field(..., description="File path relative to repo root")
    framework: TestFramework = Field(..., description="Test framework")
    line_start: int = Field(..., description="Starting line number")
    line_end: int = Field(..., description="Ending line number")
    fixtures: List[str] = Field(
        default_factory=list, description="Fixture dependencies"
    )
    test_cases: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, description="List of test cases for this entity"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="allow",
        json_schema_extra={
            "version": "0.1.0",
            "example": {
                "id": "test_auth_login_1",
                "name": "test_login_valid_credentials",
                "file_path": "tests/auth/test_login.py",
                "framework": "pytest",
                "line_start": 42,
                "line_end": 55,
                "fixtures": ["db_conn", "user_factory"],
            },
        },
    )

    @classmethod
    def get_property_definitions(cls) -> List[Property]:
        return []

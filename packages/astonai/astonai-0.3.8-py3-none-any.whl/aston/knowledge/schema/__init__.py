"""
Knowledge Graph schema module.

This module provides schema definitions for nodes and relationships in the Knowledge Graph.
"""

__version__ = "0.1.0"

from aston.knowledge.schema.base import Node, Relationship, SchemaItem
from aston.knowledge.schema.nodes import (
    NodeSchema,
    ImplementationNode,
    ModuleNode,
    FixtureNode,
)
from aston.knowledge.schema.relationships import (
    ContainsRelationship,
    CoverageRelationship,
    CallsRelationship,
    ImportsRelationship,
    UsesFixtureRelationship,
    InheritsFromRelationship,
    CoversPathRelationship,
)

__all__ = [
    "Node",
    "Relationship",
    "SchemaItem",
    "NodeSchema",
    "ImplementationNode",
    "ModuleNode",
    "FixtureNode",
    "ContainsRelationship",
    "CoverageRelationship",
    "CallsRelationship",
    "ImportsRelationship",
    "InheritsFromRelationship",
    "UsesFixtureRelationship",
    "CoversPathRelationship",
]

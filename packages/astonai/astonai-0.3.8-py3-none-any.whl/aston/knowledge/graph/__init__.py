"""
Graph database integration for the Knowledge Graph.

This module provides Neo4j integration for storing and retrieving 
knowledge graph nodes and relationships.
"""

__version__ = "0.1.0"

from aston.knowledge.graph.neo4j_client import Neo4jClient
from aston.knowledge.graph.relation_builder import RelationBuilder
from aston.knowledge.graph.batch_operations import BatchOperations

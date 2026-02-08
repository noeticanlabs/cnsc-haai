"""
GraphGML - Graph-based Graph Merkle Language

A graph-based representation for execution traces, proofs, and constraint systems.
Provides node and edge types, graph container, and builder utilities.

Modules:
    types: Node and edge type definitions
    core: Graph container and query operations
    builder: Builder pattern for graph construction
"""

from cnsc.haai.graphgml.types import (
    EdgeType,
    GraphNode,
    CommitNode,
    EmitNode,
    StateNode,
    CandidateNode,
    ConstraintSetNode,
    GateStackRunNode,
    GateResultNode,
    ProofBundleNode,
    MemoryReadNode,
    MemoryWriteNode,
    SolverCallNode,
    Node,
)

from cnsc.haai.graphgml.core import GraphGML, GraphQuery

from cnsc.haai.graphgml.builder import GraphBuilder, graph_builder, create_simple_trace

__all__ = [
    # Types
    "EdgeType",
    "GraphNode",
    "CommitNode",
    "EmitNode",
    "StateNode",
    "CandidateNode",
    "ConstraintSetNode",
    "GateStackRunNode",
    "GateResultNode",
    "ProofBundleNode",
    "MemoryReadNode",
    "MemoryWriteNode",
    "SolverCallNode",
    "Node",
    # Core
    "GraphGML",
    "GraphQuery",
    # Builder
    "GraphBuilder",
    "graph_builder",
    "create_simple_trace",
]

__version__ = "0.1.0"

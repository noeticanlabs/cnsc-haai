"""
Coherence NSC Hierarchical Abstraction AI (HAAI)

The world's first coherence-governed hierarchical abstraction AI system.
Integrates CGL governance, Noetica ecosystem languages, and coherence-based reasoning.
"""

__version__ = "0.1.0"
__author__ = "Coherence Framework Team"

from .core import CoherenceEngine, HierarchicalAbstraction
from .nsc import NSCProcessor, GLLLEncoder, GHLLProcessor, GMLMemory
from .agent import HAAIAgent, IntegratedHAAIAgent, create_integrated_haai_agent
from .governance import CGLGovernance

__all__ = [
    "CoherenceEngine",
    "HierarchicalAbstraction",
    "NSCProcessor",
    "GLLLEncoder",
    "GHLLProcessor",
    "GMLMemory",
    "HAAIAgent",
    "IntegratedHAAIAgent",
    "create_integrated_haai_agent",
    "CGLGovernance"
]
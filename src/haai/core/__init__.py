"""
Core coherence and hierarchical abstraction components.
"""

from .coherence import CoherenceEngine, CoherenceSignals, EnvelopeManager
from .abstraction import HierarchicalAbstraction, LevelManager, CrossLevelMap
from .residuals import ResidualCalculator, CoherenceFunctional
from .gates import GateSystem, RailSystem

__all__ = [
    "CoherenceEngine",
    "CoherenceSignals", 
    "EnvelopeManager",
    "HierarchicalAbstraction",
    "LevelManager",
    "CrossLevelMap",
    "ResidualCalculator",
    "CoherenceFunctional",
    "GateSystem",
    "RailSystem"
]
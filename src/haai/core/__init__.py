"""
Core coherence and hierarchical abstraction components.
"""

from .coherence import CoherenceEngine, CoherenceSignals, EnvelopeManager
from .abstraction import HierarchicalAbstraction, LevelManager, CrossLevelMaps
from .residuals import ResidualCalculator, CoherenceFunctional
from .gates import GateSystem, RailSystem

__all__ = [
    "CoherenceEngine",
    "CoherenceSignals", 
    "EnvelopeManager",
    "HierarchicalAbstraction",
    "LevelManager",
    "CrossLevelMaps",
    "ResidualCalculator",
    "CoherenceFunctional",
    "GateSystem",
    "RailSystem"
]
"""
HAAI Agent Implementation - Main agent that integrates all foundational components.

This module contains the core HAAI agent that combines:
- Agent lifecycle management and state persistence
- Reasoning engine with hierarchical abstraction
- Attention allocation system with optimization
- Learning and adaptation mechanisms
- Tool integration framework
"""

from .core import HAAIAgent, AgentState, AgentLifecycle, AgentCoordinator
from .reasoning import ReasoningEngine, ReasoningStep, AbstractionQuality, LevelSelector
from .attention import AttentionSystem, AttentionBudget, HierarchicalAttention
from .learning import LearningSystem, ReceiptBasedLearning, AbstractionOptimizer
from .tools import ToolFramework, ToolRegistry, ToolExecutor
from .integrated import IntegratedHAAIAgent, create_integrated_haai_agent

__all__ = [
    "HAAIAgent",
    "AgentState",
    "AgentLifecycle",
    "AgentCoordinator",
    "ReasoningEngine",
    "ReasoningStep",
    "AbstractionQuality",
    "LevelSelector",
    "AttentionSystem",
    "AttentionBudget",
    "HierarchicalAttention",
    "LearningSystem",
    "ReceiptBasedLearning",
    "AbstractionOptimizer",
    "ToolFramework",
    "ToolRegistry",
    "ToolExecutor",
    "IntegratedHAAIAgent",
    "create_integrated_haai_agent"
]
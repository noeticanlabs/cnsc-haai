"""
CNHAAI (Coherent Non-Hierarchical Artificial Intelligence)

A framework for implementing coherent reasoning systems with
abstraction layers, gate validation, and full auditability.
"""

__version__ = "1.0.0"
__author__ = "CNHAAI Team"

# Core components
from cnhaai.core.abstraction import Abstraction, AbstractionLayer, AbstractionType
from cnhaai.core.gates import (
    Gate,
    GateDecision,
    GateResult,
    GateType,
    GateManager,
    EvidenceSufficiencyGate,
    CoherenceCheckGate
)
from cnhaai.core.receipts import (
    Receipt,
    ReceiptContent,
    ReceiptDecision,
    ReceiptProvenance,
    ReceiptSignature,
    ReceiptStepType,
    ReceiptSystem
)
from cnhaai.core.phases import Phase, PhaseConfig, PhaseState, PhaseManager
from cnhaai.core.coherence import CoherenceBudget
from cnhaai.kernel.minimal import MinimalKernel, EpisodeResult

__all__ = [
    # Version
    "__version__",
    
    # Abstraction
    "Abstraction",
    "AbstractionLayer",
    "AbstractionType",
    
    # Gates
    "Gate",
    "GateDecision",
    "GateResult",
    "GateType",
    "GateManager",
    "EvidenceSufficiencyGate",
    "CoherenceCheckGate",
    
    # Receipts
    "Receipt",
    "ReceiptContent",
    "ReceiptDecision",
    "ReceiptProvenance",
    "ReceiptSignature",
    "ReceiptStepType",
    "ReceiptSystem",
    
    # Phases
    "Phase",
    "PhaseConfig",
    "PhaseState",
    "PhaseManager",
    
    # Coherence
    "CoherenceBudget",
    
    # Kernel
    "MinimalKernel",
    "EpisodeResult"
]

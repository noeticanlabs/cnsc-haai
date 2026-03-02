"""
CNHAAI (Coherent Non-Hierarchical Artificial Intelligence)

A framework for implementing coherent reasoning systems with
abstraction layers, gate validation, and full auditability.

DEPRECATED: This is the legacy namespace.
Please migrate to cnsc.haai for ATS/Governance components.
"""

import warnings

# Emit deprecation warning when this module is imported
warnings.warn(
    "cnhaai is deprecated. Use cnsc.haai for ATS/Governance components.",
    DeprecationWarning,
    stacklevel=2,
)

__version__ = "1.0.0"
__author__ = "CNHAAI Team"

# Core components - Redirect to cnsc.haai where equivalent exists

# Abstraction - no cnsc.haai equivalent, use legacy
from .core.abstraction import Abstraction, AbstractionLayer, AbstractionType

# Gates - redirect to cnsc.haai.nsc.gates
try:
    from cnsc.haai.nsc.gates import (
        Gate,
        GateDecision,
        GateResult,
        GateType,
        GateManager,
        EvidenceSufficiencyGate,
        CoherenceCheckGate,
    )
except ImportError:
    from .core.gates import (
        Gate,
        GateDecision,
        GateResult,
        GateType,
        GateManager,
        EvidenceSufficiencyGate,
        CoherenceCheckGate,
    )

# Receipts - redirect to cnsc.haai.gml.receipts
try:
    from cnsc.haai.gml.receipts import (
        Receipt,
        ReceiptContent,
        ReceiptDecision,
        ReceiptProvenance,
        ReceiptSignature,
        ReceiptStepType,
        ReceiptSystem,
    )
except ImportError:
    from .core.receipts import (
        Receipt,
        ReceiptContent,
        ReceiptDecision,
        ReceiptProvenance,
        ReceiptSignature,
        ReceiptStepType,
        ReceiptSystem,
    )

# Phases - redirect to cnsc.haai (CFAPhase, PhaseLoom)
try:
    from cnsc.haai.nsc.cfa import CFAPhase as Phase
    from cnsc.haai.gml.phaseloom import PhaseLoom as PhaseManager
    PhaseConfig = None  # Not in cnsc.haai
    PhaseState = None
except ImportError:
    from .core.phases import Phase, PhaseConfig, PhaseState, PhaseManager

# CoherenceBudget/VectorResidual - redirect to cnsc.haai.ats.coherence
try:
    from cnsc.haai.ats.coherence import CoherenceBudget, VectorResidual
except ImportError:
    from .core.coherence import CoherenceBudget, VectorResidual

# Kernel - no cnsc.haai equivalent, use legacy
from .kernel.minimal import MinimalKernel, EpisodeResult

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
    "VectorResidual",
    # Kernel
    "MinimalKernel",
    "EpisodeResult",
]

"""
NSC (Network Structured Code) Module

This module provides:
- IR: Graph-based rewrite intermediate representation
- CFA: Control Flow Automaton for phase enforcement
- VM: Stack-based bytecode virtual machine
- Gates: Gate and rail constraint evaluation
"""

from cnsc.haai.nsc.ir import (
    NSCProgram,
    NSCRewrite,
    NSCCFG,
    NSCType,
    NSCOpcode,
    NSCInstruction,
    NSCValue,
    NSCBlock,
    NSCFunction,
    # Primitive type constants
    INT,
    STRING,
    BOOL,
    FLOAT,
    UNIT,
)
from cnsc.haai.nsc.cfa import (
    CFAPhase,
    CFAState,
    CFATransition,
    CFAAutomaton,
)
from cnsc.haai.nsc.vm import (
    BytecodeEmitter,
    VM,
    VMState,
    VMFrame,
    VMStack,
    create_vm,
)
from cnsc.haai.nsc.gates import (
    GateType,
    GateCondition,
    GateResult,
    Gate,
    EvidenceSufficiencyGate,
    CoherenceCheckGate,
    GateManager,
)
from cnsc.haai.nsc.proposer_client import (
    ProposerClient,
)
from cnsc.haai.nsc.proposer_client_errors import (
    ProposerClientError,
    ConnectionError,
    TimeoutError,
)

__all__ = [
    # IR
    "NSCProgram",
    "NSCRewrite",
    "NSCCFG",
    "NSCType",
    "NSCOpcode",
    "NSCInstruction",
    "NSCValue",
    "NSCBlock",
    "NSCFunction",
    # CFA
    "CFAPhase",
    "CFAState",
    "CFATransition",
    "CFAAutomaton",
    # VM
    "BytecodeEmitter",
    "VM",
    "VMState",
    "VMFrame",
    "VMStack",
    # Gates
    "GateType",
    "GateCondition",
    "GateResult",
    "Gate",
    "EvidenceSufficiencyGate",
    "CoherenceCheckGate",
    "GateManager",
    # ProposerClient
    "ProposerClient",
    "ProposerClientError",
    "ConnectionError",
    "TimeoutError",
]

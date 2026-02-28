"""
NSC IR (Intermediate Representation)

Graph-based rewrite intermediate representation for the Coherence Framework.

This module provides:
- NSCProgram: Complete program representation
- NSCRewrite: Rewrite rule definition
- NSCCFG: Control flow graph
- NSCType: NSC type system with coherence annotations
- NSCInstruction: Low-level instructions
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4
from datetime import datetime


class NSCOpcode(Enum):
    """NSC bytecode opcodes."""

    # Stack operations
    PUSH = auto()
    POP = auto()
    DUP = auto()
    SWAP = auto()

    # Local operations
    LOAD = auto()
    STORE = auto()
    ALLOC = auto()

    # Arithmetic
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    NEG = auto()

    # Comparison
    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()

    # Logical
    AND = auto()
    OR = auto()
    NOT = auto()

    # Control flow
    JUMP = auto()
    JUMP_IF = auto()
    JUMP_IF_NOT = auto()
    CALL = auto()
    RET = auto()

    # Memory
    LOAD_FIELD = auto()
    STORE_FIELD = auto()
    LOAD_INDEX = auto()
    STORE_INDEX = auto()

    # Type operations
    CAST = auto()
    TYPE_CHECK = auto()

    # Coherence operations
    COHERENCE_READ = auto()
    COHERENCE_WRITE = auto()
    COHERENCE_CHECK = auto()

    # Gate operations
    GATE_EVAL = auto()
    RAIL_CHECK = auto()

    # Trace operations
    TRACE_EVENT = auto()
    EMIT_RECEIPT = auto()

    # Special
    HALT = auto()
    NOP = auto()


@dataclass
class NSCType:
    """
    NSC type with coherence annotations.

    NSC uses structural typing with coherence annotations for
    tracking provenance and transformation history.
    """

    type_id: str
    name: str
    is_primitive: bool = False
    fields: Dict[str, "NSCType"] = field(default_factory=dict)
    element_type: Optional["NSCType"] = None
    coherence_bound: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "type_id": self.type_id,
            "name": self.name,
            "is_primitive": self.is_primitive,
            "coherence_bound": self.coherence_bound,
            "metadata": self.metadata,
        }
        if self.fields:
            result["fields"] = {k: v.to_dict() for k, v in self.fields.items()}
        if self.element_type:
            result["element_type"] = self.element_type.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NSCType":
        """Create from dictionary."""
        fields = {}
        if "fields" in data:
            fields = {k: cls.from_dict(v) for k, v in data["fields"].items()}
        element_type = None
        if "element_type" in data and data["element_type"]:
            element_type = cls.from_dict(data["element_type"])
        return cls(
            type_id=data["type_id"],
            name=data["name"],
            is_primitive=data.get("is_primitive", False),
            fields=fields,
            element_type=element_type,
            coherence_bound=data.get("coherence_bound"),
            metadata=data.get("metadata", {}),
        )

    def is_compatible_with(self, other: "NSCType") -> bool:
        """Check type compatibility."""
        if self.type_id == other.type_id:
            return True
        if self.is_primitive or other.is_primitive:
            return False
        # Structural compatibility for composites
        if len(self.fields) != len(other.fields):
            return False
        for name in self.fields:
            if name not in other.fields:
                return False
            if not self.fields[name].is_compatible_with(other.fields[name]):
                return False
        return True


@dataclass
class NSCValue:
    """
    Immediate value in NSC.

    Represents constants and literals in NSC bytecode.
    """

    value_type: NSCType
    value: Any
    provenance: Optional[str] = None
    coherence_level: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "value_type": self.value_type.to_dict(),
            "value": self.value,
            "provenance": self.provenance,
            "coherence_level": self.coherence_level,
        }


@dataclass
class NSCInstruction:
    """
    NSC instruction.

    Low-level instruction with optional operands.
    """

    opcode: NSCOpcode
    operands: List[Any] = field(default_factory=list)
    result_type: Optional[NSCType] = None
    source_span: Optional[Tuple[int, int, int, int]] = None
    provenance: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "opcode": self.opcode.name,
            "operands": self.operands,
            "result_type": self.result_type.to_dict() if self.result_type else None,
            "source_span": self.source_span,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NSCInstruction":
        """Create from dictionary."""
        return cls(
            opcode=NSCOpcode[data["opcode"]],
            operands=data["operands"],
            result_type=NSCType.from_dict(data["result_type"]) if data.get("result_type") else None,
            source_span=tuple(data["source_span"]) if data.get("source_span") else None,
            provenance=data.get("provenance"),
        )


@dataclass
class NSCBlock:
    """
    NSC basic block.

    A block of instructions with a single entry and exit point.
    """

    block_id: str
    name: str
    instructions: List[NSCInstruction] = field(default_factory=list)
    predecessors: List[str] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)
    dominance_frontier: Set[str] = field(default_factory=set)
    phi_instructions: List[NSCInstruction] = field(default_factory=list)

    def add_instruction(self, instruction: NSCInstruction) -> None:
        """Add instruction to block."""
        self.instructions.append(instruction)

    def add_successor(self, block_id: str) -> None:
        """Add successor block."""
        if block_id not in self.successors:
            self.successors.append(block_id)

    def add_predecessor(self, block_id: str) -> None:
        """Add predecessor block."""
        if block_id not in self.predecessors:
            self.predecessors.append(block_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "block_id": self.block_id,
            "name": self.name,
            "instructions": [inst.to_dict() for inst in self.instructions],
            "predecessors": self.predecessors,
            "successors": self.successors,
            "dominance_frontier": list(self.dominance_frontier),
            "phi_instructions": [inst.to_dict() for inst in self.phi_instructions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NSCBlock":
        """Create from dictionary."""
        return cls(
            block_id=data["block_id"],
            name=data["name"],
            instructions=[NSCInstruction.from_dict(i) for i in data["instructions"]],
            predecessors=data["predecessors"],
            successors=data["successors"],
            dominance_frontier=set(data.get("dominance_frontier", [])),
            phi_instructions=[
                NSCInstruction.from_dict(i) for i in data.get("phi_instructions", [])
            ],
        )


@dataclass
class NSCFunction:
    """
    NSC function.

    A function with control flow graph and type signature.
    """

    function_id: str
    name: str
    param_types: List[NSCType] = field(default_factory=list)
    return_type: Optional[NSCType] = None
    local_types: Dict[str, NSCType] = field(default_factory=dict)
    blocks: Dict[str, NSCBlock] = field(default_factory=dict)
    entry_block: str = ""
    exit_blocks: List[str] = field(default_factory=list)
    coherence_requirement: float = 0.5

    def add_block(self, block: NSCBlock) -> None:
        """Add block to function."""
        self.blocks[block.block_id] = block

    def get_block(self, block_id: str) -> Optional[NSCBlock]:
        """Get block by ID."""
        return self.blocks.get(block_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "function_id": self.function_id,
            "name": self.name,
            "param_types": [t.to_dict() for t in self.param_types],
            "return_type": self.return_type.to_dict() if self.return_type else None,
            "local_types": {k: v.to_dict() for k, v in self.local_types.items()},
            "blocks": {k: b.to_dict() for k, b in self.blocks.items()},
            "entry_block": self.entry_block,
            "exit_blocks": self.exit_blocks,
            "coherence_requirement": self.coherence_requirement,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NSCFunction":
        """Create from dictionary."""
        return cls(
            function_id=data["function_id"],
            name=data["name"],
            param_types=[NSCType.from_dict(t) for t in data["param_types"]],
            return_type=NSCType.from_dict(data["return_type"]) if data.get("return_type") else None,
            local_types={k: NSCType.from_dict(v) for k, v in data.get("local_types", {}).items()},
            blocks={k: NSCBlock.from_dict(b) for k, b in data["blocks"].items()},
            entry_block=data["entry_block"],
            exit_blocks=data["exit_blocks"],
            coherence_requirement=data.get("coherence_requirement", 0.5),
        )


@dataclass
class NSCCFG:
    """
    NSC Control Flow Graph.

    SSA form representation with dominance information.
    """

    entry_block: str
    exit_blocks: List[str] = field(default_factory=list)
    blocks: Dict[str, NSCBlock] = field(default_factory=dict)
    immediate_dominators: Dict[str, str] = field(default_factory=dict)
    dominance_tree: Dict[str, List[str]] = field(default_factory=dict)

    def add_block(self, block: NSCBlock) -> None:
        """Add block to CFG."""
        self.blocks[block.block_id] = block

    def get_block(self, block_id: str) -> Optional[NSCBlock]:
        """Get block by ID."""
        return self.blocks.get(block_id)

    def add_edge(self, from_id: str, to_id: str) -> None:
        """Add CFG edge."""
        from_block = self.blocks.get(from_id)
        to_block = self.blocks.get(to_id)
        if from_block and to_block:
            from_block.add_successor(to_id)
            to_block.add_predecessor(from_id)
            if to_id not in self.exit_blocks and from_id not in self.exit_blocks:
                pass

    def compute_dominance(self) -> None:
        """Compute dominance information using Lengauer-Tarjan algorithm."""
        # Simple iterative algorithm for now
        if not self.blocks:
            return

        # Initialize
        for block_id in self.blocks:
            self.immediate_dominators[block_id] = None

        # Entry block dominates itself
        self.immediate_dominators[self.entry_block] = self.entry_block

        # Iterative fixpoint
        changed = True
        while changed:
            changed = False
            for block_id, block in self.blocks.items():
                if block_id == self.entry_block:
                    continue

                predecessors = block.predecessors
                if not predecessors:
                    continue

                # Intersect dominators of all predecessors
                new_dom = None
                for pred_id in predecessors:
                    pred_dom = self.immediate_dominators.get(pred_id)
                    if pred_dom is not None:
                        if new_dom is None:
                            new_dom = set(self.blocks.keys())
                        new_dom = new_dom.intersection(self._get_dominator_set(pred_id))

                if new_dom is None:
                    new_dom = set(self.blocks.keys())

                new_dom.add(block_id)

                old_dom = self._get_dominator_set(block_id)
                if new_dom != old_dom:
                    self._set_dominator_set(block_id, new_dom)
                    changed = True

    def _get_dominator_set(self, block_id: str) -> Set[str]:
        """Get dominator set for block."""
        idom = self.immediate_dominators.get(block_id)
        if idom is None:
            return set()
        result = set()
        current = block_id
        while current is not None:
            result.add(current)
            current = self.immediate_dominators.get(current)
            if current == idom and current != block_id:
                break
        return result

    def _set_dominator_set(self, block_id: str, dom_set: Set[str]) -> None:
        """Set dominator set for block."""
        # Store just the immediate dominator for efficiency
        if block_id in dom_set:
            dom_set = dom_set.copy()
            dom_set.discard(block_id)
            if dom_set:
                # Find closest dominator
                for candidate in dom_set:
                    other_doms = self._get_dominator_set(candidate)
                    if dom_set - {candidate} <= other_doms:
                        self.immediate_dominators[block_id] = candidate
                        return
        self.immediate_dominators[block_id] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_block": self.entry_block,
            "exit_blocks": self.exit_blocks,
            "blocks": {k: b.to_dict() for k, b in self.blocks.items()},
            "immediate_dominators": self.immediate_dominators,
            "dominance_tree": self.dominance_tree,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NSCCFG":
        """Create from dictionary."""
        cfg = cls(
            entry_block=data["entry_block"],
            exit_blocks=data["exit_blocks"],
        )
        cfg.blocks = {k: NSCBlock.from_dict(b) for k, b in data["blocks"].items()}
        cfg.immediate_dominators = data.get("immediate_dominators", {})
        cfg.dominance_tree = data.get("dominance_tree", {})
        return cfg


@dataclass
class NSCRewrite:
    """
    NSC Rewrite Rule.

    Defines a rewrite rule with pattern, conditions, and replacement.
    """

    rewrite_id: str
    name: str
    pattern: Dict[str, Any]
    replacement: Dict[str, Any]
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    priority: int = 0
    coherence_cost: float = 0.0
    is_conditional: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rewrite_id": self.rewrite_id,
            "name": self.name,
            "pattern": self.pattern,
            "conditions": self.conditions,
            "replacement": self.replacement,
            "priority": self.priority,
            "coherence_cost": self.coherence_cost,
            "is_conditional": self.is_conditional,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NSCRewrite":
        """Create from dictionary."""
        return cls(
            rewrite_id=data["rewrite_id"],
            name=data["name"],
            pattern=data["pattern"],
            conditions=data.get("conditions", []),
            replacement=data["replacement"],
            priority=data.get("priority", 0),
            coherence_cost=data.get("coherence_cost", 0.0),
            is_conditional=data.get("is_conditional", False),
        )


@dataclass
class NSCProgram:
    """
    NSC Program.

    Complete program representation with functions and rewrite rules.
    """

    program_id: str
    name: str
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Types
    types: Dict[str, NSCType] = field(default_factory=dict)

    # Functions
    functions: Dict[str, NSCFunction] = field(default_factory=dict)
    entry_function: Optional[str] = None

    # Rewrite rules
    rewrite_rules: List[NSCRewrite] = field(default_factory=list)

    # Global types and values
    global_types: Dict[str, NSCType] = field(default_factory=dict)
    global_values: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_type(self, nsc_type: NSCType) -> None:
        """Add type to program."""
        self.types[nsc_type.type_id] = nsc_type

    def add_function(self, func: NSCFunction) -> None:
        """Add function to program."""
        self.functions[func.function_id] = func

    def add_rewrite_rule(self, rule: NSCRewrite) -> None:
        """Add rewrite rule."""
        self.rewrite_rules.append(rule)

    def get_function(self, function_id: str) -> Optional[NSCFunction]:
        """Get function by ID."""
        return self.functions.get(function_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "program_id": self.program_id,
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "types": {k: t.to_dict() for k, t in self.types.items()},
            "functions": {k: f.to_dict() for k, f in self.functions.items()},
            "entry_function": self.entry_function,
            "rewrite_rules": [r.to_dict() for r in self.rewrite_rules],
            "global_types": {k: t.to_dict() for k, t in self.global_types.items()},
            "global_values": self.global_values,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NSCProgram":
        """Create from dictionary."""
        return cls(
            program_id=data["program_id"],
            name=data["name"],
            version=data.get("version", "1.0.0"),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if "created_at" in data
                else datetime.utcnow()
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if "updated_at" in data
                else datetime.utcnow()
            ),
            types={k: NSCType.from_dict(t) for k, t in data.get("types", {}).items()},
            functions={k: NSCFunction.from_dict(f) for k, f in data.get("functions", {}).items()},
            entry_function=data.get("entry_function"),
            rewrite_rules=[NSCRewrite.from_dict(r) for r in data.get("rewrite_rules", [])],
            global_types={k: NSCType.from_dict(t) for k, t in data.get("global_types", {}).items()},
            global_values=data.get("global_values", {}),
            metadata=data.get("metadata", {}),
        )


def create_nsc_program(name: str, program_id: Optional[str] = None) -> NSCProgram:
    """Create a new NSC program."""
    return NSCProgram(
        program_id=program_id or str(uuid4()),
        name=name,
    )


def create_nsc_function(
    name: str,
    param_types: Optional[List[NSCType]] = None,
    return_type: Optional[NSCType] = None,
) -> NSCFunction:
    """Create a new NSC function."""
    function_id = str(uuid4())
    return NSCFunction(
        function_id=function_id,
        name=name,
        param_types=param_types,
        return_type=return_type,
    )


def create_nsc_block(name: str) -> NSCBlock:
    """Create a new NSC block."""
    block_id = str(uuid4())[:8]
    return NSCBlock(
        block_id=block_id,
        name=name,
    )


# Primitive type constants for convenience
# These are also available as NSCType.INT, NSCType.STRING, etc.
INT = NSCType(type_id="int", name="int", is_primitive=True)
STRING = NSCType(type_id="string", name="string", is_primitive=True)
BOOL = NSCType(type_id="bool", name="bool", is_primitive=True)
FLOAT = NSCType(type_id="float", name="float", is_primitive=True)
UNIT = NSCType(type_id="unit", name="unit", is_primitive=True)

# Add as class attributes for convenience
NSCType.INT = INT
NSCType.STRING = STRING
NSCType.BOOL = BOOL
NSCType.FLOAT = FLOAT
NSCType.UNIT = UNIT

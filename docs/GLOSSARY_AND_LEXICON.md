# CNSC-HAAI Glossary and Lexicon

**Document Version:** 1.0.0  
**Status:** Canonical  
**Last Updated:** 2026-02-09

---

## Table of Contents

1. [Overview](#overview)
2. [Core Coherence Terms](#core-coherence-terms)
3. [GLLL (Glyph Low-Level Language) Terms](#glll-glyph-low-level-language-terms)
4. [GHLL (Glyph High-Level Language) Terms](#ghll-glyph-high-level-language-terms)
5. [NSC (Native Stack Computing) Terms](#nsc-native-stack-computing-terms)
6. [GML (Governance Markup Language) Terms](#gml-governance-markup-language-terms)
7. [Seam Terms](#seam-terms)
8. [NPE (Neuro-Proposition Engine) Terms](#npe-neuro-proposition-engine-terms)
9. [Cross-Component Terminology Index](#cross-component-terminology-index)
10. [Default Values and Configurations](#default-values-and-configurations)

---

## Overview

This document provides a comprehensive glossary and lexicon for the CNSC-HAAI (Cognitive Neural Symbolic Coherence - Hierarchical Adaptive Artificial Intelligence) system. Terms are organized by architectural component with cross-references to related concepts.

### Tag Conventions

| Tag | Meaning |
|-----|---------|
| **CANON** | Required for compliance and auditable governance |
| **BRIDGE/UNVERIFIED** | Optional hypotheses or cross-domain analogies |
| **[Component]** | Terms specific to that component |

---

## Core Coherence Terms

These terms form the foundational vocabulary of the Coherence Framework.

### Coherence
**Definition:** Measurable governance budget (debt + residual vector) that determines affordability of system actions.

**Components:**
- **Debt (C):** Scalar integrity budget derived from residuals and penalties
- **Residual:** Measurable defect relative to constraints, normalized to budget boundary

**See Also:** [`CoherenceBudget`](src/cnhaai/core/coherence.py), [`CoherenceTransport`](Coherence_Spec_v1_0/docs/05_Coherence_Transport_and_Balance.md)

---

### Gates
**Definition:** Hard/soft acceptability checks that determine admissible evolution of the system.

**Types:**
- [`EvidenceSufficiencyGate`](src/cnsc/haai/nsc/gates.py:296): Evaluates whether sufficient evidence has been gathered
- [`CoherenceCheckGate`](src/cnsc/haai/nsc/gates.py:318): Verifies coherence level is acceptable
- [`AffordabilityGate`](src/cnsc/haai/nsc/gates.py:27): Checks if action is within budget
- [`RailTrajectoryGate`](src/cnsc/haai/nsc/gates.py:27): Validates rail compliance
- [`PhaseTransitionGate`](src/cnsc/haai/nsc/gates.py:27): Evaluates phase transition conditions

**See Also:** [`GateType`](src/cnsc/haai/nsc/gates.py:27), [`GateDecision`](src/cnsc/haai/nsc/gates.py:37), [`GateCondition`](src/cnsc/haai/nsc/gates.py:45), [`GateResult`](src/cnsc/haai/nsc/gates.py:142)

---

### Rails
**Definition:** Bounded corrective actions invoked when gates fail. Rails provide deterministic remediation paths.

**See Also:** [`RailTrajectoryGate`](src/cnsc/haai/nsc/gates.py:27)

---

### Receipts
**Definition:** Structured logs for decisions, residuals, and actions. Receipts enable replay and auditability.

**Properties:**
- Input hash capture
- Output hash computation
- Transformation verification
- Chain hash linking

**See Also:** [`Receipt`](src/cnsc/haai/gml/receipts.py), [`ReceiptChain`](src/cnsc/haai/gml/receipts.py), [`ReceiptStepType`](src/cnsc/haai/gml/receipts.py:32)

---

### Hysteresis
**Definition:** Separate enter/exit thresholds to prevent oscillation (chatter) between states.

**Implementation:** [`CoherenceStatus`](src/cnhaai/core/coherence.py) with distinct thresholds for status transitions.

---

### Replay
**Definition:** Recomputation of decisions from receipts within tolerance to verify correctness.

**Invariant:** Replay must match original execution.

---

### Certificate
**Definition:** Run summary containing final hash and maxima. Certificates provide attestation of execution.

**Schema:** [`run_certificate.schema.json`](Coherence_Spec_v1_0/schemas/run_certificate.schema.json)

---

### Transport/Current
**Definition:** Structured change or flow of coherence (CANON for discrete; BRIDGE for continuous).

---

### Dissipation
**Definition:** Deliberate reduction of debt via bounded correction. The inverse of accumulation.

---

### Reconstruction
**Definition:** Fidelity of state representation or model output. Measures how well the system recreates intended behavior.

---

### Contradiction
**Definition:** Detectable inconsistency within symbolic claims or constraints. Contradictions trigger remediation.

---

## GLLL (Glyph Low-Level Language) Terms

GLLL provides error-tolerant binary encoding using Hadamard codes.

### Glyph
**Definition:** The fundamental unit of GLLL encoding. A glyph is a vector encoded using Hadamard codes.

**Properties:**
- Error tolerance through syndrome decoding
- Deterministic decode from noisy input
- Versioned for extensibility

---

### Hadamard Code
**Definition:** Error-correcting code based on Hadamard matrices. Used for noise-tolerant transmission.

**Properties:**
- Sylvester construction: H₂ₙ = [Hₙ Hₙ; Hₙ -Hₙ]
- Order: Power of 2 (1, 2, 4, 8, 16, 32, 64, 128, ...)
- Maximum correctable errors: t = floor(n/4)

**See Also:** [`HadamardMatrix`](src/cnsc/haai/glll/hadamard.py:38), [`HadamardOrder`](src/cnsc/haai/glll/hadamard.py:25)

---

### Codebook
**Definition:** Mapping between symbols and their Hadamard-encoded glyph representations.

**Formats:**
- Binary format for efficient storage
- JSON format for interoperability

**Schema:** [`codebook.schema.json`](schemas/codebook.schema.json)

**See Also:** [`Codebook`](src/cnsc/haai/glll/codebook.py)

---

### Glyph Type
**Definition:** Classification of glyphs by their encoding characteristics.

**Categories:**
- **SYMBOL:** Simple symbol encoding
- **PATTERN:** Regular expression pattern matching
- **TEMPLATE:** Format string template
- **GRAMMAR:** Grammar production rule

---

### Symbol Category
**Definition:** Semantic classification of symbols in the codebook.

---

### Vector
**Definition:** Binary data representation in GLLL. Vectors are encoded/decoded using Hadamard matrices.

---

### Packet
**Definition:** Container for transmitting glyphs across the GLLL layer.

**Properties:**
- Version information
- Payload (encoded glyphs)
- Error detection (syndrome)

**See Also:** [`Packet`](src/cnsc/haai/glll/packetizer.py)

---

### Distance Metric
**Definition:** Measure of similarity between glyphs. Used for error detection and correction.

**Implementation:** Hamming distance or Hadamard transform magnitude comparison.

---

### Hadamard Basis
**Definition:** The set of orthogonal vectors that form the rows of a Hadamard matrix.

---

### Deterministic Decode
**Definition:** Property that the same noisy input always produces the same decoded output.

---

### Glyph Construction
**Definition:** Process of creating valid glyphs from source symbols.

**Steps:**
1. Symbol to binary index conversion
2. Hadamard matrix row selection
3. Codeword generation

---

### Versioning
**Definition:** Glyph format version for backward/forward compatibility.

**Current Version:** 1.0

---

## GHLL (Glyph High-Level Language) Terms

GHLL provides semantic structure and type system for glyph-based programming.

### LexiconEntry
**Definition:** Single lexicon entry defining parse forms, semantics, and receipt signatures.

**Attributes:**
- [`semantic_atom`](src/cnsc/haai/ghll/lexicon.py:106): Stable identifier
- [`parse_forms`](src/cnsc/haai/ghll/lexicon.py:106): Recognition patterns
- [`semantics`](src/cnsc/haai/ghll/lexicon.py:106): Semantic description
- [`receipt_signature`](src/cnsc/haai/ghll/lexicon.py:106): Provenance information

**See Also:** [`LexiconManager`](src/cnsc/haai/ghll/lexicon.py:191)

---

### SemanticAtom
**Definition:** Stable identifier for semantic concepts. Maps tokens in source code to meaning.

**Format:** Hierarchical namespace (e.g., `kw_if`, `op_eq`)

---

### ParseForm
**Definition:** Defines how a lexical entry is recognized in source code.

**Attributes:**
- [`form_type`](src/cnsc/haai/ghll/lexicon.py:32): SYMBOL, PATTERN, TEMPLATE, GRAMMAR
- [`pattern`](src/cnsc/haai/ghll/lexicon.py:32): Recognition pattern
- [`precedence`](src/cnsc/haai/ghll/lexicon.py:32): Operator precedence (for expressions)
- [`associativity`](src/cnsc/haai/ghll/lexicon.py:32): Left, right, or none

**See Also:** [`ParseFormType`](src/cnsc/haai/ghll/lexicon.py:23)

---

### ReceiptSignature
**Definition:** Provenance and integrity information for lexicon entries.

**Attributes:**
- [`algorithm`](src/cnsc/haai/ghll/lexicon.py:68): Hash algorithm (SHA256)
- [`digest`](src/cnsc/haai/ghll/lexicon.py:68): Hash digest
- [`timestamp`](src/cnsc/haai/ghll/lexicon.py:68): Creation timestamp

---

### LexiconManager
**Definition:** Manages the lexicon for GHLL with CRUD operations, lookup, and validation.

**Capabilities:**
- Add/get entries by semantic atom
- Token lookup with pattern fallback
- Category-based filtering
- Integrity validation and repair

---

### Keywords
**Definition:** Reserved words in GHLL with specific semantic meaning.

**Examples:**
| Keyword | Semantic Atom | Purpose |
|---------|---------------|---------|
| `if` | `kw_if` | Conditional branching |
| `then` | `kw_then` | Consequent clause |
| `else` | `kw_else` | Alternative clause |
| `let` | `kw_let` | Variable binding |

**See Also:** [`spec/ghll/02_Grammar_EBNF.md`](spec/ghll/02_Grammar_EBNF.md)

---

### Operators
**Definition:** Symbols that perform operations on values.

**Examples:**
| Operator | Semantic Atom | Arity | Purpose |
|----------|---------------|-------|---------|
| `=` | `op_assign` | Binary | Assignment |
| `==` | `op_eq` | Binary | Equality comparison |
| `+` | `op_add` | Binary | Addition |
| `-` | `op_sub` | Binary | Subtraction |

---

### Delimiters
**Definition:** Tokens that structure code and separate expressions.

**Examples:**
| Delimiter | Semantic Atom | Purpose |
|-----------|---------------|---------|
| `(` | `delim_lparen` | Left parenthesis |
| `)` | `delim_rparen` | Right parenthesis |
| `{` | `delim_lbrace` | Left brace |
| `}` | `delim_rbrace` | Right brace |

---

### TypeOrigin
**Definition:** Source of type information (lexicon, inference, annotation).

---

### TypeRegistry
**Definition:** Repository of all known type definitions.

---

### TypeVariable
**Definition:** Placeholder for unresolved types during type checking.

---

### TypeChecker
**Definition:** Component that verifies type correctness of GHLL programs.

---

### TypeSystem Types

| Type | Definition |
|------|------------|
| [`FunctionType`](spec/ghll/03_Type_System.md) | Function signature with parameter and return types |
| [`StructType`](spec/ghll/03_Type_System.md) | Structured collection of named fields |
| [`UnionType`](spec/ghll/03_Type_System.md) | Type that can be one of several alternatives |
| [`SequenceType`](spec/ghll/03_Type_System.md) | Ordered collection of elements |
| [`OptionalType`](spec/ghll/03_Type_System.md) | Type that may be absent (None) |

---

## NSC (Native Stack Computing) Terms

NSC provides the runtime execution model for compiled GHLL programs.

### Bytecode
**Definition:** Low-level instruction format executed by the NSC VM.

**Format:** Stack-based with typed operands.

**See Also:** [`NSCOpcode`](src/cnsc/haai/nsc/ir.py)

---

### VM (Virtual Machine)
**Definition:** Stack-based virtual machine that executes NSC bytecode.

**Components:**
- [`VMStack`](src/cnsc/haai/nsc/vm.py): Operand stack
- [`VMFrame`](src/cnsc/haai/nsc/vm.py): Execution frame with local variables
- [`VMState`](src/cnsc/haai/nsc/vm.py): Complete VM state snapshot

**See Also:** [`NSC VM`](src/cnsc/haai/nsc/vm.py)

---

### IR (Intermediate Representation)
**Definition:** Structured representation of bytecode instructions.

**Types:** See NSC Opcodes below.

---

### NSC Opcodes

#### Stack Operations
| Opcode | Operand(s) | Description |
|--------|------------|-------------|
| `PUSH` | value | Push value onto stack |
| `POP` | - | Pop top value |
| `DUP` | - | Duplicate top value |
| `SWAP` | - | Swap top two values |

#### Local Operations
| Opcode | Operand(s) | Description |
|--------|------------|-------------|
| `LOAD` | index | Load local variable |
| `STORE` | index | Store local variable |
| `ALLOC` | size | Allocate stack space |

#### Arithmetic Operations
| Opcode | Operand(s) | Description |
|--------|------------|-------------|
| `ADD` | - | Add top two values |
| `SUB` | - | Subtract top from second |
| `MUL` | - | Multiply top two values |
| `DIV` | - | Divide second by top |
| `MOD` | - | Modulo |
| `NEG` | - | Negate top value |

#### Comparison Operations
| Opcode | Operand(s) | Description |
|--------|------------|-------------|
| `EQ` | - | Equality check |
| `NE` | - | Inequality check |
| `LT` | - | Less than |
| `LE` | - | Less than or equal |
| `GT` | - | Greater than |
| `GE` | - | Greater than or equal |

#### Logical Operations
| Opcode | Operand(s) | Description |
|--------|------------|-------------|
| `AND` | - | Logical AND |
| `OR` | - | Logical OR |
| `NOT` | - | Logical NOT |

#### Control Operations
| Opcode | Operand(s) | Description |
|--------|------------|-------------|
| `JUMP` | target | Unconditional jump |
| `JUMP_IF` | target | Pop and jump if true |
| `JUMP_IF_NOT` | target | Pop and jump if false |
| `CALL` | func | Call function |
| `RET` | - | Return from function |

#### Memory Operations
| Opcode | Operand(s) | Description |
|--------|------------|-------------|
| `LOAD_FIELD` | offset | Load struct field |
| `STORE_FIELD` | offset | Store struct field |
| `LOAD_INDEX` | - | Load from sequence |
| `STORE_INDEX` | - | Store to sequence |

#### Type Operations
| Opcode | Operand(s) | Description |
|--------|------------|-------------|
| `CAST` | target_type | Type conversion |
| `TYPE_CHECK` | expected_type | Runtime type check |

#### Coherence Operations
| Opcode | Operand(s) | Description |
|--------|------------|-------------|
| `COHERENCE_READ` | - | Read coherence level |
| `COHERENCE_WRITE` | value | Write coherence level |
| `COHERENCE_CHECK` | threshold | Verify coherence threshold |

#### Gate Operations
| Opcode | Operand(s) | Description |
|--------|------------|-------------|
| `GATE_EVAL` | gate_id | Evaluate gate |
| `RAIL_CHECK` | rail_id | Check rail compliance |

#### Trace Operations
| Opcode | Operand(s) | Description |
|--------|------------|-------------|
| `TRACE_EVENT` | event_type | Emit trace event |
| `EMIT_RECEIPT` | receipt_type | Emit receipt |

#### Special Operations
| Opcode | Operand(s) | Description |
|--------|------------|-------------|
| `HALT` | - | Terminate execution |
| `NOP` | - | No operation |

---

### NSCType
**Definition:** Type annotation for NSC values.

**Types:** `int`, `float`, `bool`, `string`, `struct`, `function`, `sequence`, `optional`

---

### NSCValue
**Definition:** Runtime value with type and data.

---

### Frontier
**Definition:** Boundary between committed (soft) and tentative (hard) state.

**Invariant:** Operations beyond frontier require coherence checks.

---

### NSCBlock
**Definition:** Basic block of instructions with single entry/exit.

---

### NSCCFG
**Definition:** Control Flow Graph representing program structure.

**Properties:**
- Nodes: [`NSCBlock`](src/cnsc/haai/nsc/cfa.py)
- Edges: Control flow transitions

---

### NSCFunction
**Definition:** Callable function with parameters, locals, and body.

---

### NSCInstruction
**Definition:** Single bytecode instruction.

---

### Dominance Frontier
**Definition:** Set of blocks where dominance relationships change.

---

### PHI Instructions
**Definition:** Instructions that merge values from different control flow paths.

---

### Lengauer-Tarjan
**Definition:** Algorithm for computing dominance relationships in CFG.

---

## GML (Governance Markup Language) Terms

GML provides trace, receipt, and audit capabilities.

### Trace
**Definition:** Sequence of events recording system execution.

**Components:**
- [`TraceEvent`](src/cnsc/haai/gml/trace.py:48): Single atomic event
- [`TraceThread`](src/cnsc/haai/gml/trace.py:167): Thread of related events
- [`TraceManager`](src/cnsc/haai/gml/trace.py): Collection management

---

### TraceEvent
**Definition:** Single atomic event in the reasoning trace.

**Attributes:**
- `event_id`: Unique identifier
- `timestamp`: Event time
- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `event_type`: Event classification
- `message`: Human-readable description
- `details`: Structured event data
- `parent_event_id`: Causality link
- `coherence_before/after`: Coherence levels

**See Also:** [`TraceLevel`](src/cnsc/haai/gml/trace.py:28)

---

### TraceThread
**Definition:** Thread of related trace events with ordering.

**Attributes:**
- `thread_id`: Thread identifier
- `events`: Ordered list of events
- `parent_thread_id`: Parent thread (for nesting)
- `child_thread_ids`: Child threads

---

### Receipt
**Definition:** Cryptographic record of a system decision or action.

**Components:**
- [`ReceiptContent`](src/cnsc/haai/gml/receipts.py:283): Step type, input/output hashes, decision
- [`ReceiptSignature`](src/cnsc/haai/gml/receipts.py:241): HMAC-SHA256 signature

**See Also:** [`ReceiptChain`](src/cnsc/haai/gml/receipts.py)

---

### Receipt Chain
**Definition:** Linked list of receipts forming an auditable trail.

**Properties:**
- Each receipt contains hash of previous
- Enables tamper detection
- Supports replay verification

---

### Genesis Receipt
**Definition:** First receipt in a chain, with no predecessor.

---

### Chain Hash
**Definition:** Cumulative hash of all receipts in chain.

**Formula:** H(receipt) = HMAC(H(prev_receipt), receipt_content)

---

### Step Type
**Definition:** Classification of receipt-generating steps.

**Values:**
- `PARSE`, `TYPE_CHECK`, `GATE_EVAL`, `PHASE_TRANSITION`, `VM_EXECUTION`
- `COHERENCE_CHECK`, `TRACE_EVENT`, `CHECKPOINT`, `REPLAY`, `CUSTOM`

---

### Decision
**Definition:** Outcome of a step.

**Values:** `PASS`, `FAIL`, `WARN`, `SKIP`, `PENDING`

---

### Episode ID
**Definition:** Unique identifier for a coherent unit of work.

---

### Checkpoint
**Definition:** Saved state enabling backtracking or replay.

**Properties:**
- Complete state snapshot
- Receipt chain position
- Timestamp

---

### PhaseLoom Thread
**Definition:** Lightweight execution context for reasoning phases.

**See Also:** [`PhaseLoom`](src/cnsc/haai/gml/phaseloom.py)

---

### Coupling
**Definition:** Relationship between threads or phases.

**Types:**
- `depends_on`: Predecessor relationship
- `produces_for`: Output feeds input
- `blocks`: Synchronization point
- `triggers`: Event-based activation

---

### Phase Transition
**Definition:** Change from one reasoning phase to another.

**Governed by:** [`PhaseTransitionGate`](src/cnsc/haai/nsc/gates.py:27)

---

### Rewrite Event
**Definition:** Modification to the rewrite graph.

---

### Trace Serialization
**Definition:** Conversion of trace to storable format (JSON).

---

### ThreadState
**Definition:** Runtime state of a PhaseLoom thread.

---

### CouplingPolicy
**Definition:** Rules governing thread coupling.

---

### GateStackRun
**Definition:** Execution of a gate evaluation sequence.

---

### ThreadCoupling
**Definition:** Coupling configuration for thread interactions.

---

## Seam Terms

Seams are the boundaries between architectural layers.

### Seam
**Definition:** Boundary between architectural layers with defined contracts.

**Seams:**
| Seam | From | To | Purpose |
|------|------|-----|---------|
| GLLL→GHLL | GLLL | GHLL | Glyph decoding to semantic atoms |
| GHLL→NSC | GHLL | NSC | High-level to intermediate representation |
| NSC→GML | NSC | GML | Execution traces to receipts |

---

### Binding
**Definition:** Association of a GLLL glyph with its GHLL semantic meaning.

---

### Lowering
**Definition:** Transformation from higher-level representation to lower-level.

---

### Receipt Emission
**Definition:** Generation of receipts when crossing seams.

---

### Semantic Preservation
**Definition:** Property that meaning is maintained across seam transformations.

---

### Determinism
**Definition:** Property that same input produces same output across seams.

---

### Auditability
**Definition:** Capability to verify seam crossings through receipts.

---

### Input Hash
**Definition:** Hash of data entering a seam.

---

### Output Hash
**Definition:** Hash of data exiting a seam.

---

### Receipt Chain
**Definition:** Linked receipts tracking all seam crossings.

---

## NPE (Neuro-Proposition Engine) Terms

NPE provides intelligent proposal generation for repair and optimization.

### NPE
**Definition:** Neuro-Proposition Engine. Component that generates candidates for governance decisions.

---

### NPERequest
**Definition:** Request envelope for NPE operations.

**Attributes:**
- `spec`: Specification identifier
- `request_type`: PROPOSE or REPAIR
- `request_id`: Unique request identifier
- `domain`: Operation domain (GR = Governance/Repair)
- `determinism_tier`: D0 (fully deterministic)
- `seed`: Random seed for reproducibility
- `budgets`: Budget constraints
- `inputs`: Input data (state, constraints, goals, context)

**Default Values:**
- `spec`: "NPE-REQUEST-1.0"
- `request_type`: "propose"
- `domain`: "gr"
- `determinism_tier`: "d0"

---

### NPEResponse
**Definition:** Response envelope from NPE operations.

**Attributes:**
- `spec`: Specification identifier
- `response_id`: Unique response identifier
- `request_id`: Reference to request
- `corpus_snapshot_hash`: Corpus state hash
- `memory_snapshot_hash`: Aeonic memory state hash
- `registry_hash`: Proposer registry hash
- `candidates`: Generated candidates
- `diagnostics`: Diagnostic information

**Default Values:**
- `spec`: "NPE-RESPONSE-1.0"

---

### NPERepairRequest
**Definition:** Repair request with failure information.

**Additional Attributes:**
- `failure`: FailureInfo containing proof hash, failing gates, etc.

---

### Candidate
**Definition:** Proposed solution generated by proposers.

**Attributes:**
- `candidate_hash`: Unique identifier
- `candidate_type`: REPAIR, PLAN, SOLVER_CONFIG, EXPLAIN
- `domain`: Operation domain
- `input_state_hash`: Hash of input state
- `constraints_hash`: Hash of constraints
- `payload`: Candidate solution
- `evidence`: Supporting evidence items
- `scores`: Risk, utility, cost, confidence scores

**Default Scores:**
- `risk`: 0.5
- `utility`: 0.5
- `cost`: 0.5
- `confidence`: 0.5

---

### EvidenceItem
**Definition:** Evidence supporting a candidate.

**Attributes:**
- `evidence_id`: Unique identifier
- `source_type`: Source (receipt, corpus, codebook)
- `content_hash`: Hash of evidence content
- `relevance`: Relevance score (0.0-1.0)
- `taint_tags`: Filter status tags
- `filters_applied`: Applied filters

---

### Goal
**Definition:** Goal specification for proposal generation.

**Attributes:**
- `goal_type`: Type (repair, optimize, explain)
- `goal_payload`: Goal-specific parameters

---

### Context
**Definition:** Execution context for proposal generation.

**Attributes:**
- `risk_posture`: conservative, moderate, aggressive (default: "conservative")
- `allowed_sources`: List of allowed evidence sources
- `time_scope`: Time range for evidence
- `scenario_id`: Current scenario
- `policy_tags`: Applicable policies

**Default Values:**
- `risk_posture`: "conservative"

---

### StateRef
**Definition:** Reference to a system state.

**Attributes:**
- `state_hash`: SHA256 hash
- `step`: Step number
- `clock`: Clock information
- `summary`: State summary

---

### ConstraintsRef
**Definition:** Reference to system constraints.

**Attributes:**
- `constraints_hash`: SHA256 hash
- `params`: Constraint parameters
- `tags`: Constraint tags

---

### Budgets
**Definition:** Budget constraints for NPE operation.

**Attributes:**
| Attribute | Default | Description |
|-----------|---------|-------------|
| `max_wall_ms` | 1000 | Maximum wall-clock time (ms) |
| `max_candidates` | 16 | Maximum candidates returned |
| `max_evidence_items` | 100 | Maximum evidence items |
| `max_search_expansions` | 50 | Maximum search expansions |

---

### BudgetAccounting
**Definition:** Tracking of budget consumption.

**Attributes:**
- `wall_ms_used`: Time consumed
- `candidates_generated`: Candidates produced
- `evidence_retrieved`: Evidence items retrieved
- `search_expansions`: Expansions performed
- `proposer_wall_ms`: Per-proposer time tracking

---

### BudgetEnforcer
**Definition:** Component that enforces budget constraints.

**Methods:**
- `check_time_budget(additional_ms)`
- `check_candidates_budget(additional)`
- `check_evidence_budget(additional)`
- `check_search_budget(additional)`
- `record_time(ms, proposer_id)`
- `record_candidates(count)`
- `record_evidence(count)`
- `record_search_expansions(count)`

---

### Proposer
**Definition:** Component that generates candidates.

**Types:**
- [`ProposerClient`](src/cnsc/haai/nsc/proposer_client.py): RPC client for proposers
- Registry-based proposer discovery

---

### Registry
**Definition:** Repository of available proposers.

**Format:** YAML manifest ([`manifest.yaml`](src/npe/registry/manifest.yaml))

---

### Domain
**Definition:** Operational domain for NPE.

**Values:** `gr` (Governance/Repair)

---

### DeterminismTier
**Definition:** Reproducibility level.

**Values:** `d0` (Fully deterministic)

---

### Scores
**Definition:** Scoring information for candidates.

**Attributes:**
- `risk`: Risk score (0.0-1.0)
- `utility`: Utility score (0.0-1.0)
- `cost`: Cost score (0.0-1.0)
- `confidence`: Confidence score (0.0-1.0)

---

### CandidateType
**Definition:** Classification of candidates.

**Values:** `REPAIR`, `SOLVER_CONFIG`, `PLAN`, `EXPLAIN`

---

### Corpus
**Definition:** Collection of evidence and knowledge for proposal generation.

**See Also:** [`CorpusStore`](src/npe/retrieval/corpus_store.py)

---

### Codebooks
**Definition:** Structured knowledge bases for proposal generation.

**See Also:** [`CodebookStore`](src/npe/retrieval/codebook_store.py)

---

### ReceiptsStore
**Definition:** Storage for historical receipts.

**See Also:** [`ReceiptsStore`](src/npe/retrieval/receipts_store.py)

---

### CJ0 Canonicalization
**Definition:** Normalization of candidates for consistent comparison.

**See Also:** [`CJ0 Canon`](src/npe/core/canon.py)

---

### Typed Hashing
**Definition:** Hashing that preserves type information.

**See Also:** [`TypedHashing`](src/npe/core/hashing.py)

---

### Pass-Yield@k
**Definition:** Metric for candidate quality at k candidates.

---

### ProposerClient
**Definition:** Client for communicating with proposer services.

**Methods:**
- `propose(request)`: Generate proposals
- `repair(gate_name, failure_reasons, context)`: Request repair

---

## Cross-Component Terminology Index

| Term | Components | Definition |
|------|------------|------------|
| **Receipt** | GML, Seam, Coherence | Structured log for auditability |
| **Coherence** | Core, NSC, GML | Governance budget measurement |
| **Gate** | Core, NSC, NPE | Acceptability check |
| **Rail** | Core, NSC | Corrective action |
| **Trace** | GML, NSC | Execution record |
| **ReceiptSignature** | GHLL, GML, Seam | Integrity verification |
| **Budget** | NPE, Core | Resource constraint |
| **LexiconEntry** | GHLL, Seam | Parse form definition |
| **Bytecode** | NSC, Seam | VM instruction format |
| **SemanticAtom** | GHLL, GLLL, Seam | Stable identifier |
| **EpisodeID** | GML, NPE | Unit of work identifier |
| **Checkpoint** | GML, NSC | State save point |
| **Binding** | Seam, GLLL, GHLL | Semantic mapping |
| **Determinism** | Core, NSC, NPE | Reproducibility guarantee |

---

## Default Values and Configurations

### Budget Defaults (NPE)

```python
Budgets(
    max_wall_ms=1000,
    max_candidates=16,
    max_evidence_items=100,
    max_search_expansions=50
)
```

### Context Defaults (NPE)

```python
Context(
    risk_posture="conservative",
    allowed_sources=[],
    time_scope={},
    scenario_id=None,
    policy_tags=[]
)
```

### Score Defaults (NPE)

```python
Scores(
    risk=0.5,
    utility=0.5,
    cost=0.5,
    confidence=0.5
)
```

### Hadamard Matrix Orders (GLLL)

| Order | Size | Max Correctable Errors |
|-------|------|------------------------|
| H1 | 1x1 | 0 |
| H2 | 2x2 | 0 |
| H4 | 4x4 | 1 |
| H8 | 8x8 | 2 |
| H16 | 16x16 | 4 |
| H32 | 32x32 | 8 |
| H64 | 64x64 | 16 |
| H128 | 128x128 | 32 |

### Gate Status Levels (Coherence)

| Status | Description |
|--------|-------------|
| **optimal** | Coherence at maximum |
| **healthy** | Coherence within acceptable range |
| **acceptable** | Coherence at lower bound |
| **degraded** | Coherence below acceptable |
| **critical** | Coherence at minimum threshold |

### Trace Levels

| Level | Use Case |
|-------|----------|
| DEBUG | Development debugging |
| INFO | General information |
| WARNING | Unexpected but recoverable |
| ERROR | Failure requiring attention |
| CRITICAL | System-level failure |

### Receipt Decisions

| Decision | Meaning |
|----------|---------|
| PASS | Step succeeded |
| FAIL | Step failed |
| WARN | Step succeeded with warnings |
| SKIP | Step was skipped |
| PENDING | Step awaiting resolution |

---

## Related Documents

- [`Coherence_Spec_v1_0/docs/12_Glossary_and_Lexicon.md`](Coherence_Spec_v1_0/docs/12_Glossary_and_Lexicon.md) - Original glossary
- [`spec/seam/00_Seam_Principles.md`](spec/seam/00_Seam_Principles.md) - Seam architecture
- [`spec/ghll/01_Lexicon_and_Semantic_Atoms.md`](spec/ghll/01_Lexicon_and_Semantic_Atoms.md) - GHLL lexicon
- [`spec/glll/01_Hadamard_Basis_and_Glyph_Construction.md`](spec/glll/01_Hadamard_Basis_and_Glyph_Construction.md) - GLLL encoding
- [`src/cnsc/haai/ghll/lexicon.py`](src/cnsc/haai/ghll/lexicon.py) - Lexicon implementation
- [`src/cnsc/haai/nsc/gates.py`](src/cnsc/haai/nsc/gates.py) - Gate implementation
- [`src/npe/core/types.py`](src/npe/core/types.py) - NPE types
- [`src/npe/core/budgets.py`](src/npe/core/budgets.py) - Budget implementation

---

*End of Glossary and Lexicon*

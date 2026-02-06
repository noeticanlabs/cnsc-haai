# Coherence Framework Implementation Plan

## Executive Summary

This plan addresses the main gaps identified in the system review:
1. **GHLL/GLLL/NSC/GML Implementation** - Full compiler toolchain
2. **CLI/Tooling** - Command-line interface
3. **Integration Tests** - End-to-end validation
4. **Performance Testing** - Benchmarks
5. **Real-world Validation** - Deployment scenarios

The plan is organized into **8 phases** over approximately **16-24 weeks**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     GLLL (Glyphic Low-Level Language)           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Codebook    │  │ Hadamard    │  │ Packetizer  │            │
│  │ Management  │  │ Encoder     │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────┬───────────────────────────────────────┘
                          │ GLLL→GHLL Binding
┌─────────────────────────▼───────────────────────────────────────┐
│                     GHLL (Glyphic High-Level Language)          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Lexicon     │  │ Parser      │  │ Type System │            │
│  │ Manager     │  │ (EBNF)      │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────┬───────────────────────────────────────┘
                          │ GHLL→NSC Lowering
┌─────────────────────────▼───────────────────────────────────────┐
│                  NSC (Network Structured Code)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ CFA         │  │ Bytecode    │  │ Gate/Rail   │            │
│  │ Automaton   │  │ VM          │  │ Evaluator   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────┬───────────────────────────────────────┘
                          │ NSC→GML Receipt Emission
┌─────────────────────────▼───────────────────────────────────────┐
│                  GML (Governance Metadata Language)             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Trace       │  │ Receipt     │  │ Replay      │            │
│  │ Manager     │  │ Chain       │  │ Verifier    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                          │
                    ┌─────▼─────┐
                    │  CLI Tool │
                    │ (Unified) │
                    └───────────┘
```

---

## Phase 1: Foundation - GHLL Parser and Lexicon System

### Duration: 2-3 weeks

### Goals
Implement the core GHLL parsing infrastructure and lexicon management system.

### Deliverables

#### 1.1 Lexicon Module
- **File**: `src/cnsc/haai/ghll/lexicon.py`
- **Purpose**: Manage semantic atoms and parse forms
- **Classes**:
  - `LexiconEntry`: Single entry with parse form, semantics, receipt signature
  - `LexiconManager`: CRUD operations, lookup, validation
- **Key Features**:
  - Load/save lexicon from JSON
  - Semantic atom resolution
  - Parse form matching
  - Receipt signature generation

#### 1.2 Type System
- **File**: `src/cnsc/haai/ghll/types.py`
- **Purpose**: GHLL type system per spec
- **Classes**:
  - `GHLLType`: Base type class
  - `PrimitiveType`: bool, int, float, string, symbol
  - `CompositeType`: struct, union, sequence
  - `TypeRegistry`: Type catalog and validation
- **Key Features**:
  - Type checking and validation
  - Type inference
  - Type compatibility checking

#### 1.3 Parser
- **File**: `src/cnsc/haai/ghll/parser.py`
- **Purpose**: Parse GHLL source code per EBNF grammar
- **Classes**:
  - `GHLLParser`: Main parser class
  - `Token`: Token representation
  - `ParseError`: Structured error reporting
- **Key Features**:
  - EBNF-based recursive descent parser
  - Span/provenance tracking
  - Error recovery
  - Canonical form generation

#### 1.4 Unit Tests
- **File**: `tests/test_ghll_parser.py`
- Coverage: Parser, Lexicon, Type System

### Specifications Reference
- [`cnsc-haai/spec/ghll/01_Lexicon_and_Semantic_Atoms.md`](cnsc-haai/spec/ghll/01_Lexicon_and_Semantic_Atoms.md)
- [`cnsc-haai/spec/ghll/02_Grammar_EBNF.md`](cnsc-haai/spec/ghll/02_Grammar_EBNF.md)
- [`cnsc-haai/spec/ghll/03_Type_System.md`](cnsc-haai/spec/ghll/03_Type_System.md)

---

## Phase 2: NSC Compiler - Bytecode and VM Implementation

### Duration: 3-4 weeks

### Goals
Implement the NSC intermediate representation, bytecode compiler, and virtual machine.

### Deliverables

#### 2.1 NSC IR and Typing
- **File**: `src/cnsc/haai/nsc/ir.py`
- **Purpose**: NSC intermediate representation
- **Classes**:
  - `NSCProgram`: Complete program representation
  - `NSCRewrite`: Rewrite rule definition
  - `NSCCFG`: Control flow graph
  - `NSCType`: NSC type system
- **Key Features**:
  - SSA form representation
  - Type checking
  - CFG construction

#### 2.2 CFA Automaton
- **File**: `src/cnsc/haai/nsc/cfa.py`
- **Purpose**: Control Flow Automaton for phase enforcement
- **Classes**:
  - `CFAState`: Individual state node
  - `CFATransition`: Transition between states
  - `CFAAutomaton`: Complete automaton
- **Key Features**:
  - Phase state machine
  - Transition validation
  - PoC constraint enforcement

#### 2.3 Bytecode VM
- **File**: `src/cnsc/haai/nsc/vm.py`
- **Purpose**: Execute NSC bytecode
- **Classes**:
  - `BytecodeEmitter`: Generate bytecode from IR
  - `VM`: Stack-based virtual machine
  - `VMState`: VM execution state
- **Key Features**:
  - Stack-based bytecode interpreter
  - Deterministic execution
  - Receipt emission hooks

#### 2.4 Gate/Rail Evaluator
- **File**: `src/cnsc/haai/nsc/gates.py`
- **Purpose**: Gate and rail constraint evaluation
- **Classes**:
  - `GateEvaluator`: Gate condition evaluation
  - `RailEvaluator`: Rail constraint checking
  - `AffordabilityChecker`: Resource affordability
- **Key Features**:
  - Gate condition evaluation
  - Rail trajectory checking
  - Hysteresis handling

#### 2.5 Unit Tests
- **File**: `tests/test_nsc_compiler.py`
- Coverage: IR, CFA, VM, Gate evaluation

### Specifications Reference
- [`cnsc-haai/spec/nsc/02_Grammar_and_Parsing.md`](cnsc-haai/spec/nsc/02_Grammar_and_Parsing.md)
- [`cnsc-haai/spec/nsc/03_IR_and_Typing.md`](cnsc-haai/spec/nsc/03_IR_and_Typing.md)
- [`cnsc-haai/spec/nsc/04_Rewrite_Runtime_Model.md`](cnsc-haai/spec/nsc/04_Rewrite_Runtime_Model.md)
- [`cnsc-haai/spec/nsc/05_CFA_Flow_Automaton.md`](cnsc-haai/spec/nsc/05_CFA_Flow_Automaton.md)
- [`cnsc-haai/spec/nsc/06_Gates_Rails_Receipts.md`](cnsc-haai/spec/nsc/06_Gates_Rails_Receipts.md)
- [`cnsc-haai/spec/nsc/07_Bytecode_and_VM.md`](cnsc-haai/spec/nsc/07_Bytecode_and_VM.md)

---

## Phase 3: GML Runtime - Trace and Receipt System

### Duration: 2-3 weeks

### Goals
Implement the Governance Metadata Language runtime for tracing, receipts, and replay.

### Deliverables

#### 3.1 Trace Model
- **File**: `src/cnsc/haai/gml/trace.py`
- **Purpose**: Reasoning trace representation
- **Classes**:
  - `TraceEvent`: Single trace event
  - `TraceThread`: Thread of related events
  - `TraceManager`: Trace collection and query
- **Key Features**:
  - Event logging
  - Thread coupling
  - Query interface

#### 3.2 PhaseLoom Threads
- **File**: `src/cnsc/haai/gml/phaseloom.py`
- **Purpose**: PhaseLoom thread management
- **Classes**:
  - `PhaseLoom`: Thread container
  - `ThreadCoupling`: Thread relationship
  - `CouplingPolicy`: Coupling rules
- **Key Features**:
  - Thread creation and management
  - Coupling enforcement
  - Thread recovery

#### 3.3 Receipt Chain
- **File**: `src/cnsc/haai/gml/receipts.py`
- **Purpose**: Receipt chain management (enhanced from cnhaai)
- **Classes**:
  - `ReceiptChain`: Linked receipt list
  - `HashChain`: Cryptographic chain
  - `ChainValidator`: Receipt verification
- **Key Features**:
  - Hash chain construction
  - Signature verification
  - Chain integrity checking

#### 3.4 Replay Verifier
- **File**: `src/cnsc/haai/gml/replay.py`
- **Purpose**: Deterministic replay and verification
- **Classes**:
  - `ReplayEngine`: Replay execution
  - `Verifier`: Result verification
  - `Checkpoint`: Execution checkpoint
- **Key Features**:
  - Deterministic replay
  - Checkpoint creation/restoration
  - Result verification

#### 3.5 Unit Tests
- **File**: `tests/test_gml_runtime.py`
- Coverage: Trace, PhaseLoom, Receipt chains, Replay

### Specifications Reference
- [`cnsc-haai/spec/gml/01_Trace_Model.md`](cnsc-haai/spec/gml/01_Trace_Model.md)
- [`cnsc-haai/spec/gml/02_PhaseLoom_Threads_and_Couplings.md`](cnsc-haai/spec/gml/02_PhaseLoom_Threads_and_Couplings.md)
- [`cnsc-haai/spec/gml/03_Receipt_Spec_and_Hash_Chains.md`](cnsc-haai/spec/gml/03_Receipt_Spec_and_Hash_Chains.md)
- [`cnsc-haai/spec/gml/04_Checkpoints_and_Backtracking_Protocol.md`](cnsc-haai/spec/gml/04_Checkpoints_and_Backtracking_Protocol.md)
- [`cnsc-haai/spec/gml/05_Query_and_Audit_Language.md`](cnsc-haai/spec/gml/05_Query_and_Audit_Language.md)

---

## Phase 4: GLLL Codec - Hadamard Encoding/Decoding

### Duration: 2-3 weeks

### Goals
Implement the Glyphic Low-Level Language for error-tolerant binary encoding.

### Deliverables

#### 4.1 Hadamard Basis
- **File**: `src/cnsc/haai/glll/hadamard.py`
- **Purpose**: Hadamard basis construction and operations
- **Classes**:
  - `HadamardMatrix`: Hadamard matrix operations
  - `HadamardCodec`: Encode/decode with Hadamard
  - `ErrorDetector`: Error detection via syndromes
- **Key Features**:
  - Sylvester construction
  - Fast Walsh-Hadamard Transform
  - Syndrome calculation
  - Error correction (up to t errors)

#### 4.2 Codebook Management
- **File**: `src/cnsc/haai/glll/codebook.py`
- **Purpose**: Glyph codebook management
- **Classes**:
  - `Codebook`: Glyph-to-symbol mapping
  - `CodebookBuilder`: Codebook construction
  - `CodebookValidator`: Integrity checking
- **Key Features**:
  - Load/save codebook JSON
  - Glyph encoding/decoding
  - Distance calculation
  - Integrity verification

#### 4.3 Packetization
- **File**: `src/cnsc/haai/glll/packetizer.py`
- **Purpose**: Data packetization for transmission
- **Classes**:
  - `Packet`: Transmission packet
  - `Packetizer`: Data segmentation
  - `Depacketizer`: Data reassembly
- **Key Features**:
  - Fixed-size packet creation
  - Sequence numbering
  - Checksum validation
  - Reassembly

#### 4.4 GLLL→GHLL Mapping
- **File**: `src/cnsc/haai/glll/mapping.py`
- **Purpose**: Map GLLL to GHLL semantic atoms
- **Classes**:
  - `GlyphMapper`: Glyph to token mapping
  - `SymbolResolver`: Symbol resolution
  - `BindingValidator`: Binding verification
- **Key Features**:
  - Deterministic mapping
  - Error tolerance
  - Binding validation

#### 4.5 Unit Tests
- **File**: `tests/test_glll_codec.py`
- Coverage: Hadamard, Codebook, Packetizer, Mapping

### Specifications Reference
- [`cnsc-haai/spec/glll/01_Hadamard_Basis_and_Glyph_Construction.md`](cnsc-haai/spec/glll/01_Hadamard_Basis_and_Glyph_Construction.md)
- [`cnsc-haai/spec/glll/02_Codebook_Format.md`](cnsc-haai/spec/glll/02_Codebook_Format.md)
- [`cnsc-haai/spec/glll/03_Distance_Metrics_and_Error_Tolerance.md`](cnsc-haai/spec/glll/03_Distance_Metrics_and_Error_Tolerance.md)
- [`cnsc-haai/spec/glll/04_Encoding_Decoding_Algorithms.md`](cnsc-haai/spec/glll/04_Encoding_Decoding_Algorithms.md)
- [`cnsc-haai/spec/glll/05_Transport_Packetization.md`](cnsc-haai/spec/glll/05_Transport_Packetization.md)
- [`cnsc-haai/spec/glll/06_GLLL_to_GHLL_Mapping.md`](cnsc-haai/spec/glll/06_GLLL_to_GHLL_Mapping.md)

---

## Phase 5: CLI Tools - Command Line Interface

### Duration: 2 weeks

### Goals
Implement unified command-line interface for the entire toolchain.

### Deliverables

#### 5.1 Unified CLI
- **File**: `src/cnsc/haai/cli/main.py`
- **Purpose**: Main CLI entry point
- **Commands**:
  - `parse`: Parse GHLL source
  - `compile`: Compile to NSC bytecode
  - `run`: Execute bytecode
  - `trace`: Run with full tracing
  - `replay`: Replay a trace
  - `verify`: Verify receipt chain
  - `encode`: Encode to GLLL
  - `decode`: Decode from GLLL
  - `lexicon`: Manage lexicon
  - `codebook`: Manage codebook

#### 5.2 Subcommands Implementation
- **File**: `src/cnsc/haai/cli/commands.py`
- **Purpose**: CLI subcommand implementations

#### 5.3 Configuration
- **File**: `src/cnsc/haai/cli/config.py`
- **Purpose**: CLI configuration management

#### 5.4 Man Pages
- **File**: `docs/man/`
- **Purpose**: Unix man page documentation

### Specifications Reference
- [`cnsc-haai/spec/nsc/09_CLI_and_Tooling.md`](cnsc-haai/spec/nsc/09_CLI_and_Tooling.md)

---

## Phase 6: Integration Tests - End-to-End Validation

### Duration: 2-3 weeks

### Goals
Write comprehensive integration tests covering the full toolchain.

### Deliverables

#### 6.1 End-to-End Tests
- **File**: `tests/integration/test_full_pipeline.py`
- **Tests**:
  - GLLL→GHLL→NSC→GML full pipeline
  - Receipt chain verification
  - Deterministic replay
  - Error injection and recovery

#### 6.2 Seam Contract Tests
- **File**: `tests/integration/test_seams.py`
- **Tests**:
  - GLLL→GHLL binding contract
  - GHLL→NSC lowering contract
  - NSC→GML receipt emission contract

#### 6.3 Compliance Tests Migration
- **File**: `tests/compliance/`
- **Purpose**: Migrate cnsc-haai compliance tests to pytest format

#### 6.4 Golden Artifacts
- **File**: `tests/artifacts/`
- **Purpose**: Reference outputs for comparison
  - Golden parses
  - Golden bytecode
  - Golden traces
  - Golden receipts

### Specifications Reference
- [`cnsc-haai/compliance_tests/`](cnsc-haai/compliance_tests/)

---

## Phase 7: Performance Benchmarking

### Duration: 1-2 weeks

### Goals
Establish performance baselines and benchmarks.

### Deliverables

#### 7.1 Benchmark Suite
- **File**: `benchmarks/`
- **Benchmarks**:
  - GHLL parsing throughput
  - NSC compilation speed
  - VM execution speed
  - GLLL encoding/decoding speed
  - Receipt chain verification speed
  - Memory usage profiles

#### 7.2 Profiling Tools
- **File**: `benchmarks/profiler.py`
- **Purpose**: CPU and memory profiling

#### 7.3 Performance Reports
- **File**: `docs/performance/`
- **Purpose**: Performance analysis documents

### Key Metrics to Track
| Component | Metric | Target |
|-----------|--------|--------|
| GHLL Parser | Lines/second | >10,000 |
| NSC Compiler | Functions/second | >1,000 |
| VM Execution | Instructions/second | >100,000 |
| GLLL Codec | Glyphs/second | >50,000 |
| Receipt Verification | Receipts/second | >10,000 |

---

## Phase 8: Documentation and Examples

### Duration: 1-2 weeks (ongoing)

### Goals
Complete documentation and working examples.

### Deliverables

#### 8.1 API Documentation
- **File**: `docs/api/`
- **Tool**: Sphinx with autodoc
- **Coverage**: 100% public API

#### 8.2 Tutorials
- **File**: `docs/tutorials/`
- **Tutorials**:
  - Quick Start Guide
  - Writing GHLL Programs
  - Building Custom Gates
  - Using the Receipt System
  - GLLL Encoding Guide

#### 8.3 Working Examples
- **File**: `examples/`
- **Examples**:
  - Simple GHLL program
  - Custom gate implementation
  - Full pipeline demo
  - Error recovery demo
  - Audit trail demo

#### 8.4 Architecture Guide
- **File**: `docs/architecture.md`
- **Purpose**: High-level architecture documentation

---

## File Structure

After implementation, the project structure will be:

```
cnsc-haai/
├── src/
│   └── cnsc/haai/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── commands.py
│       │   └── config.py
│       ├── ghll/
│       │   ├── __init__.py
│       │   ├── lexicon.py
│       │   ├── types.py
│       │   └── parser.py
│       ├── nsc/
│       │   ├── __init__.py
│       │   ├── ir.py
│       │   ├── cfa.py
│       │   ├── vm.py
│       │   └── gates.py
│       ├── gml/
│       │   ├── __init__.py
│       │   ├── trace.py
│       │   ├── phaseloom.py
│       │   ├── receipts.py
│       │   └── replay.py
│       └── glll/
│           ├── __init__.py
│           ├── hadamard.py
│           ├── codebook.py
│           ├── packetizer.py
│           └── mapping.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_ghll_parser.py
│   │   ├── test_nsc_compiler.py
│   │   ├── test_gml_runtime.py
│   │   └── test_glll_codec.py
│   ├── integration/
│   │   ├── test_full_pipeline.py
│   │   └── test_seams.py
│   ├── compliance/
│   │   └── (migrated tests)
│   └── artifacts/
│       ├── golden_parses/
│       ├── golden_bytecode/
│       └── golden_traces/
├── benchmarks/
│   ├── __init__.py
│   ├── test_benchmarks.py
│   └── profiler.py
├── docs/
│   ├── api/
│   ├── tutorials/
│   ├── man/
│   └── performance/
├── examples/
│   ├── simple_ghll_program.py
│   ├── custom_gates.py
│   ├── full_pipeline_demo.py
│   └── audit_trail_demo.py
└── pyproject.toml
```

---

## Dependencies

### Python Version
- Python 3.10+

### Core Dependencies
```toml
[project.requires-python]
requires-python = ">=3.10"

[project.dependencies]
pydantic = ">=2.0"  # Schema validation
click = ">=8.0"     # CLI framework
rich = ">=13.0"     # Terminal output
pyyaml = ">=6.0"    # YAML parsing
```

### Development Dependencies
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-benchmark>=4.0",
    "black>=23.0",
    "mypy>=1.0",
    "flake8>=6.0",
    "sphinx>=7.0",
    "sphinx-autodoc-typehints",
]
```

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complexity creep | High | Stick to specs, add features in phases |
| Performance issues | Medium | Early benchmarking, optimization passes |
| Specification gaps | Medium | Reference existing cnhaai implementation |
| Integration failures | High | Comprehensive integration tests |

---

## Success Criteria

### Phase Completion
- [ ] All unit tests pass (>90% coverage)
- [ ] All compliance tests pass
- [ ] All integration tests pass
- [ ] Performance targets met
- [ ] Documentation complete

### Final Release
- [ ] Full GLLL→GHLL→NSC→GML pipeline working
- [ ] CLI tool fully functional
- [ ] Deterministic replay verified
- [ ] Performance benchmarks established
- [ ] Working examples for all features

---

## Timeline

```
Week  1-3:  Phase 1 - GHLL Parser and Lexicon
Week  4-7:  Phase 2 - NSC Compiler and VM
Week  8-10: Phase 3 - GML Runtime
Week 11-13: Phase 4 - GLLL Codec
Week 14-15: Phase 5 - CLI Tools
Week 16-18: Phase 6 - Integration Tests
Week 19-20: Phase 7 - Performance Benchmarking
Week 21-22: Phase 8 - Documentation and Examples
```

**Total Estimated Time: 16-22 weeks**

---

## Next Steps

1. Review and approve this plan
2. Begin Phase 1 implementation
3. Set up CI/CD pipeline
4. Establish code review process
5. Schedule weekly progress reviews

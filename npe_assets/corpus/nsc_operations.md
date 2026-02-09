# Neural-Symbolic Core Operations

## Architecture Overview

The Neural-Symbolic Core (NSC) is the execution engine that processes GHLL programs and produces verified GML traces. It combines neural capabilities with symbolic reasoning.

## Core Components

### Parser Module

Translates GHLL source into an intermediate representation:
- Lexical analysis of the input stream
- Syntactic parsing according to grammar rules
- Semantic validation against type system
- Output: Abstract Syntax Tree (AST)

### Control Flow Automaton (CFA)

Models program flow and enables analysis:
- Builds control flow graph from AST
- Identifies all possible execution paths
- Enables static analysis of program behavior
- Supports reachability queries

### Gate System

Enforces runtime constraints:
- **Affordance Gates** - Resource limits
- **Coherence Gates** - Consistency checks
- **Security Gates** - Safety boundaries
- Each gate can pass, fail, or require repair

### Receipt Generator

Creates verifiable audit trail:
- Records every significant operation
- Chains receipts via cryptographic hashes
- Enables replay and verification
- Supports dispute resolution

## Execution Phases

### Phase 1: Parse

```
Source Code → Lexer → Parser → AST
```

### Phase 2: Analyze

```
AST → CFA Build → Gate Setup → Type Check
```

### Phase 3: Execute

```
Instructions → Gate Evaluation → Receipt Emission
```

### Phase 4: Verify

```
Receipt Chain → Hash Verification → Coherence Check
```

## Gate Evaluation Lifecycle

1. **Pre-Execution** - Gates initialized with policy
2. **During Execution** - Gates evaluate each operation
3. **On Failure** - Repair proposer invoked
4. **Post-Execution** - All gates verified as passing

## Error Handling

The NSC implements a hierarchy of error handling:

| Level | Type | Response |
|-------|------|----------|
| Recoverable | Affordability | Repair proposal |
| Recoverable | Coherence | Repair proposal |
| Fatal | Security | Immediate termination |
| Fatal | Type | Parse rejection |

## Performance Characteristics

- **Parse Time**: O(n) for input length n
- **CFA Build**: O(b) for basic blocks b
- **Gate Eval**: O(g × o) for g gates, o operations
- **Receipt Gen**: O(r) for receipts r

Memory usage scales linearly with trace complexity.

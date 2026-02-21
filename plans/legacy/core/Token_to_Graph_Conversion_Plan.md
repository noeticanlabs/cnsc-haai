# Plan: Convert Token Class to Graph-Based Semantic Units

## Objective
Transform the linear Token-based parser architecture into a graph-based representation where semantic units are nodes with explicit relationships, supporting richer structural analysis and coherence verification.

## Background

The current GHLL parser uses:
- `TokenType` enum for token classification
- `Token` dataclass for lexical units
- `Tokenizer` for linear tokenization
- `GHLLParser` for recursive descent parsing

### Problem with Linear Token Model
1. Tokens have no explicit relationships to other tokens
2. Structural hierarchy is implicit in AST construction
3. No direct representation of spans, dependencies, or provenance
4. Difficult to verify coherence across token boundaries

### Graph-Based Model Benefits
1. **Explicit Relationships**: Tokens know their neighbors, parents, and semantic connections
2. **Span Graph**: Rich representation of text ranges and their overlaps
3. **Provenance Tracking**: Direct links between source positions and derived structures
4. **Coherence Verification**: Graph traversal enables cross-token constraint checking

## Proposed Graph-Based Architecture

### Node Types

```
SemanticNode (Abstract Base)
├── TokenNode: Leaf lexical units
├── SpanNode: Text ranges with positional metadata
├── ExpressionNode: Binary operations, function calls
├── StatementNode: Control flow, assignments, assertions
├── DefinitionNode: Variable/function/type declarations
└── ModuleNode: Top-level compilation unit
```

### Edge Types

```
Relationship (Abstract)
├── PARENT_CHILD: Hierarchical AST structure
├── SIBLING: Sequential ordering within same parent
├── SPAN_LINK: Token-to-span membership
├── DEPENDENCY: Data/control flow between nodes
├── PROVENANCE: Source position tracking
└── COHERENCE: Constraint enforcement links
```

### Core Data Structures

```python
# SpanGraph: Main graph container
class SpanGraph:
    nodes: Dict[NodeId, SemanticNode]
    edges: Dict[NodeId, List[Relationship]]
    spans: Dict[Span, NodeId]  # Reverse lookup
    root: NodeId

# SemanticUnit: Graph node base class
class SemanticUnit:
    node_id: NodeId
    span: Optional[Span]
    type: SemanticType
    attributes: Dict[str, Any]
    provenance: ProvenanceInfo
```

## Implementation Phases

### Phase 1: Foundation (Week 1)
1. Create `semantic_unit.py` with base `SemanticUnit` and `SemanticType` enum
2. Define `SpanGraph` container class with edge management
3. Implement `Span` and `ProvenanceInfo` value objects
4. Create `Relationship` edge types with validation

### Phase 2: Token Migration (Week 2)
1. Rename `TokenType` to `LexicalType` in `parser.py`
2. Create `TokenNode` subclass of `SemanticUnit`
3. Migrate `Token` attributes to `TokenNode`
4. Update `Tokenizer` to emit `TokenNode` instances into `SpanGraph`

### Phase 3: Span Graph Construction (Week 3)
1. Implement `SpanBuilder` for incremental span creation
2. Add `SpanExtractor` for populating span graphs from tokens
3. Create `SpanGraphSerializer` for persistence
4. Implement span overlap detection and resolution

### Phase 4: Parser Integration (Week 4)
1. Update `GHLLParser` to use `SpanGraph` instead of AST
2. Add graph traversal utilities (pre-order, post-order, level-order)
3. Implement parent/child edge management during parsing
4. Add sibling edge linking for sequential statements

### Phase 5: Advanced Graph Features (Week 5)
1. Implement `DependencyAnalyzer` for data flow analysis
2. Create `CoherenceVerifier` for cross-node constraint checking
3. Add `ProvenanceTracker` for source mapping
4. Implement graph diff and merge operations

### Phase 6: Testing & Documentation (Week 6)
1. Write unit tests for all new classes
2. Create integration tests with existing parser tests
3. Document graph traversal patterns
4. Write migration guide for AST-based code

## File Changes

### New Files
- `src/cnsc/haai/ghll/semantic_unit.py` - Core graph types
- `src/cnsc/haai/ghll/span_graph.py` - SpanGraph implementation
- `src/cnsc/haai/ghll/provenance.py` - Provenance tracking
- `src/cnsc/haai/ghll/traversal.py` - Graph traversal utilities

### Modified Files
- `src/cnsc/haai/ghll/parser.py` - Migrate Token to TokenNode
- `src/cnsc/haai/ghll/lexer.py` (new) - Extract from parser.py
- `src/cnsc/haai/ghll/types.py` - Update type definitions

### Deprecated Files
- `src/cnsc/haai/ghll/parser.py` - Remove Token class (after migration)

## Backward Compatibility

1. Provide `Token` alias for `TokenNode` during transition period
2. Add `to_ast()` method to `SpanGraph` for legacy compatibility
3. Maintain existing `GHLLParser` interface with adapter pattern
4. Version schema for serialized span graphs

## Success Criteria

1. [ ] All existing parser tests pass with graph-based implementation
2. [ ] SpanGraph can reconstruct equivalent AST from any parse
3. [ ] Provenance tracking provides full source-to-node mapping
4. [ ] Graph traversal performance within 2x of AST performance
5. [ ] Documentation covers migration and graph patterns

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Performance regression | Benchmark-driven development; optimize hot paths |
| Complex migration | Incremental migration with feature flags |
| API breakage | Provide adapters and aliases for deprecated APIs |
| Graph size blow-up | Implement lazy loading and pruning strategies |

## Timeline

```
Week 1: Foundation
Week 2: Token Migration  
Week 3: Span Graph Construction
Week 4: Parser Integration
Week 5: Advanced Features
Week 6: Testing & Documentation
```

Total: 6 weeks for complete implementation

# NPE Index Build Documentation

This document describes how to build the search index for NPE retrieval.

## Overview

The NPE uses a chunked index to enable fast retrieval of relevant corpus documents and codebooks during proposal generation.

## Index Types

### Corpus Index
- **Purpose**: Full-text search over corpus documents
- **Chunk Size**: 1200 characters
- **Overlap**: 200 characters
- **Location**: `npe_assets/corpus/`

### Codebook Index
- **Purpose**: Structured lookup for repair maps, templates, and rules
- **Format**: YAML with typed fields
- **Location**: `npe_assets/codebooks/`

### Receipt Index
- **Purpose**: Historical search for similar past failures
- **Format**: JSONL with structured fields
- **Location**: `npe_assets/receipts/`

## Building the Index

### Prerequisites

```bash
# Install NPE dependencies
pip install -e src/npe/

# Verify corpus files exist
ls -la npe_assets/corpus/
ls -la npe_assets/codebooks/
```

### Using the Index Builder

```python
from npe.retrieval.index_build import build_all_indices

# Build all indices
build_all_indices(
    corpus_path="npe_assets/corpus",
    codebooks_path="npe_assets/codebooks",
    receipts_path="npe_assets/receipts",
    output_path="npe_assets/index"
)
```

### Manual Index Construction

```python
from npe.retrieval.corpus_store import CorpusStore
from npe.retrieval.codebook_store import CodebookStore
from npe.retrieval.receipts_store import ReceiptsStore

# Build corpus index
corpus = CorpusStore()
for filepath in corpus_path.glob("*.md"):
    with open(filepath) as f:
        corpus.add_file(str(filepath), f.read())

# Build codebook index
codebooks = CodebookStore()
for filepath in codebooks_path.glob("**/*.yaml"):
    codebooks.load_codebook(str(filepath))

# Build receipt index
receipts = ReceiptsStore()
for filepath in receipts_path.glob("*.jsonl"):
    receipts.load_receipts(str(filepath))
```

## Index Structure

```
npe_assets/index/
├── corpus/
│   ├── chunks/          # Chunk data files
│   └── inverted.json    # Inverted index for search
├── codebooks/
│   ├── repair_map.json  # Repair strategy mappings
│   ├── templates.json   # Plan templates
│   └── rules.json       # Safety rules
└── receipts/
    └── index.jsonl      # Receipt lookup index
```

## Search Usage

### Corpus Search

```python
from npe.retrieval.query import query_corpus

# Search for relevant reasoning patterns
results = query_corpus(
    "gate repair strategies for affordability failures",
    top_k=5
)
```

### Codebook Lookup

```python
from npe.retrieval.query import lookup_repair_strategies

# Get repair strategies for a failure type
strategies = lookup_repair_strategies(
    failure_type="affordability_failure"
)
```

### Receipt Search

```python
from npe.retrieval.query import search_receipts

# Find similar past failures
matches = search_receipts(
    gate_id="cpu_budget",
    limit=3
)
```

## Index Maintenance

### Rebuilding

```bash
# Full rebuild
python -m npe.retrieval.index_build --rebuild

# Incremental update
python -m npe.retrieval.index_build --update
```

### Validation

```bash
# Validate index integrity
python -m npe.retrieval.index_build --validate
```

## Performance Considerations

- Index build time scales with corpus size
- For large corpora, consider incremental indexing
- Memory usage: ~2x corpus size for full index
- Search latency: O(log n) for typical queries

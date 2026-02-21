# CLI Reference

**Status:** Canonical

## Overview

The CNHAAI CLI (`cnsc-haai`) provides command-line access to all system functionality including parsing, compilation, execution, and audit.

## Usage

```bash
cnsc-haai <command> [options] [arguments]
```

## Global Options

| Option | Description |
|--------|-------------|
| `--help, -h` | Show help message |
| `--version` | Show version |
| `--verbose, -v` | Enable verbose output |
| `--quiet, -q` | Suppress non-essential output |

## Commands

### parse

Parse GHLL source code and output AST.

```bash
cnsc-haai parse <input> [options]
```

| Argument | Description |
|----------|-------------|
| `input` | Input source file (default: stdin) |

| Option | Description |
|--------|-------------|
| `--output, -o` | Output file |
| `--format` | Output format: `json`, `yaml`, `text` (default: json) |
| `--type-check` | Enable type checking |

**Example:**
```bash
cnsc-haai parse example.ghll --format json --output ast.json
```

---

### compile

Compile GHLL source to NSC bytecode.

```bash
cnsc-haai compile <input> [options]
```

| Argument | Description |
|----------|-------------|
| `input` | Input source file (default: stdin) |

| Option | Description |
|--------|-------------|
| `--output, -o` | **Required** - Output file for bytecode |
| `--entry` | Entry point function (default: main) |

**Example:**
```bash
cnsc-haai compile example.ghll --output example.nsc --entry main
```

---

### run

Execute NSC bytecode.

```bash
cnsc-haai run <input> [options]
```

| Argument | Description |
|----------|-------------|
| `input` | Bytecode input file |

| Option | Description |
|--------|-------------|
| `--trace` | Enable execution tracing |
| `--trace-output` | Output file for trace |
| `--receipt` | Output file for receipt |

**Example:**
```bash
cnsc-haai run example.nsc --trace --receipt receipt.json
```

---

### trace

Execute with full GML tracing.

```bash
cnsc-haai trace <input> [options]
```

| Argument | Description |
|----------|-------------|
| `input` | Input source file (default: stdin) |

| Option | Description |
|--------|-------------|
| `--output, -o` | Output file for trace |
| `--receipt` | Output file for receipt |

**Example:**
```bash
cnsc-haai trace example.ghll --output trace.json --receipt receipt.json
```

---

### replay

Replay execution from a trace file.

```bash
cnsc-haai replay <trace> [options]
```

| Argument | Description |
|----------|-------------|
| `trace` | Trace file to replay |

| Option | Description |
|--------|-------------|
| `--verify` | Verify replay against original |
| `--output, -o` | Output file for replay result |

**Example:**
```bash
cnsc-haai replay trace.json --verify --output result.json
```

---

### verify

Verify receipt chain integrity.

```bash
cnsc-haai verify <receipt> [options]
```

| Argument | Description |
|----------|-------------|
| `receipt` | Receipt file or episode ID |

| Option | Description |
|--------|-------------|
| `--verbose, -v` | Show detailed verification info |

**Example:**
```bash
cnsc-haai verify receipt.json --verbose
```

---

### encode

Encode data to GLLL Hadamard format.

```bash
cnsc-haai encode <input> [options]
```

| Argument | Description |
|----------|-------------|
| `input` | Input file (default: stdin) |

| Option | Description |
|--------|-------------|
| `--output, -o` | Output file (default: stdout) |
| `--codebook` | Codebook file to use |
| `--order` | Hadamard matrix order (default: 32) |

**Example:**
```bash
cnsc-haai encode data.txt --codebook my-codebook.json --output encoded.bin
```

---

### decode

Decode from GLLL Hadamard format.

```bash
cnsc-haai decode <input> [options]
```

| Argument | Description |
|----------|-------------|
| `input` | Input file (Hadamard encoded) |

| Option | Description |
|--------|-------------|
| `--output, -o` | Output file (default: stdout) |
| `--codebook` | Codebook file to use |
| `--order` | Hadamard matrix order (default: 32) |

**Example:**
```bash
cnsc-haai decode encoded.bin --codebook my-codebook.json --output decoded.txt
```

---

### lexicon

Manage lexicon operations.

```bash
cnsc-haai lexicon <operation> [options]
```

#### Operations

**create** - Create new lexicon

```bash
cnsc-haai lexicon create --output <file> [options]
```

| Option | Description |
|--------|-------------|
| `--output, -o` | **Required** - Output file |
| `--name` | Lexicon name (default: Default Lexicon) |

**validate** - Validate lexicon

```bash
cnsc-haai lexicon validate <file>
```

**export** - Export lexicon entries

```bash
cnsc-haai lexicon export <file> [options]
```

| Option | Description |
|--------|-------------|
| `--format` | Export format: `json`, `csv` (default: json) |

**Example:**
```bash
cnsc-haai lexicon create --output lexicon.json --name "My Lexicon"
cnsc-haai lexicon validate lexicon.json
cnsc-haai lexicon export lexicon.json --format csv --output lexicon.csv
```

---

### codebook

Manage codebook operations.

```bash
cnsc-haai codebook <operation> [options]
```

#### Operations

**create** - Create new codebook

```bash
cnsc-haai codebook create --output <file> [options]
```

| Option | Description |
|--------|-------------|
| `--output, -o` | **Required** - Output file |
| `--name` | Codebook name (default: Default Codebook) |

**add** - Add glyph to codebook

```bash
cnsc-haai codebook add <file> --symbol <symbol> [options]
```

| Option | Description |
|--------|-------------|
| `--symbol` | **Required** - Symbol to add |
| `--type` | Glyph type: `data`, `control`, `sync`, `parity` |
| `--category` | Category: `atom`, `operator`, `delimiter`, `literal`, `keyword` |

**validate** - Validate codebook

```bash
cnsc-haai codebook validate <file>
```

**export** - Export codebook

```bash
cnsc-haai codebook export <file> [options]
```

| Option | Description |
|--------|-------------|
| `--format` | Export format: `json`, `csv` (default: json) |

**Example:**
```bash
cnsc-haai codebook create --output codebook.json
cnsc-haai codebook add codebook.json --symbol "A" --type data --category literal
cnsc-haai codebook validate codebook.json
```

---

### gate

Manage gate policy operations.

```bash
cnsc-haai gate <operation> [options]
```

#### Operations

**create** - Create new gate policy

```bash
cnsc-haai gate create --output <file> [options]
```

| Option | Description |
|--------|-------------|
| `--output, -o` | **Required** - Output file |
| `--name` | Policy name (default: Default Policy) |

**add** - Add gate to policy

```bash
cnsc-haai gate add <file> --name <name> --type <type> [options]
```

| Option | Description |
|--------|-------------|
| `--name` | **Required** - Gate name |
| `--type` | **Required** - Gate type: `hard`, `soft` |
| `--threshold` | **Required** - Threshold value (0.0-1.0) |

**validate** - Validate gate policy

```bash
cnsc-haai gate validate <file>
```

**Example:**
```bash
cnsc-haai gate create --output gates.json
cnsc-haai gate add gates.json --name evidence_sufficiency --type hard --threshold 0.8
cnsc-haai gate validate gates.json
```

---

### serve (NPE)

Start the NPE (Neuro-Proposition Engine) HTTP service.

```bash
cnsc-haai serve [options]
```

| Option | Description |
|--------|-------------|
| `--port` | Port to bind to (default: 8080) |
| `--socket` | Unix socket path (optional, for socket mode) |
| `--registry` | Path to registry manifest (optional) |
| `--index` | Path to corpus index (optional) |

**Examples:**

```bash
# Start on TCP port 8080
cnsc-haai serve --port 8080

# Start on Unix socket
cnsc-haai serve --socket /tmp/npe.sock

# With custom registry
cnsc-haai serve --registry /path/to/manifest.yaml
```

**NPE Service Assets:**

The NPE service uses assets from `npe_assets/`:
- Codebooks: `npe_assets/codebooks/`
- Corpus: `npe_assets/corpus/`
- Receipts: `npe_assets/receipts/`

Build corpus index:
```bash
npe build-index --corpus npe_assets/corpus --output npe_assets/index
```

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/propose` | POST | Submit a proposal request |
| `/repair` | POST | Submit a repair request |

---

### version

Show version information.

```bash
cnsc-haai version
```

---

### help

Show help for a specific command.

```bash
cnsc-haai help <command>
```

**Example:**
```bash
cnsc-haai help parse
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | File not found |
| 4 | Parse error |
| 5 | Type error |
| 6 | Runtime error |
| 7 | Verification failed |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CNHAAI_HOME` | CNHAAI home directory |
| `CNHAAI_CODEBOOK` | Default codebook file |
| `CNHAAI_LEXICON` | Default lexicon file |
| `CNHAAI_GATES` | Default gate policy file |

## See Also

- Implementation: [`src/cnsc/haai/cli/commands.py`](src/cnsc/haai/cli/commands.py)
- Spec: [`spec/nsc/09_CLI_and_Tooling.md`](spec/nsc/09_CLI_and_Tooling.md)

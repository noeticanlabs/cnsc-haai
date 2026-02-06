# CNHAAI Development Requirements

## System Requirements

| Component | Minimum Version | Recommended Version |
|-----------|-----------------|---------------------|
| Python | 3.10+ | 3.11 |
| OS | Linux/macOS/Windows | Linux (Ubuntu 22.04+) |
| Memory | 4 GB RAM | 8 GB RAM |
| Storage | 500 MB | 1 GB |

## Python Version

CNHAAI requires **Python 3.10 or higher**. Python 3.11 is recommended for optimal performance.

```bash
# Check Python version
python --version  # Should show 3.10+
```

## Dependencies

### Core Dependencies

CNHAAI is a framework with minimal external dependencies to maintain portability and auditability.

| Package | Version | Purpose |
|---------|---------|---------|
| setuptools | >=61.0 | Build system |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=7.0 | Testing framework |
| pytest-cov | >=4.0 | Coverage reporting |
| black | >=23.0 | Code formatting |
| mypy | >=1.0 | Static type checking |
| flake8 | >=6.0 | Linting |

## Installation Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/coherenceframework/cnhaai.git
cd cnhaai
```

### 2. Create Virtual Environment

```bash
# Using venv (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Using uv (faster alternative)
uv venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install with pip
pip install -e ".[dev]"

# Using uv
uv pip install -e ".[dev]"
```

### 4. Verify Installation

```bash
# Run tests
pytest

# Check code formatting
black --check .

# Run type checking
mypy .

# Run linter
flake8 .
```

## Configuration Options

### pytest Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### black Configuration

```toml
[tool.black]
line-length = 100
target-version = ['py310']
```

### mypy Configuration

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

## Development Tools

### IDE Recommendations

#### VS Code

Recommended extensions:
- `ms-python.python`
- `ms-python.black-formatter`
- `njpwerner.blackd`
- `dbaeumer.vscode-eslint`

#### Neovim

Plugins:
- `null-ls.nvim` (linting, formatting)
- `mason.nvim` (LSP support)
- `nvim-lspconfig` (LSP configuration)

### Nix Development Shell

For reproducible environments, use the provided `dev.nix`:

```bash
nix-shell
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cnhaai

# Run specific test file
pytest tests/test_core.py

# Run specific test class
pytest tests/test_core.py::TestCoherence

# Run specific test
pytest tests/test_core.py::TestCoherence::test_coherence_check
```

### Writing Tests

Tests should be placed in the `tests/` directory following the naming convention `test_*.py`.

```python
import pytest
from cnhaai.core.coherence import Coherence

class TestCoherence:
    def test_coherence_check(self):
        coherence = Coherence()
        assert coherence.check() is True
```

## Code Quality

### Formatting

```bash
# Format code
black .

# Check formatting
black --check .
```

### Type Checking

```bash
# Run mypy
mypy .

# Run with specific configuration
mypy --config-file pyproject.toml
```

### Linting

```bash
# Run flake8
flake8 .

# With specific rules
flake8 --select=E,F,W --ignore=E501 .
```

## Virtual Environment Management

### Using venv

```bash
# Create
python -m venv .venv

# Activate
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Deactivate
deactivate

# Remove
rm -rf .venv
```

### Using uv (Recommended for Speed)

```bash
# Install uv
pip install uv

# Create environment
uv venv

# Install dependencies
uv pip install -e ".[dev]"

# Sync dependencies
uv pip sync
```

## Troubleshooting

### Common Issues

1. **Python version too old**
   ```
   Error: requires-python constraint not met
   ```
   Solution: Upgrade to Python 3.10+

2. **Module not found after installation**
   ```
   ModuleNotFoundError: No module named 'cnhaai'
   ```
   Solution: Ensure virtual environment is activated and reinstall with `pip install -e .`

3. **pytest not finding tests**
   ```
   ERROR: no tests collected
   ```
   Solution: Ensure tests are in `tests/` directory and named `test_*.py`

4. **black formatting conflicts**
   ```
   File contains unexpected changes
   ```
   Solution: Run `black .` to auto-format before committing

"""
CNSC-HAAI CLI Package

Command-line interface for the Coherence Framework.

Modules:
- main: Main CLI entry point
- commands: Subcommand implementations
- config: Configuration management
"""

from cnsc.haai.cli.main import main
from cnsc.haai.cli.config import CLIConfig, load_config, save_config

__all__ = [
    "main",
    "CLIConfig",
    "load_config",
    "save_config",
]

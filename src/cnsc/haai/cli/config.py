"""
CLI Configuration

Configuration management for the CLI.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path
import json
import os


@dataclass
class CLIConfig:
    """CLI Configuration."""

    # General settings
    verbose: int = 0
    quiet: int = 0
    interactive: bool = False

    # Parse settings
    parse_format: str = "json"
    parse_type_check: bool = False

    # Compile settings
    compile_entry: str = "main"
    compile_optimize: bool = False

    # Run settings
    run_trace: bool = False
    run_gates: bool = True

    # Trace settings
    trace_output: Optional[str] = None
    trace_receipt: Optional[str] = None

    # Encode/Decode settings
    encode_order: int = 32
    encode_codebook: Optional[str] = None

    # Paths
    config_dir: Path = field(default_factory=lambda: Path("~/.cnsc-haai"))
    data_dir: Path = field(default_factory=lambda: Path("~/.local/share/cnsc-haai"))

    def load(self, filepath: Optional[str] = None) -> None:
        """Load configuration from file."""
        path = Path(filepath) if filepath else self.config_dir / "config.json"

        if path.exists():
            with open(path) as f:
                data = json.load(f)
            self._apply_dict(data)

    def save(self, filepath: Optional[str] = None) -> None:
        """Save configuration to file."""
        path = Path(filepath) if filepath else self.config_dir / "config.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def _apply_dict(self, data: Dict[str, Any]) -> None:
        """Apply dictionary to config."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "verbose": self.verbose,
            "quiet": self.quiet,
            "interactive": self.interactive,
            "parse_format": self.parse_format,
            "parse_type_check": self.parse_type_check,
            "compile_entry": self.compile_entry,
            "compile_optimize": self.compile_optimize,
            "run_trace": self.run_trace,
            "run_gates": self.run_gates,
            "trace_output": self.trace_output,
            "trace_receipt": self.trace_receipt,
            "encode_order": self.encode_order,
            "encode_codebook": self.encode_codebook,
        }

    @classmethod
    def default(cls) -> "CLIConfig":
        """Get default configuration."""
        # Expand user paths
        config = cls()
        config.config_dir = Path(os.path.expanduser("~/.cnsc-haai"))
        config.data_dir = Path(os.path.expanduser("~/.local/share/cnsc-haai"))
        return config


def load_config(filepath: Optional[str] = None) -> CLIConfig:
    """Load configuration."""
    config = CLIConfig.default()
    config.load(filepath)
    return config


def save_config(config: CLIConfig, filepath: Optional[str] = None) -> None:
    """Save configuration."""
    config.save(filepath)

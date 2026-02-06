"""
CNSC-HAAI CLI

Main entry point for the Coherence Framework command-line interface.

Usage:
    cnsc-haai <command> [options]

Commands:
    parse        Parse GHLL source file
    compile      Compile GHLL to NSC bytecode
    run          Execute NSC bytecode
    trace        Run with full GML tracing
    replay       Replay a trace
    verify       Verify receipt chain
    encode       Encode to GLLL Hadamard format
    decode       Decode from GLLL Hadamard format
    lexicon      Manage lexicon
    codebook     Manage codebook
    version      Show version info
    help         Show this help message
"""

import argparse
import sys
import os
from typing import Optional


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="cnsc-haai",
        description="CNSC-HAAI - Coherence Framework CLI",
        epilog="Use 'cnsc-haai <command> --help' for more info on a command.",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"CNSC-HAAI v1.0.0",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (multiple for more detail)",
    )
    
    parser.add_argument(
        "--quiet",
        "-q",
        action="count",
        default=0,
        help="Decrease verbosity",
    )
    
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        description="Available commands",
    )
    
    return parser, subparsers


def setup_logging(verbosity: int) -> None:
    """Setup logging based on verbosity level."""
    import logging
    
    level = logging.WARNING
    if verbosity >= 2:
        level = logging.INFO
    if verbosity >= 3:
        level = logging.DEBUG
    
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point.
    
    Args:
        argv: Command line arguments (defaults to sys.argv)
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser, subparsers = create_parser()
    
    # Import and register subcommands
    from cnsc.haai.cli import commands
    commands.register_subcommands(subparsers)
    
    args = parser.parse_args(argv)
    
    # Setup logging
    verbosity = args.verbose - args.quiet
    setup_logging(verbosity)
    
    # Execute command
    if args.command is None:
        parser.print_help()
        return 0
    
    try:
        return commands.execute(args)
    except Exception as e:
        if verbosity >= 2:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

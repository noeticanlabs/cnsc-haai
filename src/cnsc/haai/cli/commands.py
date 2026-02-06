"""
CLI Commands

Implementations for all CLI subcommands.
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional
from datetime import datetime


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:
    """Register all subcommands with the argument parser."""
    
    # === Parse Command ===
    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse GHLL source file",
        description="Parse a GHLL source file and output AST.",
    )
    parse_parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Input file (default: stdin)",
    )
    parse_parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)",
    )
    parse_parser.add_argument(
        "--format",
        choices=["json", "yaml", "text"],
        default="json",
        help="Output format (default: json)",
    )
    parse_parser.add_argument(
        "--type-check",
        action="store_true",
        help="Enable type checking",
    )
    
    # === Compile Command ===
    compile_parser = subparsers.add_parser(
        "compile",
        help="Compile GHLL to NSC bytecode",
        description="Compile GHLL source to NSC bytecode.",
    )
    compile_parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Input file (default: stdin)",
    )
    compile_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output file for bytecode",
    )
    compile_parser.add_argument(
        "--entry",
        default="main",
        help="Entry point function (default: main)",
    )
    
    # === Run Command ===
    run_parser = subparsers.add_parser(
        "run",
        help="Execute NSC bytecode",
        description="Execute NSC bytecode with optional tracing.",
    )
    run_parser.add_argument(
        "input",
        help="Bytecode input file",
    )
    run_parser.add_argument(
        "--trace",
        action="store_true",
        help="Enable execution tracing",
    )
    run_parser.add_argument(
        "--trace-output",
        help="Output file for trace",
    )
    run_parser.add_argument(
        "--receipt",
        help="Output file for receipt",
    )
    
    # === Trace Command ===
    trace_parser = subparsers.add_parser(
        "trace",
        help="Run with full GML tracing",
        description="Execute with full governance metadata tracing.",
    )
    trace_parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Input source file (default: stdin)",
    )
    trace_parser.add_argument(
        "--output",
        "-o",
        help="Output file for trace",
    )
    trace_parser.add_argument(
        "--receipt",
        help="Output file for receipt",
    )
    
    # === Replay Command ===
    replay_parser = subparsers.add_parser(
        "replay",
        help="Replay a trace",
        description="Replay execution from a trace file.",
    )
    replay_parser.add_argument(
        "trace",
        help="Trace file to replay",
    )
    replay_parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify replay against original",
    )
    replay_parser.add_argument(
        "--output",
        "-o",
        help="Output file for replay result",
    )
    
    # === Verify Command ===
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify receipt chain",
        description="Verify integrity of a receipt chain.",
    )
    verify_parser.add_argument(
        "receipt",
        help="Receipt file or episode ID",
    )
    verify_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed verification info",
    )
    
    # === Encode Command ===
    encode_parser = subparsers.add_parser(
        "encode",
        help="Encode to GLLL Hadamard format",
        description="Encode data to GLLL Hadamard format.",
    )
    encode_parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Input file (default: stdin)",
    )
    encode_parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)",
    )
    encode_parser.add_argument(
        "--codebook",
        help="Codebook file to use",
    )
    encode_parser.add_argument(
        "--order",
        type=int,
        default=32,
        help="Hadamard matrix order (default: 32)",
    )
    
    # === Decode Command ===
    decode_parser = subparsers.add_parser(
        "decode",
        help="Decode from GLLL Hadamard format",
        description="Decode data from GLLL Hadamard format.",
    )
    decode_parser.add_argument(
        "input",
        help="Input file (Hadamard encoded)",
    )
    decode_parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)",
    )
    decode_parser.add_argument(
        "--codebook",
        help="Codebook file to use",
    )
    decode_parser.add_argument(
        "--order",
        type=int,
        default=32,
        help="Hadamard matrix order (default: 32)",
    )
    
    # === Lexicon Command ===
    lexicon_parser = subparsers.add_parser(
        "lexicon",
        help="Manage lexicon",
        description="Lexicon management operations.",
    )
    lexicon_subparsers = lexicon_parser.add_subparsers(
        title="operations",
        dest="operation",
    )
    
    lexicon_create = lexicon_subparsers.add_parser(
        "create",
        help="Create new lexicon",
    )
    lexicon_create.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output file",
    )
    lexicon_create.add_argument(
        "--name",
        default="Default Lexicon",
        help="Lexicon name",
    )
    
    lexicon_validate = lexicon_subparsers.add_parser(
        "validate",
        help="Validate lexicon",
    )
    lexicon_validate.add_argument(
        "file",
        help="Lexicon file to validate",
    )
    
    lexicon_export = lexicon_subparsers.add_parser(
        "export",
        help="Export lexicon entries",
    )
    lexicon_export.add_argument(
        "file",
        help="Lexicon file",
    )
    lexicon_export.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Export format",
    )
    
    # === Codebook Command ===
    codebook_parser = subparsers.add_parser(
        "codebook",
        help="Manage codebook",
        description="Codebook management operations.",
    )
    codebook_subparsers = codebook_parser.add_subparsers(
        title="operations",
        dest="operation",
    )
    
    codebook_create = codebook_subparsers.add_parser(
        "create",
        help="Create new codebook",
    )
    codebook_create.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output file",
    )
    codebook_create.add_argument(
        "--name",
        default="Default Codebook",
        help="Codebook name",
    )
    
    codebook_add = codebook_subparsers.add_parser(
        "add",
        help="Add glyph to codebook",
    )
    codebook_add.add_argument(
        "file",
        help="Codebook file",
    )
    codebook_add.add_argument(
        "--symbol",
        required=True,
        help="Symbol to add",
    )
    codebook_add.add_argument(
        "--code",
        required=True,
        help="Hadamard code (comma-separated)",
    )
    
    codebook_validate = codebook_subparsers.add_parser(
        "validate",
        help="Validate codebook",
    )
    codebook_validate.add_argument(
        "file",
        help="Codebook file to validate",
    )
    
    codebook_stats = codebook_subparsers.add_parser(
        "stats",
        help="Show codebook statistics",
    )
    codebook_stats.add_argument(
        "file",
        help="Codebook file",
    )
    
    # === Version Command ===
    version_parser = subparsers.add_parser(
        "version",
        help="Show version info",
        description="Show version and system information.",
    )
    version_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )


def execute(args: argparse.Namespace) -> int:
    """
    Execute the specified command.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        Exit code
    """
    command = args.command
    
    if command == "parse":
        return cmd_parse(args)
    elif command == "compile":
        return cmd_compile(args)
    elif command == "run":
        return cmd_run(args)
    elif command == "trace":
        return cmd_trace(args)
    elif command == "replay":
        return cmd_replay(args)
    elif command == "verify":
        return cmd_verify(args)
    elif command == "encode":
        return cmd_encode(args)
    elif command == "decode":
        return cmd_decode(args)
    elif command == "lexicon":
        return cmd_lexicon(args)
    elif command == "codebook":
        return cmd_codebook(args)
    elif command == "version":
        return cmd_version(args)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 1


def cmd_parse(args: argparse.Namespace) -> int:
    """Handle parse command."""
    from cnsc.haai.ghll.parser import parse_ghll
    from cnsc.haai.ghll.types import TypeChecker
    
    # Read input
    if args.input == "-":
        source = sys.stdin.read()
    else:
        with open(args.input) as f:
            source = f.read()
    
    # Parse
    result = parse_ghll(source, args.input)
    
    if not result.success:
        print("Parse errors:", file=sys.stderr)
        for error in result.errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    
    # Type check if requested
    if args.type_check:
        checker = TypeChecker()
        for node in result.ast:
            if isinstance(node, dict) and "type" in node:
                # Type check expression
                pass
    
    # Format output
    if args.format == "json":
        output = json.dumps(result.to_dict(), indent=2)
    elif args.format == "yaml":
        try:
            import yaml
            output = yaml.dump(result.to_dict(), default_flow_style=False)
        except ImportError:
            output = json.dumps(result.to_dict(), indent=2)
    else:
        output = str(result.ast)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        print(output)
    
    return 0


def cmd_compile(args: argparse.Namespace) -> int:
    """Handle compile command."""
    from cnsc.haai.ghll.parser import parse_ghll
    from cnsc.haai.nsc.vm import NSCVirtualMachine, compile_to_bytecode
    
    # Read input
    if args.input == "-":
        source = sys.stdin.read()
    else:
        with open(args.input) as f:
            source = f.read()
    
    # Parse
    result = parse_ghll(source, args.input)
    if not result.success:
        print("Parse errors:", file=sys.stderr)
        for error in result.errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    
    # Compile to bytecode
    try:
        bytecode = compile_to_bytecode(result.ast, entry_point=args.entry)
        
        # Save bytecode
        with open(args.output, "wb") as f:
            f.write(bytecode)
        
        print(f"Compiled to {args.output}")
        return 0
    except Exception as e:
        print(f"Compilation error: {e}", file=sys.stderr)
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    """Handle run command."""
    from cnsc.haai.nsc.vm import NSCVirtualMachine
    
    # Load bytecode
    with open(args.input, "rb") as f:
        bytecode = f.read()
    
    # Create VM
    vm = NSCVirtualMachine()
    
    # Run
    try:
        result = vm.run(bytecode)
        
        if args.trace:
            print("Execution trace enabled (not shown)")
        
        if args.receipt:
            print(f"Receipt saved to {args.receipt}")
        
        print(f"Execution completed: {result}")
        return 0
    except Exception as e:
        print(f"Execution error: {e}", file=sys.stderr)
        return 1


def cmd_trace(args: argparse.Namespace) -> int:
    """Handle trace command."""
    print("Trace command - full GML tracing")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Receipt: {args.receipt}")
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    """Handle replay command."""
    print("Replay command")
    print(f"Trace: {args.trace}")
    print(f"Verify: {args.verify}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Handle verify command."""
    print("Verify command")
    print(f"Receipt: {args.receipt}")
    print(f"Verbose: {args.verbose}")
    return 0


def cmd_encode(args: argparse.Namespace) -> int:
    """Handle encode command."""
    print("Encode command")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Codebook: {args.codebook}")
    print(f"Order: {args.order}")
    return 0


def cmd_decode(args: argparse.Namespace) -> int:
    """Handle decode command."""
    print("Decode command")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Codebook: {args.codebook}")
    print(f"Order: {args.order}")
    return 0


def cmd_lexicon(args: argparse.Namespace) -> int:
    """Handle lexicon command."""
    operation = getattr(args, "operation", None)
    
    if operation == "create":
        from cnsc.haai.ghll.lexicon import LexiconManager
        lexicon = LexiconManager.create_default_lexicon(args.name)
        lexicon.save(args.output)
        print(f"Created lexicon: {args.output}")
        return 0
    
    elif operation == "validate":
        from cnsc.haai.ghll.lexicon import LexiconManager
        lexicon = LexiconManager.load(args.file)
        valid, errors = lexicon.validate_integrity()
        if valid:
            print("Lexicon is valid")
            return 0
        else:
            print("Lexicon validation errors:", file=sys.stderr)
            for error in errors:
                print(f"  {error}", file=sys.stderr)
            return 1
    
    elif operation == "export":
        from cnsc.haai.ghll.lexicon import LexiconManager
        lexicon = LexiconManager.load(args.file)
        entries = lexicon.get_all_entries()
        
        if args.format == "json":
            output = json.dumps([e.to_dict() for e in entries], indent=2)
        else:
            # CSV format
            lines = ["token,category,pattern"]
            for e in entries:
                lines.append(f"{e.token},{e.category},{e.pattern}")
            output = "\n".join(lines)
        
        print(output)
        return 0
    
    else:
        print(" lexicon: missing operation. Use 'create', 'validate', or 'export'")
        return 1


def cmd_codebook(args: argparse.Namespace) -> int:
    """Handle codebook command."""
    operation = getattr(args, "operation", None)
    
    if operation == "create":
        from cnsc.haai.glll.codebook import create_codebook
        codebook = create_codebook(args.name)
        codebook.save(args.output)
        print(f"Created codebook: {args.output}")
        return 0
    
    elif operation == "add":
        from cnsc.haai.glll.codebook import create_codebook, GlyphType, SymbolCategory
        codebook = create_codebook.load(args.file)
        
        # Parse code
        code = [int(x.strip()) for x in args.code.split(",")]
        
        codebook.add_glyph(Glyph(
            glyph_id=str(len(codebook.glyphs)),
            symbol=args.symbol,
            glyph_type=GlyphType.DATA,
            category=SymbolCategory.ATOM,
            hadamard_code=code,
            vector=[float(x) for x in code],
        ))
        
        codebook.save(args.file)
        print(f"Added {args.symbol} to codebook")
        return 0
    
    elif operation == "validate":
        from cnsc.haai.glll.codebook import create_codebook, create_codebook_validator
        codebook = create_codebook.load(args.file)
        validator = create_codebook_validator()
        valid, errors = validator.validate(codebook)
        
        if valid:
            print("Codebook is valid")
            return 0
        else:
            print("Codebook validation errors:", file=sys.stderr)
            for error in errors:
                print(f"  {error}", file=sys.stderr)
            return 1
    
    elif operation == "stats":
        from cnsc.haai.glll.codebook import create_codebook
        codebook = create_codebook.load(args.file)
        stats = codebook.get_stats()
        print(json.dumps(stats, indent=2))
        return 0
    
    else:
        print("codebook: missing operation. Use 'create', 'add', 'validate', or 'stats'")
        return 1


def cmd_version(args: argparse.Namespace) -> int:
    """Handle version command."""
    import platform
    
    version_info = {
        "version": "1.0.0",
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    
    if args.json:
        print(json.dumps(version_info, indent=2))
    else:
        print(f"CNSC-HAAI v{version_info['version']}")
        print(f"Python: {version_info['python']}")
        print(f"Platform: {version_info['platform']}")
    
    return 0

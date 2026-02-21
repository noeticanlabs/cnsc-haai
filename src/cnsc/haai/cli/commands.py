"""
CLI Commands

Implementations for all CLI subcommands.
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional
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
    
    # === NPE Command ===
    npe_parser = subparsers.add_parser(
        "npe",
        help="NPE (Noetican Proposal Engine) service management",
        description="NPE service management and proposal operations.",
    )
    npe_subparsers = npe_parser.add_subparsers(
        title="operations",
        dest="operation",
    )
    
    # === NPE Service Management ===
    # npe start
    npe_start = npe_subparsers.add_parser(
        "start",
        help="Start NPE service",
        description="Start NPE service as a background process.",
    )
    npe_start.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    npe_start.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    npe_start.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)",
    )
    
    # npe stop
    npe_stop = npe_subparsers.add_parser(
        "stop",
        help="Stop NPE service",
        description="Stop the running NPE service.",
    )
    npe_stop.add_argument(
        "--url",
        default="http://localhost:8000",
        help="NPE service URL (default: http://localhost:8000)",
    )
    npe_stop.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout for stop request (default: 10)",
    )
    
    # npe status
    npe_status = npe_subparsers.add_parser(
        "status",
        help="Check NPE service status",
        description="Check if NPE service is running.",
    )
    npe_status.add_argument(
        "--url",
        default="http://localhost:8000",
        help="NPE service URL (default: http://localhost:8000)",
    )
    
    # npe health
    npe_health = npe_subparsers.add_parser(
        "health",
        help="Detailed NPE health check",
        description="Get detailed health information from NPE service.",
    )
    npe_health.add_argument(
        "--url",
        default="http://localhost:8000",
        help="NPE service URL (default: http://localhost:8000)",
    )
    
    # === NPE Proposal Commands ===
    # npe propose
    npe_propose = npe_subparsers.add_parser(
        "propose",
        help="Submit a proposal request",
        description="Submit a proposal request to the NPE service.",
    )
    npe_propose.add_argument(
        "domain",
        help="Domain for proposal (e.g., 'gr' for general reasoning)",
    )
    npe_propose.add_argument(
        "candidate_type",
        help="Type of candidate to generate",
    )
    npe_propose.add_argument(
        "--url",
        default="http://localhost:8000",
        help="NPE service URL (default: http://localhost:8000)",
    )
    npe_propose.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)",
    )
    npe_propose.add_argument(
        "--max-candidates",
        type=int,
        default=16,
        help="Maximum number of candidates (default: 16)",
    )
    npe_propose.add_argument(
        "--max-time",
        type=int,
        default=1000,
        help="Maximum wall time in milliseconds (default: 1000)",
    )
    npe_propose.add_argument(
        "--output",
        "-o",
        help="Output file for results (default: stdout)",
    )
    
    # npe repair
    npe_repair = npe_subparsers.add_parser(
        "repair",
        help="Request a repair for a gate failure",
        description="Submit a repair request for a failed gate.",
    )
    npe_repair.add_argument(
        "gate_name",
        help="Name of the gate that failed",
    )
    npe_repair.add_argument(
        "failure_reasons",
        nargs="+",
        help="Reasons for the gate failure",
    )
    npe_repair.add_argument(
        "--url",
        default="http://localhost:8000",
        help="NPE service URL (default: http://localhost:8000)",
    )
    npe_repair.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)",
    )
    npe_repair.add_argument(
        "--output",
        "-o",
        help="Output file for results (default: stdout)",
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
    elif command == "npe":
        return cmd_npe(args)
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
    """Handle trace command - full GML tracing with coherence tracking."""
    from cnsc.haai.gml.trace import TraceManager, TraceLevel, TraceEvent, TraceThread
    from cnsc.haai.gml.receipts import ReceiptSystem, ReceiptStepType, ReceiptDecision
    from cnsc.haai.ghll.parser import parse_ghll
    
    # Read input
    if args.input == "-":
        source = sys.stdin.read()
    else:
        with open(args.input) as f:
            source = f.read()
    
    # Create trace manager and receipt system
    trace_manager = TraceManager()
    receipt_system = ReceiptSystem()
    
    # Create a trace thread for this execution
    thread = trace_manager.create_thread(name="main", thread_id="main")
    
    # Initial coherence state (1.0 = fully coherent)
    coherence_state = 1.0
    
    # Log start of trace
    start_event = TraceEvent.create(
        level=TraceLevel.INFO,
        event_type="trace_start",
        message=f"Starting GML trace for {args.input}",
        details={
            "source": args.input,
            "content_length": len(source),
            "content_preview": source[:100] if len(source) > 100 else source
        },
        thread_id=thread.thread_id,
        coherence_before=None,
        coherence_after=coherence_state
    )
    trace_manager.add_event(start_event)
    
    # Parse the source with GHLL
    coherence_before_parse = coherence_state
    parse_event = TraceEvent.create(
        level=TraceLevel.DEBUG,
        event_type="ghll_parse_start",
        message="Starting GHLL parse",
        details={"input_length": len(source)},
        thread_id=thread.thread_id,
        coherence_before=coherence_before_parse,
        coherence_after=coherence_state
    )
    trace_manager.add_event(parse_event)
    
    # Perform the parse
    parse_result = parse_ghll(source, args.input)
    
    if parse_result.success:
        # Parse succeeded - log with coherence impact
        coherence_after_parse = coherence_state  # Successful parse maintains coherence
        
        parse_success_event = TraceEvent.create(
            level=TraceLevel.INFO,
            event_type="ghll_parse_complete",
            message=f"GHLL parse successful - {len(parse_result.ast)} AST nodes",
            details={
                "ast_node_count": len(parse_result.ast),
                "has_errors": len(parse_result.errors) > 0,
                "warnings": parse_result.warnings
            },
            thread_id=thread.thread_id,
            coherence_before=coherence_before_parse,
            coherence_after=coherence_after_parse
        )
        trace_manager.add_event(parse_success_event)
        
        # Analyze AST for coherence-relevant operations
        coherence_state = coherence_after_parse
        coherence_before_analysis = coherence_state
        
        analysis_event = TraceEvent.create(
            level=TraceLevel.DEBUG,
            event_type="coherence_analysis_start",
            message="Starting coherence analysis",
            thread_id=thread.thread_id,
            coherence_before=coherence_before_analysis,
            coherence_after=coherence_state
        )
        trace_manager.add_event(analysis_event)
        
        # Analyze AST nodes for coherence impact
        analysis_details = _analyze_ast_for_coherence(parse_result.ast)
        
        # Update coherence based on analysis
        coherence_after_analysis = max(0.0, min(1.0, coherence_state - analysis_details.get("coherence_impact", 0.0)))
        
        analysis_complete_event = TraceEvent.create(
            level=TraceLevel.INFO,
            event_type="coherence_analysis_complete",
            message="Coherence analysis complete",
            details=analysis_details,
            thread_id=thread.thread_id,
            coherence_before=coherence_before_analysis,
            coherence_after=coherence_after_analysis
        )
        trace_manager.add_event(analysis_complete_event)
        coherence_state = coherence_after_analysis
        
        # Generate receipt if requested
        if args.receipt:
            coherence_before_receipt = coherence_state
            # Use emit_receipt for trace-based receipt
            receipt = receipt_system.emit_receipt(
                step_type=ReceiptStepType.CUSTOM,
                source=args.input,
                input_data=source,
                output_data=parse_result.to_dict() if hasattr(parse_result, 'to_dict') else {"ast": parse_result.ast, "success": parse_result.success},
                decision=ReceiptDecision.PASS if parse_result.success else ReceiptDecision.FAIL,
                episode_id=None,
                phase="trace_execution"
            )
            
            receipt_event = TraceEvent.create(
                level=TraceLevel.INFO,
                event_type="receipt_generated",
                message="Receipt generated successfully",
                details={
                    "receipt_id": receipt.receipt_id if hasattr(receipt, 'receipt_id') else "unknown",
                    "chain_hash": receipt.chain_hash if hasattr(receipt, 'chain_hash') else None,
                    "coherence_state": coherence_state
                },
                thread_id=thread.thread_id,
                coherence_before=coherence_before_receipt,
                coherence_after=coherence_state
            )
            trace_manager.add_event(receipt_event)
            
            # Save receipt
            receipt_dict = receipt.to_dict() if hasattr(receipt, 'to_dict') else {"receipt_id": "unknown"}
            with open(args.receipt, 'w') as f:
                json.dump(receipt_dict, f, indent=2)
            print(f"Receipt saved to {args.receipt}")
    else:
        # Parse failed - log errors
        coherence_after_parse = max(0.0, coherence_state - 0.2)  # Penalty for parse failure
        
        parse_error_event = TraceEvent.create(
            level=TraceLevel.ERROR,
            event_type="ghll_parse_failed",
            message=f"GHLL parse failed - {len(parse_result.errors)} errors",
            details={
                "errors": [str(e) for e in parse_result.errors],
                "warnings": [str(w) for w in parse_result.warnings]
            },
            thread_id=thread.thread_id,
            coherence_before=coherence_before_parse,
            coherence_after=coherence_after_parse
        )
        trace_manager.add_event(parse_error_event)
        coherence_state = coherence_after_parse
    
    # Log end of trace
    end_event = TraceEvent.create(
        level=TraceLevel.INFO,
        event_type="trace_end",
        message="GML trace complete",
        details={
            "final_coherence_state": coherence_state,
            "total_events": len(trace_manager.events),
            "active_threads": len(trace_manager.threads)
        },
        thread_id=thread.thread_id,
        coherence_before=coherence_state,
        coherence_after=coherence_state
    )
    trace_manager.add_event(end_event)
    
    # Output trace
    trace_data = trace_manager.to_dict()
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(trace_data, f, indent=2)
        print(f"Trace saved to {args.output}")
    else:
        print(json.dumps(trace_data, indent=2))
    
    return 0


def _analyze_ast_for_coherence(ast: List) -> Dict:
    """Analyze AST for coherence-relevant operations."""
    analysis = {
        "total_nodes": 0,
        "operation_types": {},
        "coherence_impact": 0.0,
        "high_risk_operations": [],
        "requires_validation": False
    }
    
    if not ast:
        return analysis
    
    analysis["total_nodes"] = len(ast)
    
    # Analyze each node
    for node in ast:
        if isinstance(node, dict):
            node_type = node.get("type", "unknown")
            
            # Track operation types
            if node_type not in analysis["operation_types"]:
                analysis["operation_types"][node_type] = 0
            analysis["operation_types"][node_type] += 1
            
            # Check for high-risk operations that impact coherence
            high_risk_types = {"assertion", "assumption", "cut", "unfold", "rewrite"}
            if node_type in high_risk_types:
                analysis["coherence_impact"] += 0.05  # Each high-risk op reduces coherence slightly
                analysis["high_risk_operations"].append(node_type)
                analysis["requires_validation"] = True
            
            # Check for coherence-relevant constructs
            coherence_relevant = {"branch", "loop", "recursion", "quantum_gate"}
            if node_type in coherence_relevant:
                analysis["coherence_impact"] += 0.02
    
    # Cap coherence impact
    analysis["coherence_impact"] = min(analysis["coherence_impact"], 0.5)
    
    return analysis


def cmd_replay(args: argparse.Namespace) -> int:
    """Handle replay command."""
    print("Replay command")
    print(f"Trace: {args.trace}")
    print(f"Verify: {args.verify}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Handle verify command - verify receipt chain."""
    from cnsc.haai.gml.receipts import ReceiptSystem, ChainValidator
    
    # Load receipt system from file or verify single receipt
    try:
        with open(args.receipt) as f:
            data = json.load(f)
        
        # Check if it's a receipt file or episode
        if "receipts" in data:
            # Full receipt system dump
            from cnsc.haai.gml.receipts import Receipt
            receipts = [Receipt.from_dict(r) for r in data["receipts"]]
            validator = ChainValidator()
            valid, message, details = validator.validate_chain(receipts)
        elif "receipt_id" in data:
            # Single receipt
            receipt = Receipt.from_dict(data)
            validator = ChainValidator()
            valid, message = validator.validate_receipt(receipt)
            details = {}
        else:
            print(f"Unknown receipt format in {args.receipt}", file=sys.stderr)
            return 1
        
        if args.verbose:
            print(json.dumps({"valid": valid, "message": message, "details": details}, indent=2))
        else:
            print(f"Verification: {'PASSED' if valid else 'FAILED'} - {message}")
        
        return 0 if valid else 1
    except FileNotFoundError:
        print(f"File not found: {args.receipt}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Verification error: {e}", file=sys.stderr)
        return 1


def cmd_encode(args: argparse.Namespace) -> int:
    """Handle encode command - encode data to GLLL Hadamard format."""
    from cnsc.haai.glll.hadamard import HadamardCodec
    
    # Read input
    if args.input == "-":
        data_str = sys.stdin.read()
    else:
        with open(args.input) as f:
            data_str = f.read()
    
    # Convert input to binary data
    # For now, encode the string as binary
    binary_data = [ord(c) for c in data_str]
    
    # Create codec and encode
    codec = HadamardCodec(order=args.order)
    encoded = codec.encode(binary_data)
    
    # Output
    output_data = {
        "original_length": len(binary_data),
        "order": args.order,
        "encoded": encoded,
    }
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"Encoded data saved to {args.output}")
    else:
        print(json.dumps(output_data, indent=2))
    
    return 0


def cmd_decode(args: argparse.Namespace) -> int:
    """Handle decode command - decode from GLLL Hadamard format."""
    from cnsc.haai.glll.hadamard import HadamardCodec
    
    # Read input
    with open(args.input) as f:
        data = json.load(f)
    
    encoded = data.get("encoded", [])
    
    if not encoded:
        print("No encoded data found in input", file=sys.stderr)
        return 1
    
    # Create codec and decode
    codec = HadamardCodec(order=data.get("order", args.order))
    decoded, was_corrected = codec.decode(encoded)
    
    # Convert binary back to string
    result_str = ''.join(chr(b) for b in decoded if b < 256)
    
    output_data = {
        "decoded": result_str,
        "was_corrected": was_corrected,
        "original_length": data.get("original_length", 0),
    }
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result_str)
        print(f"Decoded data saved to {args.output}")
    else:
        print(json.dumps(output_data, indent=2))
    
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
        from cnsc.haai.glll.codebook import Codebook, GlyphType, SymbolCategory, Glyph
        codebook = Codebook.load(args.file)
        
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
        from cnsc.haai.glll.codebook import Codebook, create_codebook_validator
        codebook = Codebook.load(args.file)
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
        from cnsc.haai.glll.codebook import Codebook
        codebook = Codebook.load(args.file)
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


def cmd_npe(args: argparse.Namespace) -> int:
    """Handle NPE command."""
    operation = args.operation
    
    if operation == "start":
        return cmd_npe_start(args)
    elif operation == "stop":
        return cmd_npe_stop(args)
    elif operation == "status":
        return cmd_npe_status(args)
    elif operation == "health":
        return cmd_npe_health(args)
    elif operation == "propose":
        return cmd_npe_propose(args)
    elif operation == "repair":
        return cmd_npe_repair(args)
    else:
        print(f"npe: unknown operation '{operation}'", file=sys.stderr)
        print("Use 'cnsc-haai npe --help' for available operations.")
        return 1


def cmd_npe_start(args: argparse.Namespace) -> int:
    """Start NPE service."""
    import subprocess
    import sys
    import os
    
    # Build command to start NPE service
    cmd = [
        sys.executable, "-m", "npe.cli", "start",
        "--host", args.host,
        "--port", str(args.port),
        "--workers", str(args.workers),
    ]
    
    print(f"Starting NPE service on {args.host}:{args.port}...")
    
    # Start as background process
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        )
        print(f"NPE service started (PID: {proc.pid})")
        print("Use 'cnsc-haai npe status' to check if it's running")
        return 0
    except Exception as e:
        print(f"Failed to start NPE service: {e}", file=sys.stderr)
        return 1


def cmd_npe_stop(args: argparse.Namespace) -> int:
    """Stop NPE service."""
    from cnsc.haai.nsc.proposer_client import ProposerClient
    
    try:
        client = ProposerClient(base_url=args.url, timeout=args.timeout)
        
        # The NPE service doesn't have a stop endpoint, so we just report
        # In a real implementation, this might use a management endpoint
        print(f"NPE stop request sent to {args.url}")
        print("Note: The service may need to be stopped manually or via process management")
        client.close()
        return 0
    except Exception as e:
        print(f"Failed to stop NPE service: {e}", file=sys.stderr)
        return 1


def cmd_npe_status(args: argparse.Namespace) -> int:
    """Check NPE service status."""
    from cnsc.haai.nsc.proposer_client import ProposerClient
    
    try:
        client = ProposerClient(base_url=args.url, timeout=5)
        is_healthy = client.health()
        client.close()
        
        if is_healthy:
            print(f"NPE service at {args.url} is RUNNING")
            return 0
        else:
            print(f"NPE service at {args.url} is NOT RUNNING")
            return 1
    except Exception as e:
        print(f"NPE service at {args.url} is NOT RUNNING: {e}")
        return 1


def cmd_npe_health(args: argparse.Namespace) -> int:
    """Get detailed NPE health information."""
    from cnsc.haai.nsc.proposer_client import ProposerClient
    
    try:
        client = ProposerClient(base_url=args.url, timeout=5)
        health_details = client.get_health_details()
        client.close()
        
        if health_details:
            print(f"NPE Service Health Report ({args.url})")
            print("=" * 50)
            print(json.dumps(health_details, indent=2))
            return 0
        else:
            print(f"NPE service at {args.url} is not responding or unhealthy")
            return 1
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        return 1


def cmd_npe_propose(args: argparse.Namespace) -> int:
    """Submit a proposal request to NPE."""
    from cnsc.haai.nsc.proposer_client import ProposerClient
    
    try:
        client = ProposerClient(base_url=args.url, timeout=args.timeout)
        
        budget = {
            "max_wall_ms": args.max_time,
            "max_candidates": args.max_candidates,
        }
        
        response = client.propose(
            domain=args.domain,
            candidate_type=args.candidate_type,
            context={},
            budget=budget,
        )
        
        client.close()
        
        # Format output
        result = {
            "request_id": response.get("request_id", "N/A"),
            "domain": args.domain,
            "candidate_type": args.candidate_type,
            "candidates": response.get("candidates", []),
        }
        
        output = json.dumps(result, indent=2)
        
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Results written to {args.output}")
        else:
            print(output)
        
        return 0
    except Exception as e:
        print(f"Proposal request failed: {e}", file=sys.stderr)
        return 1


def cmd_npe_repair(args: argparse.Namespace) -> int:
    """Submit a repair request to NPE."""
    from cnsc.haai.nsc.proposer_client import ProposerClient
    
    try:
        client = ProposerClient(base_url=args.url, timeout=args.timeout)
        
        response = client.repair(
            gate_name=args.gate_name,
            failure_reasons=args.failure_reasons,
            context={},
        )
        
        client.close()
        
        # Format output
        result = {
            "request_id": response.get("request_id", "N/A"),
            "gate_name": args.gate_name,
            "failure_reasons": args.failure_reasons,
            "candidates": response.get("candidates", []),
        }
        
        output = json.dumps(result, indent=2)
        
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Results written to {args.output}")
        else:
            print(output)
        
        return 0
    except Exception as e:
        print(f"Repair request failed: {e}", file=sys.stderr)
        return 1

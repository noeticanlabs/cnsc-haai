"""
NPE Command Line Interface.

Provides commands for indexing, proposing, and repairing.
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional

from ..core.hashing import hash_request
from ..core.types import NPERequest, NPERepairRequest, Budgets
from ..retrieval.index_build import build_index, save_index
from ..registry.loader import load_registry


def run_index_command(
    corpus: str,
    receipts: Optional[str] = None,
    out: str = "npe_assets/index",
) -> Dict[str, Any]:
    """Run the index command.
    
    Args:
        corpus: Path to corpus directory
        receipts: Optional path to receipts directory
        out: Output directory for index
        
    Returns:
        Index result dict
    """
    import os
    os.makedirs(out, exist_ok=True)
    
    builder = build_index(corpus, receipts, out)
    
    result = {
        "corpus_snapshot_hash": builder.corpus_snapshot_hash,
        "corpus_chunk_count": len(builder.corpus_store.chunks) if builder.corpus_store else 0,
    }
    
    if builder.receipts_store:
        result["receipts_snapshot_hash"] = builder.receipts_snapshot_hash
        result["receipt_count"] = len(builder.receipts_store.receipts)
    
    return result


def run_propose_command(request_file: str, output: Optional[str] = None) -> Dict[str, Any]:
    """Run the propose command.
    
    Args:
        request_file: Path to request JSON file
        output: Optional output file path
        
    Returns:
        Response dict
    """
    with open(request_file, "r", encoding="utf-8") as f:
        request_data = json.load(f)
    
    # Compute request hash
    request_id = hash_request(request_data)
    request_data["request_id"] = request_id
    
    # Create request object
    budgets = request_data.get("budgets", {})
    budget = Budgets(
        max_wall_ms=budgets.get("max_wall_ms", 1000),
        max_candidates=budgets.get("max_candidates", 16),
        max_evidence_items=budgets.get("max_evidence_items", 100),
        max_search_expansions=budgets.get("max_search_expansions", 50),
    )
    
    request = NPERequest(
        spec=request_data.get("spec", "NPE-REQUEST-1.0"),
        request_type=request_data.get("request_type", "propose"),
        request_id=request_id,
        domain=request_data.get("domain", "gr"),
        determinism_tier=request_data.get("determinism_tier", "d0"),
        seed=request_data.get("seed", 0),
        budgets=budget,
        inputs=request_data.get("inputs", {}),
    )
    
    # Load registry and create service
    from ..api.routes import NPEService
    registry = load_registry()
    service = NPEService(registry)
    
    # Execute proposal
    response = service.execute_proposal(request)
    
    # Convert to dict
    result = {
        "response_id": response.response_id,
        "request_id": response.request_id,
        "domain": response.domain,
        "registry_hash": response.registry_hash,
        "candidate_count": len(response.candidates),
        "candidates": [
            {
                "candidate_hash": c.candidate_hash,
                "candidate_type": c.candidate_type,
                "scores": {
                    "risk": c.scores.risk,
                    "utility": c.scores.utility,
                    "cost": c.scores.cost,
                    "confidence": c.scores.confidence,
                },
            }
            for c in response.candidates
        ],
    }
    
    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    return result


def run_repair_command(request_file: str, output: Optional[str] = None) -> Dict[str, Any]:
    """Run the repair command.
    
    Args:
        request_file: Path to repair request JSON file
        output: Optional output file path
        
    Returns:
        Response dict
    """
    with open(request_file, "r", encoding="utf-8") as f:
        request_data = json.load(f)
    
    # Compute request hash
    request_id = hash_request(request_data)
    request_data["request_id"] = request_id
    
    # Create repair request object
    budgets = request_data.get("budgets", {})
    budget = Budgets(
        max_wall_ms=budgets.get("max_wall_ms", 1000),
        max_candidates=budgets.get("max_candidates", 16),
        max_evidence_items=budgets.get("max_evidence_items", 100),
        max_search_expansions=budgets.get("max_search_expansions", 50),
    )
    
    failure_data = request_data.get("failure", {})
    from ..core.types import FailureInfo
    failure = FailureInfo(
        proof_hash=failure_data.get("proof_hash", ""),
        gate_stack_id=failure_data.get("gate_stack_id", ""),
        registry_hash=failure_data.get("registry_hash", ""),
        failing_gates=failure_data.get("failing_gates", []),
    )
    
    request = NPERepairRequest(
        spec=request_data.get("spec", "NPE-REPAIR-REQUEST-1.0"),
        request_type="repair",
        request_id=request_id,
        domain=request_data.get("domain", "gr"),
        determinism_tier=request_data.get("determinism_tier", "d0"),
        seed=request_data.get("seed", 0),
        budgets=budget,
        inputs=request_data.get("inputs", {}),
        failure=failure,
    )
    
    # Load registry and create service
    from ..api.routes import NPEService
    registry = load_registry()
    service = NPEService(registry)
    
    # Execute repair
    response = service.execute_repair(request)
    
    # Convert to dict
    result = {
        "response_id": response.response_id,
        "request_id": response.request_id,
        "domain": response.domain,
        "registry_hash": response.registry_hash,
        "candidate_count": len(response.candidates),
        "candidates": [
            {
                "candidate_hash": c.candidate_hash,
                "candidate_type": c.candidate_type,
                "scores": {
                    "risk": c.scores.risk,
                    "utility": c.scores.utility,
                    "cost": c.scores.cost,
                    "confidence": c.scores.confidence,
                },
            }
            for c in response.candidates
        ],
    }
    
    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    return result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="NPE - Noetican Proposal Engine")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Build corpus index")
    index_parser.add_argument("--corpus", required=True, help="Path to corpus directory")
    index_parser.add_argument("--receipts", help="Path to receipts directory")
    index_parser.add_argument("--out", default="npe_assets/index", help="Output directory")
    
    # Propose command
    propose_parser = subparsers.add_parser("propose", help="Run proposal request")
    propose_parser.add_argument("--request", required=True, help="Path to request JSON file")
    propose_parser.add_argument("--output", help="Output file path")
    
    # Repair command
    repair_parser = subparsers.add_parser("repair", help="Run repair request")
    repair_parser.add_argument("--request", required=True, help="Path to request JSON file")
    repair_parser.add_argument("--output", help="Output file path")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start NPE server")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    serve_parser.add_argument("--socket", help="Unix socket path")
    serve_parser.add_argument("--registry", help="Path to registry manifest")
    
    args = parser.parse_args()
    
    if args.command == "index":
        result = run_index_command(args.corpus, args.receipts, args.out)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "propose":
        result = run_propose_command(args.request, args.output)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "repair":
        result = run_repair_command(args.request, args.output)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "serve":
        from ..api.server import NPEServer
        server = NPEServer(
            host=args.host,
            port=args.port,
            socket_path=args.socket,
            registry_path=args.registry,
        )
        try:
            import asyncio
            asyncio.run(server.start())
        except KeyboardInterrupt:
            pass
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

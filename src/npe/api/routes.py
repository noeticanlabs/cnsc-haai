"""
API Routes for NPE Service.

Defines endpoints for propose, repair, and health checks.
"""

from typing import Any, Dict, Optional

from ..core.budgets import BudgetEnforcer
from ..core.errors import ErrorCode, NPEError
from ..core.hashing import hash_response
from ..core.types import Candidate, NPERequest, NPEResponse
from .wire import parse_request, serialize_response


class NPERouter:
    """Router for NPE API endpoints."""

    def __init__(self, npe_service: "NPEService"):
        """Initialize the router.

        Args:
            npe_service: The NPE service instance
        """
        self._service = npe_service

    async def handle_propose(self, data: Dict[str, Any]) -> bytes:
        """Handle a propose request.

        Args:
            data: Request data

        Returns:
            Response bytes
        """
        try:
            # Parse and validate request
            request, request_id = parse_request(data)

            # Execute proposal
            response = self._service.execute_proposal(request)

            # Serialize response
            return serialize_response(response)

        except ValueError as e:
            return self._create_error_response(
                str(e), request_id if "request_id" in dir() else None
            )
        except NPEError as e:
            return self._create_error_response(str(e), e.request_id, e.code)
        except Exception as e:
            return self._create_error_response(f"Internal error: {str(e)}")

    async def handle_repair(self, data: Dict[str, Any]) -> bytes:
        """Handle a repair request.

        Args:
            data: Request data

        Returns:
            Response bytes
        """
        try:
            # Parse and validate request
            request, request_id = parse_request(data)

            # Execute repair
            response = self._service.execute_repair(request)

            # Serialize response
            return serialize_response(response)

        except ValueError as e:
            return self._create_error_response(
                str(e), request_id if "request_id" in dir() else None
            )
        except NPEError as e:
            return self._create_error_response(str(e), e.request_id, e.code)
        except Exception as e:
            return self._create_error_response(f"Internal error: {str(e)}")

    async def handle_health(self) -> bytes:
        """Handle a health check request.

        Returns:
            Health response bytes
        """
        health = self._service.health_check()
        import json

        json_str = json.dumps(health, separators=(",", ":"), ensure_ascii=False)
        return json_str.encode("utf-8")

    def _create_error_response(
        self,
        message: str,
        request_id: Optional[str] = None,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
    ) -> bytes:
        """Create an error response.

        Args:
            message: Error message
            request_id: Related request ID
            code: Error code

        Returns:
            Error response bytes
        """
        response = NPEResponse(
            spec="NPE-RESPONSE-1.0",
            response_id="",  # Will be computed
            request_id=request_id or "",
            domain="gr",
            error={"code": code.value, "message": message},
        )
        return serialize_response(response)


def setup_routes(app, router: NPERouter) -> None:
    """Set up routes on an aiohttp app.

    Args:
        app: The aiohttp application
        router: The NPE router
    """
    app.router.add_post("/npe/v1/propose", router.handle_propose)
    app.router.add_post("/npe/v1/repair", router.handle_repair)
    app.router.add_get("/npe/v1/health", router.handle_health)


class NPEService:
    """Core NPE Service logic."""

    def __init__(self, registry: Any, corpus_index: Any = None):
        """Initialize the service.

        Args:
            registry: The proposer registry
            corpus_index: Optional corpus index
        """
        self._registry = registry
        self._corpus_index = corpus_index
        self._request_count = 0

    def execute_proposal(self, request: NPERequest) -> NPEResponse:
        """Execute a proposal request.

        Args:
            request: The proposal request

        Returns:
            Proposal response
        """
        self._request_count += 1

        # Create budget enforcer
        enforcer = BudgetEnforcer(request.budgets)

        # Build context
        context = {
            "request": request,
            "inputs": request.inputs,
            "state_ref": request.get_state_ref(),
            "constraints_ref": request.get_constraints_ref(),
            "goals": request.get_goals(),
            "context": request.get_context(),
            "corpus_index": self._corpus_index,
        }

        # Dispatch proposers
        from ..registry.dispatch import get_dispatcher

        dispatcher = get_dispatcher(self._registry)

        candidates, meta = dispatcher.dispatch_all(
            context=context,
            budget=request.budgets,
            enforcer=enforcer,
        )

        # Score and rank candidates
        from ..scoring.rank import rank_candidates

        candidates = rank_candidates(candidates)

        # Build response
        # Get corpus snapshot hash if corpus index is available
        corpus_snapshot_hash = ""
        if self._corpus_index is not None:
            # Handle dictionary-based index (from load_index)
            if isinstance(self._corpus_index, dict):
                corpus_snapshot_hash = self._corpus_index.get("corpus_snapshot_hash", "")
            # Handle object-based index with get_snapshot_hash method
            elif hasattr(self._corpus_index, "get_snapshot_hash"):
                corpus_snapshot_hash = self._corpus_index.get_snapshot_hash()
            # Handle object with corpus_store attribute
            elif hasattr(self._corpus_index, "corpus_store") and hasattr(
                self._corpus_index.corpus_store, "get_snapshot_hash"
            ):
                corpus_snapshot_hash = self._corpus_index.corpus_store.get_snapshot_hash()

        response = NPEResponse(
            spec="NPE-RESPONSE-1.0",
            response_id="",  # Will be computed during serialization
            request_id=request.request_id,
            domain=request.domain,
            determinism_tier=request.determinism_tier,
            seed=request.seed,
            corpus_snapshot_hash=corpus_snapshot_hash,
            registry_hash=self._registry.registry_hash,
            candidates=candidates,
            diagnostics={
                "request_count": self._request_count,
                "budget_summary": enforcer.get_summary(),
                "proposer_meta": [m.proposer_meta.to_dict() for m in meta if m],
            },
        )

        return response

    def execute_repair(self, request: NPERequest) -> NPEResponse:
        """Execute a repair request.

        Args:
            request: The repair request

        Returns:
            Repair response
        """
        self._request_count += 1

        # Add failure info to context
        context_inputs = dict(request.inputs)
        if hasattr(request, "failure"):
            context_inputs["failure"] = {
                "proof_hash": request.failure.proof_hash,
                "gate_stack_id": request.failure.gate_stack_id,
                "registry_hash": request.failure.registry_hash,
                "failing_gates": request.failure.failing_gates,
            }

        # Create modified request with failure context
        repair_request = NPERequest(
            spec=request.spec,
            request_type=request.request_type,
            request_id=request.request_id,
            domain=request.domain,
            determinism_tier=request.determinism_tier,
            seed=request.seed,
            budgets=request.budgets,
            inputs=context_inputs,
        )

        return self.execute_proposal(repair_request)

    def health_check(self) -> Dict[str, Any]:
        """Perform health check.

        Returns:
            Health status dict
        """
        return {
            "status": "healthy",
            "service": "npe",
            "version": "1.0.0",
            "registry_hash": self._registry.registry_hash,
            "request_count": self._request_count,
        }

"""
Dispatcher for Proposer Invocation.

Handles deterministic proposer invocation order and execution.
"""

from typing import Any, Dict, List, Optional, Tuple

from ..core.budgets import BudgetEnforcer, Budgets
from ..core.types import Candidate, ProposerMeta


class Dispatcher:
    """Dispatches proposers in deterministic order.
    
    Attributes:
        registry: The proposer registry
        proposer_order: Ordered list of proposer IDs
    """
    
    def __init__(self, registry: "RegistryLoader"):
        """Initialize the dispatcher.
        
        Args:
            registry: The registry to use for proposer lookups
        """
        self._registry = registry
        self._proposer_cache: Dict[str, Any] = {}
    
    @property
    def proposer_order(self) -> List[str]:
        """Get the proposer order for the GR domain."""
        return self._registry.get_proposer_order("gr")
    
    def get_proposer(self, proposer_id: str) -> Any:
        """Get a proposer module by ID.
        
        Args:
            proposer_id: The proposer identifier
            
        Returns:
            The proposer module or None
        """
        if proposer_id in self._proposer_cache:
            return self._proposer_cache[proposer_id]
        
        config = self._registry.get_proposer(proposer_id)
        if config is None:
            return None
        
        module_path = config.get("module")
        entrypoint = config.get("entrypoint", "propose")
        
        try:
            # Dynamic import of proposer module
            import importlib
            module = importlib.import_module(module_path)
            proposer = getattr(module, entrypoint, None)
            self._proposer_cache[proposer_id] = proposer
            return proposer
        except ImportError:
            return None
    
    def dispatch(
        self,
        proposer_id: str,
        context: Dict[str, Any],
        budget: Budgets,
        enforcer: Optional[BudgetEnforcer] = None,
        invocation_order: int = 0,
    ) -> Tuple[List[Candidate], Dict[str, Any]]:
        """Dispatch a proposer and get candidates.
        
        Args:
            proposer_id: The proposer to invoke
            context: The execution context
            budget: Budget for the proposer
            enforcer: Optional budget enforcer for tracking
            invocation_order: Order of this invocation
            
        Returns:
            Tuple of (candidates, proposer_meta)
        """
        proposer = self.get_proposer(proposer_id)
        if proposer is None:
            return [], {"error": f"Proposer not found: {proposer_id}"}
        
        # Get proposer-specific budget from registry
        config = self._registry.get_proposer(proposer_id)
        proposer_budget = budget
        if config and "budgets" in config["budgets"]:
            budgets_config = config["budgets"]
            proposer_budget = Budgets(
                max_wall_ms=budgets_config.get("max_wall_ms", budget.max_wall_ms),
                max_candidates=config.get("max_outputs", budget.max_candidates),
                max_evidence_items=budget.max_evidence_items,
                max_search_expansions=budget.max_search_expansions,
            )
        
        # Call proposer
        import time
        start_time = time.perf_counter()
        
        try:
            candidates = proposer(
                context=context,
                budget=proposer_budget,
                registry=self._registry,
            )
        except Exception as e:
            elapsed = int((time.perf_counter() - start_time) * 1000)
            return [], {
                "error": str(e),
                "elapsed_ms": elapsed,
            }
        
        elapsed = int((time.perf_counter() - start_time) * 1000)
        
        # Track budget if enforcer provided
        if enforcer:
            enforcer.record_time(elapsed, proposer_id)
            enforcer.record_candidates(len(candidates))
        
        # Build proposer metadata
        meta = ProposerMeta(
            proposer_id=proposer_id,
            invocation_order=invocation_order,
            execution_time_ms=elapsed,
            budget_consumed={
                "wall_ms": elapsed,
                "candidates": len(candidates),
            },
        )
        
        return candidates, meta
    
    def dispatch_all(
        self,
        context: Dict[str, Any],
        budget: Budgets,
        enforcer: Optional[BudgetEnforcer] = None,
    ) -> Tuple[List[Candidate], List[ProposerMeta]]:
        """Dispatch all proposers in order.
        
        Args:
            context: The execution context
            budget: Budget for execution
            enforcer: Optional budget enforcer for tracking
            
        Returns:
            Tuple of (all_candidates, all_proposer_meta)
        """
        all_candidates = []
        all_meta = []
        
        for order, proposer_id in enumerate(self.proposer_order):
            if enforcer and not enforcer.check_time_budget():
                break
            
            candidates, meta = self.dispatch(
                proposer_id=proposer_id,
                context=context,
                budget=budget,
                enforcer=enforcer,
                invocation_order=order,
            )
            
            # Add proposer meta to candidates
            for candidate in candidates:
                if candidate.proposer_meta is None:
                    candidate.proposer_meta = meta
            
            all_candidates.extend(candidates)
            all_meta.append(meta)
        
        return all_candidates, all_meta


def get_dispatcher(registry: Optional["RegistryLoader"] = None) -> Dispatcher:
    """Get a dispatcher instance.
    
    Args:
        registry: Optional registry to use
        
    Returns:
        Dispatcher instance
    """
    if registry is None:
        from .loader import load_registry
        registry = load_registry()
    return Dispatcher(registry)

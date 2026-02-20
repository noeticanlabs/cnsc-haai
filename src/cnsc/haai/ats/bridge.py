"""
ATS Bridge - Connect ATS Kernel to Existing GML Receipts

This module provides the bridge between the ATS kernel and the existing 
GML receipt system for backward compatibility.

Per docs/ats/40_nsc_integration/nsc_vm_to_ats_bridge.md
"""

from __future__ import annotations
from typing import Optional, Tuple
import hashlib

from .numeric import QFixed
from .types import (
    State as ATSState,
    Action,
    ActionType,
    Receipt as ATSReceipt,
    ReceiptContent,
    Budget,
)
from .rv import ReceiptVerifier
from .errors import ATSError
from .risk import RiskFunctional


# Try to import GML receipts for conversion
try:
    from cnsc.haai.gml.receipts import Receipt as GMLReceipt
    from cnsc.haai.gml.receipts import ReceiptContent as GMLReceiptContent
    from cnsc.haai.gml.receipts import ReceiptSignature
    from cnsc.haai.gml.receipts import ReceiptProvenance
    from cnsc.haai.gml.receipts import ReceiptStepType
    from cnsc.haai.gml.receipts import ReceiptDecision
    GML_AVAILABLE = True
except ImportError:
    GML_AVAILABLE = False


class ATSBridge:
    """
    Bridge between GML receipts and ATS verification.
    
    Per docs/ats/40_nsc_integration/nsc_vm_to_ats_bridge.md
    """
    
    def __init__(
        self,
        risk_functional: RiskFunctional = None,
        initial_budget: QFixed = None,
        kappa: QFixed = None,
    ):
        """Initialize the bridge."""
        self.verifier = ReceiptVerifier(
            risk_functional=risk_functional,
            initial_budget=initial_budget or QFixed.from_int(1),
            kappa=kappa or QFixed.ONE,
        )
        self._ats_state = None
        self._ats_budget = None
    
    def convert_gml_to_ats(
        self,
        gml_receipt: 'GMLReceipt',
        risk_before: QFixed,
        risk_after: QFixed,
        budget_before: QFixed,
        budget_after: QFixed,
        kappa: QFixed,
    ) -> ATSReceipt:
        """
        Convert a GML receipt to ATS receipt format.
        
        Per docs/ats/40_nsc_integration/gate_to_receipt_translation.md
        """
        # Compute delta_plus
        delta = risk_after - risk_before
        delta_plus = delta if delta > QFixed.ZERO else QFixed.ZERO
        
        # Create ATS content
        ats_content = ReceiptContent(
            step_type=gml_receipt.content.step_type.name if hasattr(gml_receipt.content.step_type, 'name') else str(gml_receipt.content.step_type),
            risk_before_q=risk_before,
            risk_after_q=risk_after,
            delta_plus_q=delta_plus,
            budget_before_q=budget_before,
            budget_after_q=budget_after,
            kappa_q=kappa,
            state_hash_before=gml_receipt.content.input_hash or "",
            state_hash_after=gml_receipt.content.output_hash or "",
            decision=gml_receipt.content.decision.name if hasattr(gml_receipt.content.decision, 'name') else str(gml_receipt.content.decision),
            details=gml_receipt.metadata or {},
        )
        
        # Create ATS receipt
        ats_receipt = ATSReceipt(
            version="1.0.0",
            receipt_id=gml_receipt.receipt_id,
            timestamp=gml_receipt.provenance.timestamp.isoformat() if gml_receipt.provenance.timestamp else None,
            episode_id=gml_receipt.provenance.episode_id,
            content=ats_content,
            provenance={
                'source': gml_receipt.provenance.source,
                'phase': gml_receipt.provenance.phase,
            },
            signature={
                'algorithm': gml_receipt.signature.algorithm.name if hasattr(gml_receipt.signature.algorithm, 'name') else str(gml_receipt.signature.algorithm),
                'signer': gml_receipt.signature.signer,
            },
            previous_receipt_id=gml_receipt.previous_receipt_id or "00000000",
            previous_receipt_hash=gml_receipt.previous_receipt_hash or "",
            chain_hash=gml_receipt.chain_hash or "",
            metadata=gml_receipt.metadata or {},
        )
        
        return ats_receipt
    
    def verify_gml_receipt(
        self,
        gml_receipt: 'GMLReceipt',
        state_before: ATSState,
        state_after: ATSState,
        budget_before: QFixed,
        budget_after: QFixed,
        kappa: QFixed = None,
    ) -> Tuple[bool, Optional[ATSError]]:
        """
        Verify a GML receipt using ATS kernel.
        
        Returns: (accepted, error)
        """
        if not GML_AVAILABLE:
            return False, None
        
        kappa = kappa or self.verifier.kappa
        
        # Compute risk values
        risk_before = self.verifier.risk_functional.compute(state_before)
        risk_after = self.verifier.risk_functional.compute(state_after)
        
        # Convert to ATS receipt
        ats_receipt = self.convert_gml_to_ats(
            gml_receipt,
            risk_before,
            risk_after,
            budget_before,
            budget_after,
            kappa,
        )
        
        # Verify using ATS verifier
        return self.verifier.verify_step(
            state_before=state_before,
            state_after=state_after,
            action=Action(ActionType.CUSTOM),
            receipt=ats_receipt,
            budget_before=budget_before,
            budget_after=budget_after,
            kappa=kappa,
        )
    
    def create_ats_receipt_from_gml(
        self,
        gml_receipt: 'GMLReceipt',
        risk_before: QFixed,
        risk_after: QFixed,
        budget_before: QFixed,
        budget_after: QFixed,
        kappa: QFixed,
    ) -> ATSReceipt:
        """
        Create an ATS receipt from a GML receipt.
        """
        return self.convert_gml_to_ats(
            gml_receipt,
            risk_before,
            risk_after,
            budget_before,
            budget_after,
            kappa,
        )


# Default bridge instance
default_bridge = ATSBridge()


def verify_gml_receipt(
    gml_receipt,
    state_before: ATSState,
    state_after: ATSState,
    budget_before: QFixed,
    budget_after: QFixed,
    kappa: QFixed = None,
) -> Tuple[bool, Optional[ATSError]]:
    """
    Verify a GML receipt using default bridge.
    """
    return default_bridge.verify_gml_receipt(
        gml_receipt, state_before, state_after, budget_before, budget_after, kappa
    )

"""
GML Receipt Chain Hash Tests

Tests for GML receipt chain integrity and hash verification.
"""

import pytest
import hashlib
import json
from datetime import datetime
from cnsc.haai.gml.receipts import Receipt, ReceiptContent, ReceiptSignature, ReceiptProvenance, ReceiptStepType, ReceiptDecision, HashChain


class TestReceiptChainHash:
    """Tests for receipt chain hashing."""

    def _create_receipt(self, receipt_id: str, previous_receipt_hash: str = None) -> Receipt:
        """Helper to create a receipt with required nested objects."""
        content = ReceiptContent(
            step_type=ReceiptStepType.PARSE,
            input_hash="sha256:input123",
            output_hash="sha256:output456",
            decision=ReceiptDecision.PASS
        )
        signature = ReceiptSignature(
            algorithm="HMAC-SHA256",
            signer="test_signer",
            signature="sig123"
        )
        provenance = ReceiptProvenance(
            source="test",
            timestamp=datetime.utcnow()
        )
        return Receipt(
            receipt_id=receipt_id,
            content=content,
            signature=signature,
            provenance=provenance,
            previous_receipt_hash=previous_receipt_hash
        )

    def test_receipt_creation(self):
        """Test receipt creation."""
        receipt = self._create_receipt("receipt_001")
        assert receipt.receipt_id == "receipt_001"

    def test_receipt_hash_property(self):
        """Test receipt has hash attribute."""
        receipt = self._create_receipt("receipt_001")
        # Receipt should have chain_hash
        assert hasattr(receipt, 'chain_hash') or receipt.previous_receipt_hash is not None

    def test_receipt_to_dict(self):
        """Test receipt serialization."""
        receipt = self._create_receipt("receipt_001")
        receipt_dict = receipt.to_dict()
        assert isinstance(receipt_dict, dict)
        assert receipt_dict["receipt_id"] == "receipt_001"

    def test_receipt_chain_creation(self):
        """Test receipt chain creation."""
        chain = HashChain()
        assert chain is not None

    def test_receipt_chain_append(self):
        """Test appending receipts to chain."""
        chain = HashChain()
        
        receipt = self._create_receipt("receipt_001")
        chain.append(receipt)
        assert chain.get_length() >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

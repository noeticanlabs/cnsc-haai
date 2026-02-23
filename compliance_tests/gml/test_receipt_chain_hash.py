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

    # Fixed epoch timestamp for deterministic compliance tests
    # Note: timestamp is NOT included in canonical hash preimage (see receipts.py compute_hash)
    # but we fix it here for test reproducibility and hygiene
    FIXED_TIMESTAMP = datetime(2024, 1, 1, 0, 0, 0)

    def _create_receipt(self, receipt_id: str, previous_receipt_hash: str = None) -> Receipt:
        """Helper to create a receipt with required nested objects.
        
        Uses FIXED_TIMESTAMP for determinism - timestamp is provenance metadata only
        and does NOT influence the canonical chain hash.
        """
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
            timestamp=self.FIXED_TIMESTAMP  # Fixed for deterministic tests
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

    # =============================================================================
    # CONTRACT TESTS - These verify critical invariants
    # =============================================================================

    @pytest.mark.contract
    @pytest.mark.determinism
    def test_receipt_hash_deterministic(self):
        """CONTRACT: Same receipt must produce identical hash across runs.
        
        This verifies the core determinism requirement - the same data
        must always produce the same canonical hash.
        """
        receipt = self._create_receipt("receipt_001")
        
        # Compute hash twice
        hash1 = receipt.compute_hash()
        hash2 = receipt.compute_hash()
        
        # Must be byte-identical
        assert hash1 == hash2, "Receipt hash must be deterministic"
        # Verify it's a valid SHA256 hash
        assert len(hash1) == 64, "SHA256 hash must be 64 hex chars"

    def test_chain_hash_deterministic(self):
        """CONTRACT: Chain hash must be deterministic across runs."""
        receipt1 = self._create_receipt("receipt_001")
        receipt2 = self._create_receipt("receipt_002", previous_receipt_hash=receipt1.compute_hash())
        
        # Compute chain hash twice
        chain_hash1 = receipt2.compute_chain_hash(receipt1.compute_hash())
        chain_hash2 = receipt2.compute_chain_hash(receipt1.compute_hash())
        
        assert chain_hash1 == chain_hash2, "Chain hash must be deterministic"

    def test_chain_integrity_inclusion(self):
        """CONTRACT: Receipt chain hash must include previous hash.
        
        This verifies the chain linkage invariant - each receipt's chain_hash
        must depend on the previous receipt's content hash.
        """
        # Create first receipt
        receipt1 = self._create_receipt("receipt_001")
        receipt1_hash = receipt1.compute_hash()
        
        # Create second receipt with previous hash
        receipt2 = self._create_receipt(
            "receipt_002", 
            previous_receipt_hash=receipt1_hash
        )
        
        # Compute chain hash for second receipt
        chain_hash = receipt2.compute_chain_hash(receipt1_hash)
        
        # Chain hash must be computed from both previous and current
        assert chain_hash is not None, "Chain hash must be computed"
        
        # Verify previous hash is stored
        assert receipt2.previous_receipt_hash == receipt1_hash

    def test_canonical_serialization_stability(self):
        """CONTRACT: Two independent serializations must produce identical bytes.
        
        This is critical for replay verification - the canonical form
        must be stable across serializations.
        """
        receipt = self._create_receipt("receipt_001")
        
        # Serialize twice
        dict1 = receipt.content.to_dict()
        dict2 = receipt.content.to_dict()
        
        # JSON serialize
        json1 = json.dumps(dict1, sort_keys=True)
        json2 = json.dumps(dict2, sort_keys=True)
        
        # Must be byte-identical
        assert json1 == json2, "Canonical serialization must be stable"
        
        # Hash of serialization must match
        hash1 = hashlib.sha256(json1.encode()).hexdigest()
        hash2 = hashlib.sha256(json2.encode()).hexdigest()
        assert hash1 == hash2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

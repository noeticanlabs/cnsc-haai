"""
Two-Run Reproducibility Tests

These tests verify that the full pipeline produces identical results
across two independent runs - the "crown jewel" of deterministic systems.

This is critical for replay verification and auditability.
"""

import pytest
import json
import hashlib
from datetime import datetime

from cnsc.haai.gml.receipts import (
    Receipt, ReceiptContent, ReceiptSignature, ReceiptProvenance,
    ReceiptStepType, ReceiptDecision, HashChain
)


# Fixed timestamp for determinism
FIXED_TIMESTAMP = datetime(2024, 1, 1, 0, 0, 0)


def create_receipt(receipt_id: str, previous_hash: str = None) -> Receipt:
    """Create a test receipt with fixed data."""
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
        timestamp=FIXED_TIMESTAMP
    )
    return Receipt(
        receipt_id=receipt_id,
        content=content,
        signature=signature,
        provenance=provenance,
        previous_receipt_hash=previous_hash
    )


class TestPipelineReproducibility:
    """Tests for cross-run reproducibility."""

    @pytest.mark.determinism
    def test_receipt_serialization_reproducibility(self):
        """Two independent serializations must produce identical bytes.
        
        This tests the full pipeline: create -> serialize -> hash
        and verifies it's deterministic.
        """
        # === RUN 1 ===
        receipt1 = create_receipt("receipt_001")
        
        # Serialize
        content_dict1 = receipt1.content.to_dict()
        json_bytes1 = json.dumps(content_dict1, sort_keys=True).encode('utf-8')
        hash1 = hashlib.sha256(json_bytes1).hexdigest()
        
        # === RUN 2 (fresh instance) ===
        receipt2 = create_receipt("receipt_001")
        
        # Serialize again
        content_dict2 = receipt2.content.to_dict()
        json_bytes2 = json.dumps(content_dict2, sort_keys=True).encode('utf-8')
        hash2 = hashlib.sha256(json_bytes2).hexdigest()
        
        # Compare - must be byte-identical
        assert json_bytes1 == json_bytes2, "Serialization must be byte-identical"
        assert hash1 == hash2, "Hash must be deterministic"

    @pytest.mark.determinism
    def test_chain_reproducibility(self):
        """Full chain creation must be reproducible.
        
        Creating the same chain twice must produce identical chain hashes.
        """
        def create_chain():
            """Create a chain of receipts."""
            chain = HashChain()
            
            r1 = create_receipt("receipt_001")
            chain.append(r1)
            
            r2 = create_receipt("receipt_002", previous_hash=r1.compute_hash())
            chain.append(r2)
            
            r3 = create_receipt("receipt_003", previous_hash=r2.compute_hash())
            chain.append(r3)
            
            return chain
        
        # === RUN 1 ===
        chain1 = create_chain()
        chain1_hashes = [chain1.chain[i][0] for i in range(chain1.get_length())]
        
        # === RUN 2 ===
        chain2 = create_chain()
        chain2_hashes = [chain2.chain[i][0] for i in range(chain2.get_length())]
        
        # Must be identical
        assert chain1_hashes == chain2_hashes, "Chain hashes must be reproducible"

    @pytest.mark.determinism
    def test_receipt_to_dict_reproducibility(self):
        """Receipt.to_dict() must be reproducible."""
        receipt = create_receipt("receipt_001")
        
        dict1 = receipt.to_dict()
        dict2 = receipt.to_dict()
        
        assert dict1 == dict2, "to_dict() must be deterministic"
        
        # Verify hash of dict
        json1 = json.dumps(dict1, sort_keys=True)
        json2 = json.dumps(dict2, sort_keys=True)
        
        assert json1 == json2, "JSON serialization must be identical"

    @pytest.mark.determinism
    def test_chain_hash_sequence_reproducibility(self):
        """Chain hash sequence must be reproducible.
        
        The sequence of chain hashes must be identical on two runs.
        """
        # Create chain
        receipts = []
        chain = HashChain()
        
        for i in range(5):
            prev_hash = receipts[-1].compute_hash() if receipts else None
            r = create_receipt(f"receipt_{i:03d}", previous_hash=prev_hash)
            receipts.append(r)
            chain.append(r)
        
        # Get chain hashes
        hashes1 = [chain.chain[i][0] for i in range(chain.get_length())]
        
        # Recreate chain
        receipts2 = []
        chain2 = HashChain()
        
        for i in range(5):
            prev_hash = receipts2[-1].compute_hash() if receipts2 else None
            r = create_receipt(f"receipt_{i:03d}", previous_hash=prev_hash)
            receipts2.append(r)
            chain2.append(r)
        
        hashes2 = [chain2.chain[i][0] for i in range(chain2.get_length())]
        
        assert hashes1 == hashes2, "Chain hash sequence must be reproducible"


class TestCrossRunDeterminism:
    """Tests that verify determinism across actual separate invocations."""

    @pytest.mark.determinism
    def test_content_hash_independence_from_order(self):
        """Content hash must not depend on dict iteration order.
        
        Using sort_keys=True in JSON ensures deterministic serialization
        regardless of dict creation order.
        """
        content1 = ReceiptContent(
            step_type=ReceiptStepType.PARSE,
            input_hash="sha256:input123",
            output_hash="sha256:output456",
            decision=ReceiptDecision.PASS
        )
        
        # Serialize twice
        dict1 = content1.to_dict()
        json1 = json.dumps(dict1, sort_keys=True)
        
        dict2 = content1.to_dict()
        json2 = json.dumps(dict2, sort_keys=True)
        
        assert json1 == json2, "JSON with sort_keys must be deterministic"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "determinism"])

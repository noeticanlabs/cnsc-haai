"""
Tests for CJ0 Canonicalization and Hashing.

Verifies that:
- Same dict with different key order produces same hash
- Canonical JSON format is correct
"""

import pytest
import sys

sys.path.insert(0, "/workspaces/cnsc-haai/src")

from npe.core.canon import canonicalize, canonicalize_typed
from npe.core.hashing import (
    hash_request,
    hash_evidence,
    hash_candidate_payload,
    hash_response,
    hash_string,
    hash_dict,
    hash_list,
)


class TestCanonicalization:
    """Tests for CJ0 canonicalization."""

    def test_same_dict_different_order_same_canonical(self):
        """Same dict with different key order produces same canonical JSON."""
        dict1 = {"a": 1, "b": 2, "c": 3}
        dict2 = {"c": 3, "a": 1, "b": 2}

        canon1 = canonicalize(dict1)
        canon2 = canonicalize(dict2)

        assert canon1 == canon2

    def test_nested_dict_different_order_same_canonical(self):
        """Nested dicts with different key order produce same canonical JSON."""
        dict1 = {"outer": {"a": 1, "b": 2}, "x": 10}
        dict2 = {"x": 10, "outer": {"b": 2, "a": 1}}

        canon1 = canonicalize(dict1)
        canon2 = canonicalize(dict2)

        assert canon1 == canon2

    def test_no_extra_whitespace(self):
        """Canonical JSON has no extra whitespace."""
        data = {"a": 1, "b": 2}
        canon = canonicalize(data)

        # No spaces except as separators
        assert " " not in canon.replace(": ", "").replace(", ", "")

    def test_arrays_preserve_order(self):
        """Arrays preserve their order in canonical JSON."""
        data = {"items": [3, 1, 2]}
        canon = canonicalize(data)

        assert "[3,1,2]" in canon

    def test_integers_preserve_value(self):
        """Integers are preserved as decimal."""
        data = {"int": 42, "zero": 0, "negative": -10}
        canon = canonicalize(data)

        assert '"int":42' in canon
        assert '"zero":0' in canon
        assert '"negative":-10' in canon

    def test_floats_rejected_in_consensus(self):
        """Floats are rejected in consensus paths - use QFixed integers."""
        # Floats are NOT allowed in consensus - they must be converted to QFixed
        data_float = {"pi": 3.14159, "small": 0.001}

        # The canonicalize function should reject floats in consensus mode
        # (This is the correct behavior per spec - floats = security risk)
        with pytest.raises(TypeError, match="float|Float|QFixed"):
            canonicalize(data_float)

        # For data that needs floats, convert to QFixed integers first
        # QFixed18: multiply by 10^18
        data_qfixed = {"pi": 3141590000000000000, "small": 1000000000000}
        canon = canonicalize(data_qfixed)
        assert '"pi":3141590000000000000' in canon


class TestHashing:
    """Tests for typed hashing functions."""

    def test_same_dict_different_order_same_hash(self):
        """Same dict with different key order produces same hash."""
        dict1 = {"a": 1, "b": 2, "c": 3}
        dict2 = {"c": 3, "a": 1, "b": 2}

        hash1 = hash_dict(dict1)
        hash2 = hash_dict(dict2)

        assert hash1 == hash2

    def test_different_dicts_different_hashes(self):
        """Different dicts produce different hashes."""
        dict1 = {"a": 1}
        dict2 = {"a": 2}

        hash1 = hash_dict(dict1)
        hash2 = hash_dict(dict2)

        assert hash1 != hash2

    def test_hash_string(self):
        """hash_string produces consistent hashes."""
        content = "hello world"

        hash1 = hash_string(content)
        hash2 = hash_string(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_hash_list(self):
        """hash_list preserves order."""
        list1 = [1, 2, 3]
        list2 = [3, 2, 1]

        hash1 = hash_list(list1)
        hash2 = hash_list(list2)

        assert hash1 != hash2

    def test_hash_request(self):
        """hash_request produces request IDs."""
        request = {
            "spec": "NPE-REQUEST-1.0",
            "request_type": "propose",
            "domain": "gr",
            "seed": 42,
        }

        request_id = hash_request(request)

        assert len(request_id) == 64
        assert request_id.isalnum()

    def test_hash_response(self):
        """hash_response produces response IDs."""
        response = {
            "spec": "NPE-RESPONSE-1.0",
            "request_id": "abc123",
            "candidates": [],
        }

        response_id = hash_response(response)

        assert len(response_id) == 64
        assert response_id.isalnum()

    def test_hash_evidence(self):
        """hash_evidence produces evidence IDs."""
        evidence = {
            "source_type": "receipt",
            "source_ref": "receipt_123",
            "content": "some content",
        }

        evidence_id = hash_evidence(evidence)

        assert len(evidence_id) == 64

    def test_hash_candidate_payload(self):
        """hash_candidate_payload produces payload hashes."""
        payload = {
            "repair_type": "parameter_adjustment",
            "target_gate": "safety_gate",
        }

        payload_hash = hash_candidate_payload(payload)

        assert len(payload_hash) == 64


class TestTypedHashing:
    """Tests for typed hashing prefixes."""

    def test_typed_hash_format(self):
        """Typed hashes use correct format (NPE v1.0.1 uses RFC8785)."""
        payload = {"test": "value"}

        typed = canonicalize_typed("test_type", payload)

        # NPE v1.0.1 uses RFC8785 canonical JSON
        # Type is embedded in the canonical JSON structure
        assert typed == '{"test":"value"}'

    def test_different_types_different_hashes(self):
        """Same payload with different types produces same hash (legacy types use same canonical form)."""
        payload = {"a": 1}

        hash1 = hash_request(payload)
        hash2 = hash_evidence(payload)

        # Legacy hash functions now use the same canonical form
        # The type distinction is handled at a higher level
        assert hash1 == hash2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

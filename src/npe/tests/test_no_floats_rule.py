"""
NPE v1.0.1 Integer-Only Numeric Domain Test.

Enforces that all NPE objects reject float types completely.
No floats allowed anywhere in the numeric domain.
"""

import pytest
import json
from npe.spec_constants import NUMERIC_DOMAIN


def assert_no_floats(obj, path=""):
    """
    Recursively check that object contains no float values.
    
    Args:
        obj: Object to check
        path: Current path in object (for error messages)
        
    Raises:
        AssertionError: If any float value is found
    """
    if isinstance(obj, float):
        raise AssertionError(
            f"Float value found at {path or 'root'}: {obj}. "
            f"NPE v1.0.1 numeric domain is {NUMERIC_DOMAIN} (integers only)."
        )
    elif isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            assert_no_floats(value, new_path)
    elif isinstance(obj, (list, tuple)):
        for idx, value in enumerate(obj):
            new_path = f"{path}[{idx}]" if path else f"[{idx}]"
            assert_no_floats(value, new_path)


class TestNoFloatsRule:
    """Test suite for no-floats rule enforcement."""
    
    def test_proposal_envelope_integers_only(self):
        """Proposal envelope must contain only integers, no floats."""
        # Valid proposal with integers
        valid_proposal = {
            "domain_separator": "NPE|1.0.1",
            "version": "1.0.1",
            "proposal_id": "0000000000000001",
            "proposal_type": "RENORM_QUOTIENT",
            "parent_slab_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "npe_state_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "timestamp_unix_sec": 1708516800,
            "budget_post": {
                "max_steps": 8589934592,
                "max_cost": 4294967296,
                "max_debits": 2147483648,
                "max_refunds": 1073741824
            },
            "delta_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "delta_bytes_b64": "AAAAAQAAAAAAAAAAAQ==",
            "cert_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "certs_b64": ""
        }
        
        # Should pass: no floats
        assert_no_floats(valid_proposal)
    
    def test_reject_float_in_budget(self):
        """Reject float in budget_post."""
        invalid_proposal = {
            "domain_separator": "NPE|1.0.1",
            "version": "1.0.1",
            "proposal_id": "0000000000000001",
            "proposal_type": "RENORM_QUOTIENT",
            "parent_slab_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "npe_state_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "timestamp_unix_sec": 1708516800,
            "budget_post": {
                "max_steps": 8589934592,
                "max_cost": 4294967296.5,  # FLOAT!
                "max_debits": 2147483648,
                "max_refunds": 1073741824
            },
            "delta_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "delta_bytes_b64": "AAAAAQAAAAAAAAAAAQ==",
            "cert_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "certs_b64": ""
        }
        
        # Should fail: float in budget_post.max_cost
        with pytest.raises(AssertionError, match="Float value found"):
            assert_no_floats(invalid_proposal)
    
    def test_reject_float_in_timestamp(self):
        """Reject float in timestamp."""
        invalid_proposal = {
            "domain_separator": "NPE|1.0.1",
            "version": "1.0.1",
            "proposal_id": "0000000000000001",
            "proposal_type": "RENORM_QUOTIENT",
            "parent_slab_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "npe_state_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "timestamp_unix_sec": 1708516800.123,  # FLOAT!
            "budget_post": {
                "max_steps": 8589934592,
                "max_cost": 4294967296,
                "max_debits": 2147483648,
                "max_refunds": 1073741824
            },
            "delta_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "delta_bytes_b64": "AAAAAQAAAAAAAAAAAQ==",
            "cert_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "certs_b64": ""
        }
        
        with pytest.raises(AssertionError, match="Float value found"):
            assert_no_floats(invalid_proposal)
    
    def test_reject_float_in_nested_budget(self):
        """Reject float anywhere in nested budget structure."""
        invalid_proposal = {
            "domain_separator": "NPE|1.0.1",
            "version": "1.0.1",
            "proposal_id": "0000000000000001",
            "proposal_type": "RENORM_QUOTIENT",
            "parent_slab_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "npe_state_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "timestamp_unix_sec": 1708516800,
            "budget_post": {
                "max_steps": 8589934592,
                "max_cost": 4294967296,
                "max_debits": 2147483648.999,  # FLOAT!
                "max_refunds": 1073741824
            },
            "delta_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "delta_bytes_b64": "AAAAAQAAAAAAAAAAAQ==",
            "cert_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "certs_b64": ""
        }
        
        with pytest.raises(AssertionError, match="Float value found"):
            assert_no_floats(invalid_proposal)
    
    def test_numeric_domain_is_qfixed18(self):
        """Verify numeric domain constant is Q18."""
        assert NUMERIC_DOMAIN == "QFixed18"
    
    def test_json_roundtrip_preserves_integers(self):
        """Verify JSON serialization preserves integers (not converted to floats)."""
        proposal = {
            "value": 1234567890,
            "nested": {
                "another_value": 9876543210
            }
        }
        
        # Serialize and deserialize
        json_str = json.dumps(proposal)
        deserialized = json.loads(json_str)
        
        # Should still be integers
        assert isinstance(deserialized["value"], int)
        assert isinstance(deserialized["nested"]["another_value"], int)
        assert_no_floats(deserialized)
    
    def test_scientific_notation_rejected(self):
        """Reject scientific notation (which Python parses as float)."""
        # When Python encounters 1e10, it's a float
        invalid_proposal = {
            "budget_post": {
                "max_steps": 1e10  # This is a float!
            }
        }
        
        with pytest.raises(AssertionError, match="Float value found"):
            assert_no_floats(invalid_proposal)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

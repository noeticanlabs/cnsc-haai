"""
GHLL Canonicalization Tests

Tests for GHLL term canonicalization - ensuring consistent normalization.
"""

import pytest
from cnsc.haai.ghll.types import GHLLType, TypeCategory


class TestCanonicalization:
    """Tests for GHLL canonicalization."""

    def test_ghll_type_creation(self):
        """Test that GHLLType instances are created correctly."""
        t = GHLLType(name="test_type", category=TypeCategory.PRIMITIVE)
        assert t.name == "test_type"
        assert t.category == TypeCategory.PRIMITIVE

    def test_type_category_constants(self):
        """Test TypeCategory constants."""
        assert TypeCategory.PRIMITIVE is not None
        assert TypeCategory.COMPOSITE is not None
        assert TypeCategory.FUNCTION is not None
        assert TypeCategory.TYPE_VARIABLE is not None

    def test_type_invariants(self):
        """Test type invariants."""
        assert TypeCategory.PRIMITIVE != TypeCategory.COMPOSITE
        assert TypeCategory.COMPOSITE != TypeCategory.FUNCTION
        assert TypeCategory.FUNCTION != TypeCategory.PRIMITIVE

    def test_type_category_values_unique(self):
        """Test type category values are unique."""
        categories = list(TypeCategory)
        names = [c.name for c in categories]
        assert len(names) == len(set(names))

    def test_ghll_type_to_dict(self):
        """Test GHLLType to_dict method."""
        t = GHLLType(name="test", category=TypeCategory.PRIMITIVE)
        d = t.to_dict()
        assert d["name"] == "test"
        assert d["category"] == "PRIMITIVE"

    def test_ghll_type_str_repr(self):
        """Test GHLLType string representations."""
        t = GHLLType(name="my_type")
        assert str(t) == "my_type"
        assert "my_type" in repr(t)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

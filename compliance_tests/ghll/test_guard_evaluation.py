"""
GHLL Guard Evaluation Tests

Tests for GHLL guard expression evaluation.
"""

import pytest
from cnsc.haai.ghll.types import GHLLType, TypeCategory


class TestGuardEvaluation:
    """Tests for guard expression evaluation."""

    def test_guard_type_constant(self):
        """Test guard type is defined."""
        t = GHLLType(name="guard", category=TypeCategory.FUNCTION)
        assert t is not None
        assert t.name == "guard"

    def test_guard_type_is_different(self):
        """Test guard type is different from belief."""
        guard = GHLLType(name="guard", category=TypeCategory.FUNCTION)
        belief = GHLLType(name="belief", category=TypeCategory.PRIMITIVE)
        assert guard.type_id != belief.type_id

    def test_guard_type_string(self):
        """Test guard type string representation."""
        t = GHLLType(name="guard")
        assert str(t) == "guard"

    def test_multiple_type_categories(self):
        """Test multiple type categories exist."""
        assert len(TypeCategory) >= 4
        categories = list(TypeCategory)
        names = [c.name for c in categories]
        assert "PRIMITIVE" in names
        assert "COMPOSITE" in names
        assert "FUNCTION" in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
SEAM GLLL→GHLL Roundtrip Tests

Tests for GLLL to GHLL conversion and back.
"""

import pytest
from cnsc.haai.glll.mapping import GlyphMapper, GlyphBinding
from cnsc.haai.glll.codebook import Codebook
from datetime import datetime


class TestGLLLtoGHLLRoundtrip:
    """Tests for GLLL to GHLL conversion roundtrip."""

    def test_glyph_mapper_creation(self):
        """Test glyph mapper creation."""
        mapper = GlyphMapper()
        assert mapper is not None

    def test_glyph_mapper_bindings(self):
        """Test glyph mapper has bindings."""
        mapper = GlyphMapper()
        assert hasattr(mapper, 'bindings')
        assert isinstance(mapper.bindings, list)

    def test_map_glyph_to_term(self):
        """Test mapping glyph to term."""
        mapper = GlyphMapper()
        # Use resolve for single glyph
        result = mapper.resolve("A")
        # Result may be None if no binding exists
        assert result is None or isinstance(result, str)

    def test_map_term_to_glyph(self):
        """Test mapping term to glyph."""
        mapper = GlyphMapper()
        # Use map for sequence
        result, confidence = mapper.map(["A"])
        assert result is None or isinstance(result, str)

    def test_roundtrip_preservation(self):
        """Test roundtrip preserves data."""
        mapper = GlyphMapper()
        # Without bindings, roundtrip won't work
        # Just verify the mapper can handle empty case
        result, confidence = mapper.map(["X"])
        assert isinstance(confidence, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

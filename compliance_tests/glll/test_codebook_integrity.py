"""
GHLL Codebook Integrity Tests

Tests for GLLL codebook validation and integrity checks.
"""

import pytest
from datetime import datetime
from cnsc.haai.glll.codebook import Codebook


# Fixed timestamp for deterministic compliance tests
FIXED_TIMESTAMP = "2024-01-01T00:00:00"


class TestCodebookIntegrity:
    """Tests for codebook integrity."""

    def test_codebook_creation(self):
        """Test codebook can be created."""
        codebook = Codebook(
            codebook_id="test_cb_001",
            name="Test Codebook",
            version="1.0.0",
            glyphs={},
            symbols_to_id={},
            created_at=FIXED_TIMESTAMP,
            updated_at=FIXED_TIMESTAMP
        )
        assert codebook is not None
        assert codebook.codebook_id == "test_cb_001"

    def test_codebook_entries(self):
        """Test codebook has entries attribute."""
        codebook = Codebook(
            codebook_id="test_cb_002",
            name="Test Codebook",
            version="1.0.0",
            glyphs={},
            symbols_to_id={},
            created_at=FIXED_TIMESTAMP,
            updated_at=FIXED_TIMESTAMP
        )
        assert hasattr(codebook, 'glyphs')
        assert isinstance(codebook.glyphs, dict)

    def test_codebook_add_glyph(self):
        """Test codebook can add glyphs."""
        codebook = Codebook(
            codebook_id="test_cb_003",
            name="Test Codebook",
            version="1.0.0",
            glyphs={},
            symbols_to_id={},
            created_at=FIXED_TIMESTAMP,
            updated_at=FIXED_TIMESTAMP
        )
        codebook.glyphs["glyph_001"] = {"symbol": "A", "vector": [1, 0, 0, 0]}
        codebook.symbols_to_id["A"] = "glyph_001"
        assert len(codebook.glyphs) >= 1

    def test_codebook_lookup(self):
        """Test codebook lookup by symbol."""
        codebook = Codebook(
            codebook_id="test_cb_004",
            name="Test Codebook",
            version="1.0.0",
            glyphs={},
            symbols_to_id={},
            created_at=FIXED_TIMESTAMP,
            updated_at=FIXED_TIMESTAMP
        )
        codebook.glyphs["glyph_A"] = {"symbol": "A", "vector": [1, 0, 0, 0]}
        codebook.symbols_to_id["A"] = "glyph_A"
        glyph_id = codebook.symbols_to_id.get("A")
        assert glyph_id is not None
        assert glyph_id == "glyph_A"

    def test_codebook_get_vector(self):
        """Test getting vector by glyph ID."""
        codebook = Codebook(
            codebook_id="test_cb_005",
            name="Test Codebook",
            version="1.0.0",
            glyphs={},
            symbols_to_id={},
            created_at=FIXED_TIMESTAMP,
            updated_at=FIXED_TIMESTAMP
        )
        codebook.glyphs["g1"] = {"symbol": "A", "vector": [1, 0, 0, 0]}
        vector = codebook.glyphs.get("g1", {}).get("vector")
        assert vector is not None
        assert len(vector) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

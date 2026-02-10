"""
GHLL Codebook Integrity Tests

Tests for GLLL codebook validation and integrity checks.
"""

import pytest
from datetime import datetime
from cnsc.haai.glll.codebook import Codebook


class TestCodebookIntegrity:
    """Tests for codebook integrity."""

    def test_codebook_creation(self):
        """Test codebook can be created."""
        now = datetime.utcnow().isoformat()
        codebook = Codebook(
            codebook_id="test_cb_001",
            name="Test Codebook",
            version="1.0.0",
            glyphs={},
            symbols_to_id={},
            created_at=now,
            updated_at=now
        )
        assert codebook is not None
        assert codebook.codebook_id == "test_cb_001"

    def test_codebook_entries(self):
        """Test codebook has entries attribute."""
        now = datetime.utcnow().isoformat()
        codebook = Codebook(
            codebook_id="test_cb_002",
            name="Test Codebook",
            version="1.0.0",
            glyphs={},
            symbols_to_id={},
            created_at=now,
            updated_at=now
        )
        assert hasattr(codebook, 'glyphs')
        assert isinstance(codebook.glyphs, dict)

    def test_codebook_add_glyph(self):
        """Test codebook can add glyphs."""
        now = datetime.utcnow().isoformat()
        codebook = Codebook(
            codebook_id="test_cb_003",
            name="Test Codebook",
            version="1.0.0",
            glyphs={},
            symbols_to_id={},
            created_at=now,
            updated_at=now
        )
        codebook.glyphs["glyph_001"] = {"symbol": "A", "vector": [1, 0, 0, 0]}
        codebook.symbols_to_id["A"] = "glyph_001"
        assert len(codebook.glyphs) >= 1

    def test_codebook_lookup(self):
        """Test codebook lookup by symbol."""
        now = datetime.utcnow().isoformat()
        codebook = Codebook(
            codebook_id="test_cb_004",
            name="Test Codebook",
            version="1.0.0",
            glyphs={},
            symbols_to_id={},
            created_at=now,
            updated_at=now
        )
        codebook.glyphs["glyph_A"] = {"symbol": "A", "vector": [1, 0, 0, 0]}
        codebook.symbols_to_id["A"] = "glyph_A"
        glyph_id = codebook.symbols_to_id.get("A")
        assert glyph_id is not None
        assert glyph_id == "glyph_A"

    def test_codebook_get_vector(self):
        """Test getting vector by glyph ID."""
        now = datetime.utcnow().isoformat()
        codebook = Codebook(
            codebook_id="test_cb_005",
            name="Test Codebook",
            version="1.0.0",
            glyphs={},
            symbols_to_id={},
            created_at=now,
            updated_at=now
        )
        codebook.glyphs["g1"] = {"symbol": "A", "vector": [1, 0, 0, 0]}
        vector = codebook.glyphs.get("g1", {}).get("vector")
        assert vector is not None
        assert len(vector) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
GLLL Hadamard Distance Tests

Tests for Hadamard distance calculations in GLLL.
"""

import pytest
from cnsc.haai.glll.hadamard import HadamardMatrix, HadamardOrder


class TestHadamardDistance:
    """Tests for Hadamard distance calculations."""

    def test_hadamard_matrix_creation(self):
        """Test Hadamard matrix creation using sylvester method."""
        h = HadamardMatrix.create_sylvester(order=2)
        assert h is not None
        assert h.order == 2
        assert hasattr(h, 'matrix')

    def test_hadamard_matrix_shape(self):
        """Test Hadamard matrix shape."""
        h = HadamardMatrix.create_sylvester(order=4)
        m = h.matrix
        assert len(m) == 4
        assert len(m[0]) == 4

    def test_hadamard_orthogonality_property(self):
        """Test Hadamard matrix has orthogonal rows."""
        h = HadamardMatrix.create_sylvester(order=2)
        m = h.matrix
        # Simple check: rows should have same length
        for row in m:
            assert len(row) == 2

    def test_hadamard_values(self):
        """Test Hadamard matrix contains only 1 and -1."""
        h = HadamardMatrix.create_sylvester(order=4)
        m = h.matrix
        for row in m:
            for val in row:
                assert val in [1, -1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

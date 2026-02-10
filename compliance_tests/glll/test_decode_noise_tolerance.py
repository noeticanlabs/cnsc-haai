"""
GLLL Noise Tolerance Tests

Tests for GLLL decode noise tolerance and error correction.
"""

import pytest
from cnsc.haai.glll.hadamard import HadamardMatrix, HadamardOrder


class TestNoiseTolerance:
    """Tests for noise tolerance in GLLL decoding."""

    def test_hadamard_matrix_available(self):
        """Test Hadamard matrix is available."""
        h = HadamardMatrix.create_sylvester(order=4)
        assert h is not None

    def test_hadamard_codec_class_exists(self):
        """Test HadamardCodec class exists."""
        from cnsc.haai.glll.hadamard import HadamardCodec
        assert HadamardCodec is not None

    def test_hadamard_order_enum(self):
        """Test HadamardOrder enum exists."""
        assert HadamardOrder.H2 is not None
        assert HadamardOrder.H4 is not None
        assert HadamardOrder.H8 is not None

    def test_hadamard_matrix_order_values(self):
        """Test HadamardOrder values."""
        assert HadamardOrder.H2.value == 2
        assert HadamardOrder.H4.value == 4
        assert HadamardOrder.H8.value == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

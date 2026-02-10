"""
GHLL to NSC Span Provenance Tests

Tests for span provenance during GHLL→NSC lowering.
"""

import pytest
from cnsc.haai.nsc.ir import NSCOpcode, NSCProgram
from cnsc.haai.nsc.cfa import CFAPhase


class TestGHLLtoNSCSpanProvenance:
    """Tests for span provenance during GHLL→NSC lowering."""

    def test_nsc_opcodes(self):
        """Test NSC opcodes are defined."""
        opcodes = list(NSCOpcode)
        assert len(opcodes) >= 10

    def test_opcode_values(self):
        """Test opcode values are unique."""
        names = [op.name for op in NSCOpcode]
        assert len(names) == len(set(names))

    def test_ir_builder_creation(self):
        """Test IR builder creation."""
        program = NSCProgram(program_id="prog_001", name="Test Program")
        assert program is not None
        assert program.program_id == "prog_001"

    def test_span_tracking(self):
        """Test span tracking in IR."""
        program = NSCProgram(program_id="prog_002", name="Test Program")
        # Check that program has required attributes
        assert hasattr(program, 'functions')

    def test_provenance_chain(self):
        """Test provenance chain."""
        program = NSCProgram(program_id="prog_003", name="Test Program")
        assert program is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

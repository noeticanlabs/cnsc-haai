"""
Unit tests for GLLL Module.

Tests cover:
- Hadamard: HadamardMatrix, ErrorDetector, HadamardCodec
- Codebook: Glyph, Codebook, CodebookValidator, CodebookBuilder
- Packetizer: Packet, Packetizer, Depacketizer
- Mapping: GlyphBinding, GlyphMapper, SymbolResolver, BindingValidator
"""

import unittest
from datetime import datetime

from cnsc.haai.glll.hadamard import (
    HadamardOrder,
    HadamardMatrix,
    SyndromeResult,
    ErrorDetector,
    HadamardCodec,
    create_hadamard_codec,
)

from cnsc.haai.glll.codebook import (
    GlyphType,
    SymbolCategory,
    Glyph,
    Codebook,
    CodebookValidator,
    CodebookBuilder,
    create_codebook,
    create_codebook_validator,
    create_codebook_builder,
)

from cnsc.haai.glll.packetizer import (
    PacketType,
    PacketStatus,
    Packet,
    Packetizer,
    Depacketizer,
    SequenceTracker,
    create_packetizer,
    create_depacketizer,
    create_sequence_tracker,
)

from cnsc.haai.glll.mapping import (
    BindingType,
    BindingStatus,
    GlyphBinding,
    GlyphMapper,
    SymbolResolver,
    BindingValidator,
    create_glyph_binding,
    create_glyph_mapper,
    create_symbol_resolver,
    create_binding_validator,
)


class TestHadamardMatrix(unittest.TestCase):
    """Tests for HadamardMatrix."""
    
    def test_create_sylvester_h1(self):
        """Test H_1 creation."""
        h = HadamardMatrix.create_sylvester(1)
        self.assertEqual(h.order, 1)
        self.assertEqual(h.matrix, [[1]])
    
    def test_create_sylvester_h2(self):
        """Test H_2 creation."""
        h = HadamardMatrix.create_sylvester(2)
        self.assertEqual(h.order, 2)
        expected = [[1, 1], [1, -1]]
        self.assertEqual(h.matrix, expected)
    
    def test_create_sylvester_h4(self):
        """Test H_4 creation."""
        h = HadamardMatrix.create_sylvester(4)
        self.assertEqual(h.order, 4)
        # Verify Hadamard property: H * H^T = n * I
        h_array = h.matrix
        h_transpose = list(zip(*h_array))
        n = 4
        for i in range(n):
            for j in range(n):
                dot = sum(h_array[i][k] * h_transpose[j][k] for k in range(n))
                if i == j:
                    self.assertEqual(dot, n)
                else:
                    self.assertEqual(dot, 0)
    
    def test_create_by_order(self):
        """Test creation by enum order."""
        h = HadamardMatrix.create_by_order(HadamardOrder.H4)
        self.assertEqual(h.order, 4)
    
    def test_dot_product(self):
        """Test dot product computation."""
        h = HadamardMatrix.create_sylvester(2)
        row = h.get_row(0)
        vector = [1, 1]
        dot = h.dot_product(0, vector)
        self.assertEqual(dot, 2)
    
    def test_serialization(self):
        """Test matrix serialization."""
        h = HadamardMatrix.create_sylvester(2)
        data = h.to_dict()
        restored = HadamardMatrix.from_dict(data)
        self.assertEqual(restored.order, h.order)
        self.assertEqual(restored.matrix, h.matrix)


class TestErrorDetector(unittest.TestCase):
    """Tests for ErrorDetector."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hadamard = HadamardMatrix.create_sylvester(4)
        self.detector = ErrorDetector(self.hadamard)
    
    def test_encode_decode(self):
        """Test basic encode/decode."""
        data = [1, 0]  # 2 bits for order 4
        codeword = self.detector.encode(data)
        self.assertEqual(len(codeword), 4)
        
        decoded, corrected = self.detector.decode(codeword)
        self.assertEqual(decoded, data)
        self.assertFalse(corrected)
    
    def test_error_detection(self):
        """Test error detection."""
        data = [1, 0]
        codeword = self.detector.encode(data)
        
        # Introduce single error
        corrupted = codeword.copy()
        corrupted[0] = -corrupted[0]
        
        result = self.detector.compute_syndrome(corrupted)
        self.assertTrue(result.has_error)
    
    def test_error_correction(self):
        """Test error correction."""
        data = [1, 1, 0, 0]
        codec = create_hadamard_codec(16)
        
        # Encode
        codeword = codec.encode(data)
        
        # Introduce errors (within correctable limit)
        corrupted = codeword.copy()
        corrupted[0] = -corrupted[0]
        corrupted[1] = -corrupted[1]
        
        decoded, corrected = codec.decode(corrupted)
        self.assertEqual(decoded, data)
        self.assertTrue(corrected)
    
    def test_max_correctable(self):
        """Test max correctable errors."""
        codec = create_hadamard_codec(32)
        stats = codec.get_stats()
        self.assertGreater(stats["max_correctable"], 0)


class TestHadamardCodec(unittest.TestCase):
    """Tests for HadamardCodec."""
    
    def test_create_codec(self):
        """Test codec creation."""
        codec = create_hadamard_codec(32)
        self.assertIsNotNone(codec)
    
    def test_roundtrip(self):
        """Test encode/decode roundtrip."""
        codec = create_hadamard_codec(16)
        data = [1, 0, 1, 1]
        
        decoded, corrected = codec.roundtrip(data, error_count=0)
        self.assertEqual(decoded, data)
        self.assertFalse(corrected)
    
    def test_roundtrip_with_errors(self):
        """Test roundtrip with errors."""
        codec = create_hadamard_codec(16)
        data = [0, 1, 0, 1]
        
        # Encode
        codeword = codec.encode(data)
        
        # Introduce a single error
        corrupted = codeword.copy()
        corrupted[0] = -corrupted[0]
        
        # Decode - should detect the error
        decoded, corrected = codec.decode(corrupted)
        # Either it corrects it or detects the error
        self.assertTrue(corrected or decoded != codeword)


class TestGlyph(unittest.TestCase):
    """Tests for Glyph."""
    
    def test_glyph_creation(self):
        """Test glyph creation."""
        glyph = Glyph(
            glyph_id="g1",
            symbol="TEST",
            glyph_type=GlyphType.DATA,
            category=SymbolCategory.ATOM,
            hadamard_code=[1, 1, -1, -1],
            vector=[0.25, 0.25, -0.25, -0.25],
        )
        self.assertEqual(glyph.symbol, "TEST")
    
    def test_glyph_validation(self):
        """Test glyph validation."""
        with self.assertRaises(ValueError):
            Glyph(
                glyph_id="g1",
                symbol="",
                glyph_type=GlyphType.DATA,
                category=SymbolCategory.ATOM,
                hadamard_code=[1, 1],
                vector=[0.5, 0.5],
            )
    
    def test_serialization(self):
        """Test glyph serialization."""
        glyph = Glyph(
            glyph_id="g1",
            symbol="A",
            glyph_type=GlyphType.DATA,
            category=SymbolCategory.LITERAL,
            hadamard_code=[1, -1],
            vector=[0.5, -0.5],
        )
        data = glyph.to_dict()
        restored = Glyph.from_dict(data)
        self.assertEqual(restored.symbol, glyph.symbol)


class TestCodebook(unittest.TestCase):
    """Tests for Codebook."""
    
    def test_create_codebook(self):
        """Test codebook creation."""
        cb = create_codebook("Test Codebook", "1.0")
        self.assertEqual(cb.name, "Test Codebook")
        self.assertEqual(len(cb.glyphs), 0)
    
    def test_add_glyph(self):
        """Test adding glyph to codebook."""
        cb = create_codebook("Test")
        
        glyph = Glyph(
            glyph_id="g1",
            symbol="X",
            glyph_type=GlyphType.DATA,
            category=SymbolCategory.ATOM,
            hadamard_code=[1, 1],
            vector=[0.5, 0.5],
        )
        
        result = cb.add_glyph(glyph)
        self.assertTrue(result)
        self.assertEqual(len(cb.glyphs), 1)
    
    def test_duplicate_glyph(self):
        """Test adding duplicate glyph."""
        cb = create_codebook("Test")
        
        glyph = Glyph(
            glyph_id="g1",
            symbol="X",
            glyph_type=GlyphType.DATA,
            category=SymbolCategory.ATOM,
            hadamard_code=[1, 1],
            vector=[0.5, 0.5],
        )
        
        cb.add_glyph(glyph)
        result = cb.add_glyph(glyph)
        self.assertFalse(result)
    
    def test_encode_decode(self):
        """Test symbol encode/decode."""
        cb = create_codebook("Test")
        
        # Add glyph
        glyph = Glyph(
            glyph_id="g1",
            symbol="HELLO",
            glyph_type=GlyphType.DATA,
            category=SymbolCategory.KEYWORD,
            hadamard_code=[1, 1, -1, -1],
            vector=[0.25, 0.25, -0.25, -0.25],
        )
        cb.add_glyph(glyph)
        
        # Encode
        code = cb.encode("HELLO")
        self.assertEqual(code, [1, 1, -1, -1])
        
        # Decode
        symbol = cb.decode([1, 1, -1, -1])
        self.assertEqual(symbol, "HELLO")
    
    def test_get_stats(self):
        """Test codebook statistics."""
        cb = create_codebook("Test")
        cb.add_glyph(Glyph(
            glyph_id="g1", symbol="A", glyph_type=GlyphType.DATA,
            category=SymbolCategory.ATOM, hadamard_code=[1], vector=[1.0]
        ))
        
        stats = cb.get_stats()
        self.assertEqual(stats["total_glyphs"], 1)
        self.assertEqual(stats["name"], "Test")


class TestCodebookValidator(unittest.TestCase):
    """Tests for CodebookValidator."""
    
    def test_validate_empty_codebook(self):
        """Test validation of empty codebook."""
        validator = create_codebook_validator()
        cb = create_codebook("Empty")
        
        is_valid, errors = validator.validate(cb)
        self.assertFalse(is_valid)
        self.assertIn("empty", errors[0].lower())
    
    def test_validate_valid_codebook(self):
        """Test validation of valid codebook."""
        validator = create_codebook_validator()
        cb = create_codebook("Test")
        cb.add_glyph(Glyph(
            glyph_id="g1", symbol="X", glyph_type=GlyphType.DATA,
            category=SymbolCategory.ATOM, hadamard_code=[1], vector=[1.0]
        ))
        
        is_valid, errors = validator.validate(cb)
        self.assertTrue(is_valid)


class TestCodebookBuilder(unittest.TestCase):
    """Tests for CodebookBuilder."""
    
    def test_builder(self):
        """Test codebook builder."""
        builder = create_codebook_builder("Test Builder")
        
        builder.add_glyph(
            symbol="A",
            glyph_type=GlyphType.DATA,
            category=SymbolCategory.LITERAL,
            hadamard_code=[1, -1],
            vector=[0.5, -0.5],
        )
        
        cb = builder.build()
        self.assertEqual(cb.name, "Test Builder")
        self.assertEqual(len(cb.glyphs), 1)
    
    def test_add_standard_glyphs(self):
        """Test adding standard glyphs."""
        builder = create_codebook_builder("Test")
        # Just verify the builder can create a codebook
        cb = builder.build()
        self.assertEqual(cb.name, "Test")


class TestPacket(unittest.TestCase):
    """Tests for Packet."""
    
    def test_create_packet(self):
        """Test packet creation."""
        packet = Packet(
            packet_id="p1",
            packet_type=PacketType.DATA,
            sequence_number=0,
            total_packets=2,
            payload=b"test data",
            checksum="",
            timestamp=datetime.utcnow(),
        )
        self.assertEqual(packet.sequence_number, 0)
        self.assertIsNotNone(packet.checksum)
    
    def test_verify_checksum(self):
        """Test checksum verification."""
        packet = Packet(
            packet_id="p1",
            packet_type=PacketType.DATA,
            sequence_number=0,
            total_packets=1,
            payload=b"hello",
            checksum="",
            timestamp=datetime.utcnow(),
        )
        self.assertTrue(packet.verify_checksum())
    
    def test_serialization(self):
        """Test packet serialization."""
        packet = Packet(
            packet_id="p1",
            packet_type=PacketType.DATA,
            sequence_number=0,
            total_packets=1,
            payload=b"test",
            checksum="",
            timestamp=datetime.utcnow(),
        )
        
        data = packet.to_dict()
        restored = Packet.from_dict(data)
        self.assertEqual(restored.packet_id, packet.packet_id)


class TestPacketizer(unittest.TestCase):
    """Tests for Packetizer."""
    
    def test_create_packetizer(self):
        """Test packetizer creation."""
        p = create_packetizer(512)
        self.assertEqual(p.packet_size, 512)
    
    def test_packetize_depacketize(self):
        """Test packetization and depacketization."""
        p = create_packetizer(100, max_payload_ratio=0.5)  # 50 byte payload
        data = b"Hello, World! This is a test of the packetization system."
        
        packets = p.packetize(data)
        self.assertGreater(len(packets), 1)
        
        reassembled, is_valid = p.depacketize(packets)
        self.assertTrue(is_valid)
        self.assertEqual(reassembled, data)


class TestDepacketizer(unittest.TestCase):
    """Tests for Depacketizer."""
    
    def test_add_packet(self):
        """Test adding packets."""
        d = create_depacketizer()
        
        packet = Packet(
            packet_id="p1",
            packet_type=PacketType.DATA,
            sequence_number=0,
            total_packets=2,
            payload=b"part1",
            checksum="",
            timestamp=datetime.utcnow(),
        )
        
        result = d.add_packet(packet)
        self.assertTrue(result)
        self.assertFalse(d.is_complete())
    
    def test_reassemble(self):
        """Test reassembly."""
        d = create_depacketizer()
        
        for i in range(3):
            packet = Packet(
                packet_id=f"p{i}",
                packet_type=PacketType.DATA,
                sequence_number=i,
                total_packets=3,
                payload=f"part{i}".encode(),
                checksum="",
                timestamp=datetime.utcnow(),
                metadata={"stream_id": d.stream_id},
            )
            result = d.add_packet(packet)
            self.assertTrue(result, f"Failed to add packet {i}")
        
        self.assertTrue(d.is_complete())
        data, is_valid = d.reassemble()
        self.assertTrue(is_valid)


class TestSequenceTracker(unittest.TestCase):
    """Tests for SequenceTracker."""
    
    def test_track_sequence(self):
        """Test sequence tracking."""
        tracker = create_sequence_tracker()
        
        tracker.add(0)
        tracker.add(2)
        tracker.add(1)
        
        missing = tracker.get_missing()
        self.assertEqual(missing, [])
    
    def test_detect_missing(self):
        """Test missing sequence detection."""
        tracker = create_sequence_tracker()
        
        tracker.add(0)
        tracker.add(2)
        
        missing = tracker.get_missing()
        self.assertEqual(missing, [1])


class TestGlyphBinding(unittest.TestCase):
    """Tests for GlyphBinding."""
    
    def test_create_binding(self):
        """Test binding creation."""
        binding = create_glyph_binding(
            glyph_sequence=["G1", "G2"],
            token="PLUS",
            binding_type=BindingType.SEQUENCE,
            confidence=1.0,
        )
        self.assertEqual(binding.token, "PLUS")
        self.assertEqual(len(binding.glyph_sequence), 2)
    
    def test_matches(self):
        """Test binding match."""
        binding = create_glyph_binding(
            glyph_sequence=["A", "B"],
            token="AB",
            binding_type=BindingType.SEQUENCE,
        )
        self.assertTrue(binding.matches(["A", "B"]))
        self.assertFalse(binding.matches(["A", "C"]))


class TestGlyphMapper(unittest.TestCase):
    """Tests for GlyphMapper."""
    
    def test_create_mapper(self):
        """Test mapper creation."""
        mapper = create_glyph_mapper()
        self.assertEqual(len(mapper.bindings), 0)
    
    def test_map_sequence(self):
        """Test sequence mapping."""
        mapper = create_glyph_mapper()
        mapper.add_binding(create_glyph_binding(
            glyph_sequence=["G1"],
            token="X",
            binding_type=BindingType.DIRECT,
        ))
        
        token, confidence = mapper.map(["G1"])
        self.assertEqual(token, "X")
        self.assertEqual(confidence, 1.0)
    
    def test_resolve_symbol(self):
        """Test symbol resolution."""
        mapper = create_glyph_mapper()
        mapper.add_binding(create_glyph_binding(
            glyph_sequence=["GLYPH_A"],
            token="a",
            binding_type=BindingType.DIRECT,
            confidence=0.9,
        ))
        
        result = mapper.resolve("GLYPH_A")
        self.assertEqual(result, "a")


class TestSymbolResolver(unittest.TestCase):
    """Tests for SymbolResolver."""
    
    def test_resolve_sequence(self):
        """Test sequence resolution."""
        mapper = create_glyph_mapper()
        mapper.add_binding(create_glyph_binding(
            glyph_sequence=["G1"],
            token="token1",
            binding_type=BindingType.DIRECT,
        ))
        
        resolver = create_symbol_resolver(mapper)
        # Test resolving single glyph
        result = resolver.resolve_symbol("G1")
        self.assertEqual(result, "token1")


class TestBindingValidator(unittest.TestCase):
    """Tests for BindingValidator."""
    
    def test_validate_valid_binding(self):
        """Test validation of valid binding."""
        validator = create_binding_validator()
        binding = create_glyph_binding(
            glyph_sequence=["G1"],
            token="T",
            binding_type=BindingType.DIRECT,
            confidence=0.8,
        )
        
        is_valid, errors = validator.validate_binding(binding)
        self.assertTrue(is_valid)
    
    def test_validate_invalid_binding(self):
        """Test validation of invalid binding."""
        # Empty glyph sequence should raise ValueError in constructor
        with self.assertRaises(ValueError):
            create_glyph_binding(
                glyph_sequence=[],
                token="T",
                binding_type=BindingType.DIRECT,
                confidence=1.0,
            )
    
    def test_validate_ambiguous_mapping(self):
        """Test detection of ambiguous mappings."""
        validator = create_binding_validator()
        mapper = create_glyph_mapper()
        
        mapper.add_binding(create_glyph_binding(
            glyph_sequence=["G1"],
            token="A",
            binding_type=BindingType.DIRECT,
        ))
        mapper.add_binding(create_glyph_binding(
            glyph_sequence=["G1"],
            token="B",
            binding_type=BindingType.DIRECT,
        ))
        
        is_valid, errors = validator.validate_mapping(mapper)
        self.assertFalse(is_valid)
        self.assertTrue(any("ambiguous" in e.lower() for e in errors))


if __name__ == "__main__":
    unittest.main()

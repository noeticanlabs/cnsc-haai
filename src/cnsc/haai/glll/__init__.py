"""
GLLL (Glyphic Low-Level Language) Package

Error-tolerant binary encoding using Hadamard matrices.

Modules:
- hadamard: Hadamard matrix operations and encoding/decoding
- codebook: Glyph codebook management
- packetizer: Data packetization for transmission
- mapping: GLLL to GHLL semantic atom mapping
"""

from cnsc.haai.glll.hadamard import (
    HadamardOrder,
    HadamardMatrix,
    SyndromeResult,
    ErrorDetector,
    HadamardCodec,
    create_hadamard_codec,
    create_error_detector,
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

__all__ = [
    # Hadamard
    "HadamardOrder",
    "HadamardMatrix",
    "SyndromeResult",
    "ErrorDetector",
    "HadamardCodec",
    "create_hadamard_codec",
    "create_error_detector",
    # Codebook
    "GlyphType",
    "SymbolCategory",
    "Glyph",
    "Codebook",
    "CodebookValidator",
    "CodebookBuilder",
    "create_codebook",
    "create_codebook_validator",
    "create_codebook_builder",
    # Packetizer
    "PacketType",
    "PacketStatus",
    "Packet",
    "Packetizer",
    "Depacketizer",
    "SequenceTracker",
    "create_packetizer",
    "create_depacketizer",
    "create_sequence_tracker",
    # Mapping
    "BindingType",
    "BindingStatus",
    "GlyphBinding",
    "GlyphMapper",
    "SymbolResolver",
    "BindingValidator",
    "create_glyph_binding",
    "create_glyph_mapper",
    "create_symbol_resolver",
    "create_binding_validator",
]

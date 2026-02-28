"""
GLLL Codebook Management

Glyph-to-symbol mapping and codebook management.

This module provides:
- Codebook: Glyph-to-symbol mapping
- CodebookBuilder: Codebook construction
- CodebookValidator: Integrity checking

Key Features:
- Load/save codebook JSON
- Glyph encoding/decoding
- Distance calculation
- Integrity verification
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import uuid4
import json
import hashlib


class GlyphType(Enum):
    """Type of glyph."""

    DATA = auto()
    CONTROL = auto()
    SYNC = auto()
    PARITY = auto()


class SymbolCategory(Enum):
    """Symbol category."""

    ATOM = auto()
    OPERATOR = auto()
    DELIMITER = auto()
    LITERAL = auto()
    KEYWORD = auto()


@dataclass
class Glyph:
    """
    Glyph definition.

    A glyph is a Hadamard-encoded symbol.
    """

    glyph_id: str
    symbol: str
    glyph_type: GlyphType
    category: SymbolCategory
    hadamard_code: List[int]  # Hadamard codeword
    vector: List[float]  # Normalized vector representation
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate glyph."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not self.hadamard_code:
            raise ValueError("Hadamard code cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "glyph_id": self.glyph_id,
            "symbol": self.symbol,
            "glyph_type": self.glyph_type.name,
            "category": self.category.name,
            "hadamard_code": self.hadamard_code,
            "vector": self.vector,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Glyph":
        """Create from dictionary."""
        return cls(
            glyph_id=data["glyph_id"],
            symbol=data["symbol"],
            glyph_type=GlyphType[data["glyph_type"]],
            category=SymbolCategory[data["category"]],
            hadamard_code=data["hadamard_code"],
            vector=data["vector"],
            metadata=data.get("metadata", {}),
        )

    def compute_hash(self) -> str:
        """Compute glyph hash."""
        data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class Codebook:
    """
    Codebook for glyph-to-symbol mapping.

    A codebook contains all glyph definitions and provides
    encoding/decoding functionality.
    """

    codebook_id: str
    name: str
    version: str
    glyphs: Dict[str, Glyph]  # symbol -> Glyph
    symbols_to_id: Dict[str, str]  # symbol -> glyph_id
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Build lookup indexes."""
        if not self.symbols_to_id:
            for glyph in self.glyphs.values():
                self.symbols_to_id[glyph.symbol] = glyph.glyph_id

    @classmethod
    def create(
        cls,
        name: str,
        version: str = "1.0",
        codebook_id: Optional[str] = None,
    ) -> "Codebook":
        """Create empty codebook."""
        now = datetime.utcnow()
        return cls(
            codebook_id=codebook_id or str(uuid4())[:8],
            name=name,
            version=version,
            glyphs={},
            symbols_to_id={},
            created_at=now,
            updated_at=now,
        )

    def add_glyph(self, glyph: Glyph) -> bool:
        """
        Add glyph to codebook.

        Args:
            glyph: Glyph to add

        Returns:
            True if added, False if already exists
        """
        if glyph.symbol in self.symbols_to_id:
            return False

        self.glyphs[glyph.glyph_id] = glyph
        self.symbols_to_id[glyph.symbol] = glyph.glyph_id
        self.updated_at = datetime.utcnow()
        return True

    def get_glyph(self, symbol: str) -> Optional[Glyph]:
        """Get glyph by symbol."""
        glyph_id = self.symbols_to_id.get(symbol)
        if glyph_id:
            return self.glyphs.get(glyph_id)
        return None

    def get_glyph_by_id(self, glyph_id: str) -> Optional[Glyph]:
        """Get glyph by ID."""
        return self.glyphs.get(glyph_id)

    def encode(self, symbol: str) -> Optional[List[int]]:
        """
        Encode symbol to Hadamard code.

        Args:
            symbol: Symbol to encode

        Returns:
            Hadamard codeword or None if not found
        """
        glyph = self.get_glyph(symbol)
        if glyph:
            return glyph.hadamard_code
        return None

    def decode(self, codeword: List[int]) -> Optional[str]:
        """
        Decode Hadamard codeword to symbol.

        Uses minimum distance decoding.

        Args:
            codeword: Hadamard codeword

        Returns:
            Symbol or None if no match
        """
        best_match = None
        best_distance = float("inf")

        for glyph in self.glyphs.values():
            distance = self._hamming_distance(codeword, glyph.hadamard_code)
            if distance < best_distance:
                best_distance = distance
                best_match = glyph.symbol

        # Return match if within tolerance
        if best_match and best_distance <= len(codeword) // 4:
            return best_match
        return None

    def _hamming_distance(self, a: List[int], b: List[int]) -> int:
        """Calculate Hamming distance between two codewords."""
        if len(a) != len(b):
            return float("inf")
        return sum(1 for x, y in zip(a, b) if x != y)

    def get_by_category(self, category: SymbolCategory) -> List[Glyph]:
        """Get all glyphs in a category."""
        return [g for g in self.glyphs.values() if g.category == category]

    def get_by_type(self, glyph_type: GlyphType) -> List[Glyph]:
        """Get all glyphs of a type."""
        return [g for g in self.glyphs.values() if g.glyph_type == glyph_type]

    def get_stats(self) -> Dict[str, Any]:
        """Get codebook statistics."""
        by_category = {}
        by_type = {}
        for glyph in self.glyphs.values():
            cat = glyph.category.name
            typ = glyph.glyph_type.name
            by_category[cat] = by_category.get(cat, 0) + 1
            by_type[typ] = by_type.get(typ, 0) + 1

        return {
            "codebook_id": self.codebook_id,
            "name": self.name,
            "version": self.version,
            "total_glyphs": len(self.glyphs),
            "by_category": by_category,
            "by_type": by_type,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "codebook_id": self.codebook_id,
            "name": self.name,
            "version": self.version,
            "glyphs": {k: v.to_dict() for k, v in self.glyphs.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Codebook":
        """Create from dictionary."""
        glyphs = {}
        symbols_to_id = {}
        for glyph_id, glyph_data in data.get("glyphs", {}).items():
            glyph = Glyph.from_dict(glyph_data)
            glyphs[glyph_id] = glyph
            symbols_to_id[glyph.symbol] = glyph_id

        return cls(
            codebook_id=data["codebook_id"],
            name=data["name"],
            version=data["version"],
            glyphs=glyphs,
            symbols_to_id=symbols_to_id,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Codebook":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save(self, filepath: str) -> None:
        """Save codebook to file."""
        with open(filepath, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, filepath: str) -> "Codebook":
        """Load codebook from file."""
        with open(filepath, "r") as f:
            return cls.from_json(f.read())

    def compute_checksum(self) -> str:
        """Compute codebook checksum."""
        data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class CodebookValidator:
    """Codebook integrity validation."""

    def validate(self, codebook: Codebook) -> Tuple[bool, List[str]]:
        """
        Validate codebook integrity.

        Args:
            codebook: Codebook to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check for empty codebook
        if len(codebook.glyphs) == 0:
            errors.append("Codebook is empty")

        # Check for duplicate symbols
        symbols = [g.symbol for g in codebook.glyphs.values()]
        if len(symbols) != len(set(symbols)):
            errors.append("Duplicate symbols found")

        # Check for empty symbols
        for glyph in codebook.glyphs.values():
            if not glyph.symbol.strip():
                errors.append(f"Glyph {glyph.glyph_id} has empty symbol")

        # Check for empty codewords
        for glyph in codebook.glyphs.values():
            if not glyph.hadamard_code:
                errors.append(f"Glyph {glyph.glyph_id} has empty Hadamard code")

        # Check symbol-ID consistency
        for symbol, glyph_id in codebook.symbols_to_id.items():
            if glyph_id not in codebook.glyphs:
                errors.append(f"Symbol '{symbol}' references missing glyph_id '{glyph_id}'")

        return len(errors) == 0, errors

    def validate_integrity(self, codebook: Codebook, expected_checksum: str) -> bool:
        """Validate codebook integrity against expected checksum."""
        return codebook.compute_checksum() == expected_checksum


@dataclass
class CodebookBuilder:
    """Builder for constructing codebooks."""

    codebook: Codebook

    def __init__(self, name: str, version: str = "1.0"):
        """Initialize builder."""
        self.codebook = Codebook.create(name, version)

    def add_glyph(
        self,
        symbol: str,
        glyph_type: GlyphType,
        category: SymbolCategory,
        hadamard_code: List[int],
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "CodebookBuilder":
        """
        Add glyph to codebook.

        Args:
            self: Builder instance
            symbol: Symbol to add
            glyph_type: Type of glyph
            category: Symbol category
            hadamard_code: Hadamard codeword
            vector: Optional vector representation
            metadata: Optional metadata

        Returns:
            self for chaining
        """
        glyph = Glyph(
            glyph_id=str(uuid4())[:8],
            symbol=symbol,
            glyph_type=glyph_type,
            category=category,
            hadamard_code=hadamard_code,
            vector=vector or [float(x) for x in hadamard_code],
            metadata=metadata or {},
        )
        self.codebook.add_glyph(glyph)
        return self

    def add_standard_glyphs(self) -> "CodebookBuilder":
        """Add standard control glyphs."""
        # Sync glyph
        self.add_glyph(
            symbol="SYNC",
            glyph_type=GlyphType.SYNC,
            category=SymbolCategory.CONTROL,
            hadamard_code=[1, 1, 1, 1],
        )

        # Delimiter glyphs
        for delim in ["LPAREN", "RPAREN", "LBRACK", "RBRACK", "LBRACE", "RBRACE"]:
            self.add_glyph(
                symbol=delim,
                glyph_type=GlyphType.DATA,
                category=SymbolCategory.DELIMITER,
                hadamard_code=[1, 1, -1, -1],
            )

        return self

    def build(self) -> Codebook:
        """Build and return codebook."""
        return self.codebook


def create_codebook(name: str, version: str = "1.0") -> Codebook:
    """Create new codebook."""
    return Codebook.create(name, version)


def create_codebook_validator() -> CodebookValidator:
    """Create new codebook validator."""
    return CodebookValidator()


def create_codebook_builder(name: str, version: str = "1.0") -> CodebookBuilder:
    """Create new codebook builder."""
    return CodebookBuilder(name, version)

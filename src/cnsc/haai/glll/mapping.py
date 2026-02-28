"""
GLLL to GHLL Mapping

Map GLLL glyphs to GHLL semantic atoms.

This module provides:
- GlyphMapper: Glyph to token mapping
- SymbolResolver: Symbol resolution
- BindingValidator: Binding verification

Key Features:
- Deterministic mapping
- Error tolerance
- Binding validation
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import uuid4
import json
import hashlib


class BindingType(Enum):
    """Type of glyph-to-token binding."""

    DIRECT = auto()  # 1:1 mapping
    SEQUENCE = auto()  # Glyph sequence to token
    CONTEXT = auto()  # Context-dependent mapping


class BindingStatus(Enum):
    """Status of binding validation."""

    VALID = auto()
    INVALID = auto()
    AMBIGUOUS = auto()
    UNBOUND = auto()


@dataclass
class GlyphBinding:
    """
    Glyph to token binding.

    Defines how a glyph (or sequence of glyphs) maps to a token.
    """

    binding_id: str
    glyph_sequence: List[str]  # Sequence of glyph symbols
    token: str  # GHLL token
    binding_type: BindingType
    confidence: float  # 0.0 to 1.0
    context_rules: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate binding."""
        if not self.glyph_sequence:
            raise ValueError("Glyph sequence cannot be empty")
        if not self.token:
            raise ValueError("Token cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def matches(self, glyph_sequence: List[str]) -> bool:
        """Check if binding matches glyph sequence."""
        return self.glyph_sequence == glyph_sequence

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "binding_id": self.binding_id,
            "glyph_sequence": self.glyph_sequence,
            "token": self.token,
            "binding_type": self.binding_type.name,
            "confidence": self.confidence,
            "context_rules": self.context_rules,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GlyphBinding":
        """Create from dictionary."""
        return cls(
            binding_id=data["binding_id"],
            glyph_sequence=data["glyph_sequence"],
            token=data["token"],
            binding_type=BindingType[data["binding_type"]],
            confidence=data["confidence"],
            context_rules=data.get("context_rules", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class GlyphMapper:
    """
    Glyph to token mapper.

    Maps glyph sequences to GHLL tokens.
    """

    bindings: List[GlyphBinding]
    default_binding: Optional[GlyphBinding]

    def __init__(self, bindings: Optional[List[GlyphBinding]] = None):
        """Initialize mapper."""
        self.bindings = bindings or []
        self.default_binding = None
        # Build lookup index
        self._build_index()

    def _build_index(self) -> None:
        """Build lookup index for bindings."""
        self._sequence_to_binding: Dict[Tuple[str, ...], GlyphBinding] = {}
        for binding in self.bindings:
            key = tuple(binding.glyph_sequence)
            self._sequence_to_binding[key] = binding

    def add_binding(self, binding: GlyphBinding) -> None:
        """Add binding to mapper."""
        self.bindings.append(binding)
        key = tuple(binding.glyph_sequence)
        self._sequence_to_binding[key] = binding

    def map(self, glyph_sequence: List[str]) -> Tuple[Optional[str], float]:
        """
        Map glyph sequence to token.

        Args:
            glyph_sequence: Sequence of glyph symbols

        Returns:
            Tuple of (token, confidence)
        """
        key = tuple(glyph_sequence)

        # Direct lookup
        if key in self._sequence_to_binding:
            binding = self._sequence_to_binding[key]
            return binding.token, binding.confidence

        # Try subsequence matching
        for binding in self.bindings:
            if len(binding.glyph_sequence) < len(glyph_sequence):
                if all(g in glyph_sequence for g in binding.glyph_sequence):
                    return binding.token, binding.confidence * 0.9

        # Return default or None
        if self.default_binding:
            return self.default_binding.token, self.default_binding.confidence * 0.5

        return None, 0.0

    def resolve(self, glyph: str) -> Optional[str]:
        """
        Resolve single glyph to token.

        Args:
            glyph: Single glyph symbol

        Returns:
            Token or None
        """
        result, confidence = self.map([glyph])
        if confidence > 0.5:
            return result
        return None

    def get_bindings_for_token(self, token: str) -> List[GlyphBinding]:
        """Get all bindings for a token."""
        return [b for b in self.bindings if b.token == token]

    def get_bindings_for_glyph(self, glyph: str) -> List[GlyphBinding]:
        """Get all bindings containing a glyph."""
        return [b for b in self.bindings if glyph in b.glyph_sequence]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bindings": [b.to_dict() for b in self.bindings],
            "default_binding": self.default_binding.to_dict() if self.default_binding else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GlyphMapper":
        """Create from dictionary."""
        bindings = [GlyphBinding.from_dict(b) for b in data.get("bindings", [])]
        mapper = cls(bindings)
        if data.get("default_binding"):
            mapper.default_binding = GlyphBinding.from_dict(data["default_binding"])
        return mapper


@dataclass
class SymbolResolver:
    """
    Symbol resolution for GLLL to GHLL mapping.

    Resolves symbols with context awareness.
    """

    mapper: GlyphMapper
    context: Dict[str, Any]

    def __init__(self, mapper: Optional[GlyphMapper] = None):
        """Initialize resolver."""
        self.mapper = mapper or GlyphMapper()
        self.context = {}

    def set_context(self, context: Dict[str, Any]) -> None:
        """Set resolution context."""
        self.context = context

    def resolve_sequence(self, glyph_sequence: List[str]) -> Tuple[List[str], bool]:
        """
        Resolve glyph sequence to token sequence.

        Args:
            glyph_sequence: Input glyph sequence

        Returns:
            Tuple of (token sequence, all_resolved)
        """
        tokens = []
        all_resolved = True

        i = 0
        while i < len(glyph_sequence):
            # Try matching longer sequences first
            matched = False
            for length in range(min(4, len(glyph_sequence) - i), 0, -1):
                subsequence = glyph_sequence[i : i + length]
                token, confidence = self.mapper.map(subsequence)
                if token and confidence > 0.5:
                    tokens.append(token)
                    matched = True
                    i += length
                    break

            if not matched:
                # Fallback: try single glyph
                token, confidence = self.mapper.map([glyph_sequence[i]])
                if token:
                    tokens.append(token)
                else:
                    tokens.append(glyph_sequence[i])  # Keep original
                    all_resolved = False
                i += 1

        return tokens, all_resolved

    def resolve_symbol(self, glyph: str) -> Optional[str]:
        """Resolve single symbol."""
        return self.mapper.resolve(glyph)


@dataclass
class BindingValidator:
    """Binding validation for GLLL to GHLL mapping."""

    def validate_binding(self, binding: GlyphBinding) -> Tuple[bool, List[str]]:
        """
        Validate a binding.

        Args:
            binding: Binding to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check for empty glyph sequence
        if not binding.glyph_sequence:
            errors.append("Glyph sequence cannot be empty")

        # Check for empty token
        if not binding.token:
            errors.append("Token cannot be empty")

        # Check confidence range
        if not 0.0 <= binding.confidence <= 1.0:
            errors.append("Confidence must be between 0.0 and 1.0")

        # Check for duplicate glyphs in sequence
        if len(binding.glyph_sequence) != len(set(binding.glyph_sequence)):
            if binding.binding_type == BindingType.DIRECT:
                errors.append("Direct binding cannot have duplicate glyphs")

        return len(errors) == 0, errors

    def validate_mapping(
        self,
        mapper: GlyphMapper,
    ) -> Tuple[bool, List[str]]:
        """
        Validate all bindings in mapper.

        Args:
            mapper: Mapper to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        for i, binding in enumerate(mapper.bindings):
            is_valid, binding_errors = self.validate_binding(binding)
            if not is_valid:
                for error in binding_errors:
                    errors.append(f"Binding {i}: {error}")

        # Check for ambiguous mappings (same glyph sequence to different tokens)
        seen = {}
        for binding in mapper.bindings:
            key = tuple(binding.glyph_sequence)
            if key in seen:
                if seen[key] != binding.token:
                    errors.append(
                        f"Ambiguous mapping: glyph sequence {binding.glyph_sequence} "
                        f"maps to both '{seen[key]}' and '{binding.token}'"
                    )
            else:
                seen[key] = binding.token

        return len(errors) == 0, errors

    def check_completeness(
        self,
        mapper: GlyphMapper,
        required_glyphs: List[str],
    ) -> Tuple[bool, List[str]]:
        """
        Check if mapper covers required glyphs.

        Args:
            mapper: Mapper to check
            required_glyphs: List of required glyphs

        Returns:
            Tuple of (is_complete, missing_glyphs)
        """
        covered_glyphs = set()
        for binding in mapper.bindings:
            for glyph in binding.glyph_sequence:
                covered_glyphs.add(glyph)

        missing = [g for g in required_glyphs if g not in covered_glyphs]
        return len(missing) == 0, missing


def create_glyph_binding(
    glyph_sequence: List[str],
    token: str,
    binding_type: BindingType,
    confidence: float = 1.0,
) -> GlyphBinding:
    """Create new glyph binding."""
    return GlyphBinding(
        binding_id=str(uuid4())[:8],
        glyph_sequence=glyph_sequence,
        token=token,
        binding_type=binding_type,
        confidence=confidence,
    )


def create_glyph_mapper(bindings: Optional[List[GlyphBinding]] = None) -> GlyphMapper:
    """Create new glyph mapper."""
    return GlyphMapper(bindings)


def create_symbol_resolver(mapper: Optional[GlyphMapper] = None) -> SymbolResolver:
    """Create new symbol resolver."""
    return SymbolResolver(mapper)


def create_binding_validator() -> BindingValidator:
    """Create new binding validator."""
    return BindingValidator()

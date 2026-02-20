"""
GHLL Lexicon Module

This module provides the lexicon infrastructure for GHLL including:
- LexiconEntry: Single lexicon entry with parse form, semantics, and receipt signature
- LexiconManager: CRUD operations, lookup, and validation for lexicon entries
- SemanticAtom: Stable identifier for semantic concepts

References:
- cnsc-haai/spec/ghll/01_Lexicon_and_Semantic_Atoms.md
- cnsc-haai/schemas/lexicon.schema.json
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4
import hashlib
import json
import sys


class ParseFormType(Enum):
    """Types of parse forms supported in GHLL."""
    SYMBOL = auto()      # Simple symbol
    PATTERN = auto()     # Regular expression pattern
    TEMPLATE = auto()    # Format string template
    GRAMMAR = auto()     # Grammar production rule


@dataclass
class ParseForm:
    """
    A parse form defines how a lexical entry is recognized.
    
    Attributes:
        form_type: The type of parse form
        pattern: The actual pattern string
        precedence: Operator precedence (for expressions)
        associativity: Left, right, or none
    """
    form_type: ParseFormType
    pattern: str
    precedence: int = 0
    associativity: str = "none"  # "left", "right", "none"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "form_type": self.form_type.name,
            "pattern": self.pattern,
            "precedence": self.precedence,
            "associativity": self.associativity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParseForm':
        """Create from dictionary."""
        return cls(
            form_type=ParseFormType[data.get("form_type", "SYMBOL")],
            pattern=data.get("pattern", ""),
            precedence=data.get("precedence", 0),
            associativity=data.get("associativity", "none")
        )


@dataclass
class ReceiptSignature:
    """
    Receipt signature for provenance tracking.
    
    Attributes:
        algorithm: Hash algorithm used
        digest: Hash digest of the entry
        timestamp: When the signature was created
    """
    algorithm: str = "SHA256"
    digest: str = ""
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "algorithm": self.algorithm,
            "digest": self.digest,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReceiptSignature':
        """Create from dictionary."""
        return cls(
            algorithm=data.get("algorithm", "SHA256"),
            digest=data.get("digest", ""),
            timestamp=data.get("timestamp", "")
        )
    
    def compute_digest(self, entry_data: Dict[str, Any]) -> str:
        """Compute the signature digest from entry data."""
        data_str = json.dumps(entry_data, sort_keys=True)
        self.digest = hashlib.sha256(data_str.encode()).hexdigest()
        return self.digest


@dataclass
class LexiconEntry:
    """
    A single lexicon entry.
    
    Lexicon entries define parse forms, semantics, and receipt signatures.
    They map tokens in source code to semantic atoms.
    
    Attributes:
        semantic_atom: Stable identifier for this entry
        parse_forms: List of parse forms for recognition
        semantics: Semantic description and metadata
        receipt_signature: Provenance and integrity information
        category: Lexical category (keyword, operator, identifier, etc.)
        is_reserved: Whether this is a reserved word
        metadata: Additional metadata for extensibility
    """
    semantic_atom: str
    parse_forms: List[ParseForm]
    semantics: Dict[str, Any]
    receipt_signature: ReceiptSignature = field(default_factory=ReceiptSignature)
    category: str = "identifier"
    is_reserved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize receipt signature if not set."""
        if not self.receipt_signature.digest:
            self._update_receipt_signature()
    
    def _update_receipt_signature(self) -> None:
        """Update the receipt signature."""
        entry_data = self.to_dict()
        # Remove signature fields for self-hashing
        entry_data.pop("receipt_signature", None)
        self.receipt_signature.compute_digest(entry_data)
        from datetime import datetime
        self.receipt_signature.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "semantic_atom": self.semantic_atom,
            "parse_forms": [pf.to_dict() for pf in self.parse_forms],
            "semantics": self.semantics,
            "receipt_signature": self.receipt_signature.to_dict(),
            "category": self.category,
            "is_reserved": self.is_reserved,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LexiconEntry':
        """Create from dictionary representation."""
        return cls(
            semantic_atom=data.get("semantic_atom", ""),
            parse_forms=[ParseForm.from_dict(pf) for pf in data.get("parse_forms", [])],
            semantics=data.get("semantics", {}),
            receipt_signature=ReceiptSignature.from_dict(data.get("receipt_signature", {})),
            category=data.get("category", "identifier"),
            is_reserved=data.get("is_reserved", False),
            metadata=data.get("metadata", {})
        )
    
    def matches(self, token: str) -> bool:
        """
        Check if this entry matches a token.
        
        Args:
            token: The token to match
            
        Returns:
            True if the token matches any parse form
        """
        for parse_form in self.parse_forms:
            if parse_form.form_type == ParseFormType.SYMBOL:
                if parse_form.pattern == token:
                    return True
            elif parse_form.form_type == ParseFormType.PATTERN:
                import re
                if re.match(parse_form.pattern, token):
                    return True
        return False


@dataclass
class LexiconManager:
    """
    Manages the lexicon for GHLL.
    
    The lexicon manager provides:
    - CRUD operations for lexicon entries
    - Lookup by semantic atom or token
    - Validation and integrity checking
    - Load/save from JSON
    
    Attributes:
        entries: Dictionary of entries by semantic atom
        by_category: Dictionary mapping categories to semantic atoms
        by_token: Dictionary mapping tokens to semantic atoms (for fast lookup)
    """
    entries: Dict[str, LexiconEntry] = field(default_factory=dict)
    by_category: Dict[str, Set[str]] = field(default_factory=dict)
    by_token: Dict[str, str] = field(default_factory=dict)  # token -> semantic_atom
    
    def add_entry(self, entry: LexiconEntry) -> bool:
        """
        Add a lexicon entry.
        
        Args:
            entry: The entry to add
            
        Returns:
            True if added successfully, False if already exists
        """
        if entry.semantic_atom in self.entries:
            return False
        
        self.entries[entry.semantic_atom] = entry
        
        # Index by category
        if entry.category not in self.by_category:
            self.by_category[entry.category] = set()
        self.by_category[entry.category].add(entry.semantic_atom)
        
        # Index tokens for fast lookup
        for parse_form in entry.parse_forms:
            if parse_form.form_type == ParseFormType.SYMBOL:
                self.by_token[parse_form.pattern] = entry.semantic_atom
        
        return True
    
    def get_entry(self, semantic_atom: str) -> Optional[LexiconEntry]:
        """
        Get an entry by semantic atom.
        
        Args:
            semantic_atom: The semantic atom to look up
            
        Returns:
            The entry if found, None otherwise
        """
        return self.entries.get(semantic_atom)
    
    def lookup_token(self, token: str) -> Optional[LexiconEntry]:
        """
        Look up an entry by token.
        
        Args:
            token: The token to look up
            
        Returns:
            The entry if found, None otherwise
        """
        semantic_atom = self.by_token.get(token)
        if semantic_atom:
            return self.entries.get(semantic_atom)
        
        # Fall back to sequential search for patterns
        for entry in self.entries.values():
            if entry.matches(token):
                return entry
        
        return None
    
    def get_by_category(self, category: str) -> List[LexiconEntry]:
        """
        Get all entries in a category.
        
        Args:
            category: The category to filter by
            
        Returns:
            List of entries in the category
        """
        semantic_atoms = self.by_category.get(category, set())
        return [self.entries[sa] for sa in semantic_atoms if sa in self.entries]
    
    def get_reserved_words(self) -> List[LexiconEntry]:
        """
        Get all reserved words.
        
        Returns:
            List of reserved word entries
        """
        return [e for e in self.entries.values() if e.is_reserved]
    
    def validate_integrity(self) -> bool:
        """
        Validate the integrity of all entries.
        
        Returns:
            True if all entries are valid, False otherwise
        """
        for entry in self.entries.values():
            # Verify receipt signature
            entry_data = entry.to_dict()
            entry_data.pop("receipt_signature", None)
            expected_digest = hashlib.sha256(
                json.dumps(entry_data, sort_keys=True).encode()
            ).hexdigest()
            
            if entry.receipt_signature.digest != expected_digest:
                return False
        
        return True
    
    def repair_integrity(self) -> int:
        """
        Repair integrity of entries with invalid signatures.
        
        Returns:
            Number of entries repaired
        """
        repaired = 0
        for entry in self.entries.values():
            entry_data = entry.to_dict()
            entry_data.pop("receipt_signature", None)
            expected_digest = hashlib.sha256(
                json.dumps(entry_data, sort_keys=True).encode()
            ).hexdigest()
            
            if entry.receipt_signature.digest != expected_digest:
                entry._update_receipt_signature()
                repaired += 1
        
        return repaired
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "version": "1.0.0",
            "entries": {sa: entry.to_dict() for sa, entry in self.entries.items()}
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LexiconManager':
        """Create from dictionary representation."""
        manager = cls()
        for sa, entry_data in data.get("entries", {}).items():
            entry = LexiconEntry.from_dict(entry_data)
            manager.add_entry(entry)
        return manager
    
    @classmethod
    def from_json(cls, json_str: str) -> 'LexiconManager':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def load_from_file(self, filepath: str) -> bool:
        """
        Load lexicon from JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            loaded_manager = LexiconManager.from_dict(data)
            self.entries = loaded_manager.entries
            self.by_category = loaded_manager.by_category
            self.by_token = loaded_manager.by_token
            return True
        except FileNotFoundError:
            print(f"Lexicon file not found: {filepath}", file=sys.stderr)
            return False
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in lexicon file: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error loading lexicon: {e}", file=sys.stderr)
            return False
    
    def save_to_file(self, filepath: str) -> bool:
        """
        Save lexicon to JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                f.write(self.to_json())
            return True
        except Exception:
            return False
    
    def save(self, filepath: str) -> bool:
        """
        Save lexicon to JSON file (convenience method).
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            True if saved successfully, False otherwise
        """
        return self.save_to_file(filepath)
    
    @classmethod
    def load(cls, filepath: str) -> 'LexiconManager':
        """
        Load lexicon from JSON file (class method).
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            LexiconManager instance
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def get_all_entries(self) -> List[LexiconEntry]:
        """
        Get all lexicon entries.
        
        Returns:
            List of all lexicon entries
        """
        return list(self.entries.values())
    
    def create_default_lexicon(self, name: str = "Default Lexicon") -> None:
        """
        Create the default GHLL lexicon with common entries.
        
        Args:
            name: Optional name for the lexicon (stored in metadata)
        """
        # Keywords
        keywords = [
            ("kw_if", "if", "keyword"),
            ("kw_then", "then", "keyword"),
            ("kw_else", "else", "keyword"),
            ("kw_endif", "endif", "keyword"),
            ("kw_while", "while", "keyword"),
            ("kw_do", "do", "keyword"),
            ("kw_endwhile", "endwhile", "keyword"),
            ("kw_for", "for", "keyword"),
            ("kw_endfor", "endfor", "keyword"),
            ("kw_return", "return", "keyword"),
            ("kw_assert", "assert", "keyword"),
            ("kw_let", "let", "keyword"),
            ("kw_in", "in", "keyword"),
            ("kw_where", "where", "keyword"),
            ("kw_true", "true", "keyword"),
            ("kw_false", "false", "keyword"),
            ("kw_none", "none", "keyword"),
        ]
        
        for semantic_atom, token, category in keywords:
            entry = LexiconEntry(
                semantic_atom=semantic_atom,
                parse_forms=[ParseForm(ParseFormType.SYMBOL, token)],
                semantics={"description": f"Keyword: {token}"},
                category=category,
                is_reserved=True
            )
            self.add_entry(entry)
        
        # Operators
        operators = [
            ("op_assign", "=", "operator"),
            ("op_assign_dcolon", ":=", "operator"),
            ("op_eq", "==", "operator"),
            ("op_neq", "!=", "operator"),
            ("op_lt", "<", "operator"),
            ("op_gt", ">", "operator"),
            ("op_lte", "<=", "operator"),
            ("op_gte", ">=", "operator"),
            ("op_and", "and", "operator"),
            ("op_or", "or", "operator"),
            ("op_not", "not", "operator"),
            ("op_plus", "+", "operator"),
            ("op_minus", "-", "operator"),
            ("op_mul", "*", "operator"),
            ("op_div", "/", "operator"),
            ("op_concat", "++", "operator"),
        ]
        
        for semantic_atom, token, category in operators:
            entry = LexiconEntry(
                semantic_atom=semantic_atom,
                parse_forms=[ParseForm(ParseFormType.SYMBOL, token)],
                semantics={"description": f"Operator: {token}"},
                category=category,
                is_reserved=True
            )
            self.add_entry(entry)
        
        # Delimiters
        delimiters = [
            ("delim_lparen", "(", "delimiter"),
            ("delim_rparen", ")", "delimiter"),
            ("delim_lbracket", "[", "delimiter"),
            ("delim_rbracket", "]", "delimiter"),
            ("delim_lbrace", "{", "delimiter"),
            ("delim_rbrace", "}", "delimiter"),
            ("delim_comma", ",", "delimiter"),
            ("delim_semicolon", ";", "delimiter"),
            ("delim_colon", ":", "delimiter"),
            ("delim_dot", ".", "delimiter"),
        ]
        
        for semantic_atom, token, category in delimiters:
            entry = LexiconEntry(
                semantic_atom=semantic_atom,
                parse_forms=[ParseForm(ParseFormType.SYMBOL, token)],
                semantics={"description": f"Delimiter: {token}"},
                category=category,
                is_reserved=True
            )
            self.add_entry(entry)
        
        # Identifier pattern (for fallback matching)
        entry = LexiconEntry(
            semantic_atom="ident",
            parse_forms=[ParseForm(ParseFormType.PATTERN, r"^[a-zA-Z_][a-zA-Z0-9_]*$")],
            semantics={"description": "User-defined identifier"},
            category="identifier",
            is_reserved=False
        )
        self.add_entry(entry)
        
        # Number pattern
        entry = LexiconEntry(
            semantic_atom="number",
            parse_forms=[ParseForm(ParseFormType.PATTERN, r"^-?\d+(\.\d+)?$")],
            semantics={"description": "Numeric literal"},
            category="literal",
            is_reserved=False
        )
        self.add_entry(entry)
        
        # String pattern
        entry = LexiconEntry(
            semantic_atom="string",
            parse_forms=[ParseForm(ParseFormType.PATTERN, r'^"([^"\\]|\\.)*"$')],
            semantics={"description": "String literal"},
            category="literal",
            is_reserved=False
        )
        self.add_entry(entry)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get lexicon statistics."""
        return {
            "total_entries": len(self.entries),
            "categories": {
                cat: len(atoms) for cat, atoms in self.by_category.items()
            },
            "reserved_words": len([e for e in self.entries.values() if e.is_reserved]),
            "indexed_tokens": len(self.by_token),
            "is_valid": self.validate_integrity()
        }

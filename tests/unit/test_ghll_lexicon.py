"""
Unit tests for GHLL Lexicon Module.

Tests cover:
- LexiconEntry creation and serialization
- LexiconManager CRUD operations
- Token lookup and matching
- Receipt signature generation
- Integrity validation and repair
"""

import unittest
import json
import tempfile
import os

from cnsc.haai.ghll.lexicon import (
    LexiconManager,
    LexiconEntry,
    ParseForm,
    ParseFormType,
    ReceiptSignature,
)


class TestParseForm(unittest.TestCase):
    """Tests for ParseForm class."""
    
    def test_symbol_parse_form(self):
        """Test creating a symbol parse form."""
        pf = ParseForm(ParseFormType.SYMBOL, "if")
        
        assert pf.form_type == ParseFormType.SYMBOL
        assert pf.pattern == "if"
        assert pf.precedence == 0
        assert pf.associativity == "none"
    
    def test_pattern_parse_form(self):
        """Test creating a pattern parse form."""
        pf = ParseForm(ParseFormType.PATTERN, r"^[a-zA-Z_]+$")
        
        assert pf.form_type == ParseFormType.PATTERN
        assert pf.pattern == r"^[a-zA-Z_]+$"
    
    def test_parse_form_serialization(self):
        """Test parse form to_dict and from_dict."""
        pf = ParseForm(ParseFormType.SYMBOL, "test", precedence=10, associativity="left")
        
        data = pf.to_dict()
        restored = ParseForm.from_dict(data)
        
        assert restored.form_type == pf.form_type
        assert restored.pattern == pf.pattern
        assert restored.precedence == pf.precedence
        assert restored.associativity == pf.associativity


class TestReceiptSignature(unittest.TestCase):
    """Tests for ReceiptSignature class."""
    
    def test_receipt_signature_creation(self):
        """Test creating a receipt signature."""
        sig = ReceiptSignature(algorithm="SHA256", digest="abc123")
        
        assert sig.algorithm == "SHA256"
        assert sig.digest == "abc123"
        assert sig.timestamp == ""
    
    def test_compute_digest(self):
        """Test computing a digest."""
        sig = ReceiptSignature()
        entry_data = {"semantic_atom": "test", "value": "data"}
        
        digest = sig.compute_digest(entry_data)
        
        assert digest
        assert len(digest) == 64  # SHA256 hex length
        assert sig.digest == digest
    
    def test_receipt_signature_serialization(self):
        """Test receipt signature to_dict and from_dict."""
        sig = ReceiptSignature(algorithm="SHA256", digest="abc123", timestamp="2024-01-01T00:00:00")
        
        data = sig.to_dict()
        restored = ReceiptSignature.from_dict(data)
        
        assert restored.algorithm == sig.algorithm
        assert restored.digest == sig.digest
        assert restored.timestamp == sig.timestamp


class TestLexiconEntry(unittest.TestCase):
    """Tests for LexiconEntry class."""
    
    def test_entry_creation(self):
        """Test creating a lexicon entry."""
        entry = LexiconEntry(
            semantic_atom="kw_if",
            parse_forms=[ParseForm(ParseFormType.SYMBOL, "if")],
            semantics={"description": "If keyword"},
            category="keyword",
            is_reserved=True
        )
        
        assert entry.semantic_atom == "kw_if"
        assert len(entry.parse_forms) == 1
        assert entry.category == "keyword"
        assert entry.is_reserved is True
        assert entry.receipt_signature.digest  # Auto-computed
    
    def test_entry_matches_symbol(self):
        """Test matching a token against a symbol entry."""
        entry = LexiconEntry(
            semantic_atom="op_plus",
            parse_forms=[ParseForm(ParseFormType.SYMBOL, "+")],
            semantics={},
            category="operator"
        )
        
        assert entry.matches("+") is True
        assert entry.matches("-") is False
    
    def test_entry_matches_pattern(self):
        """Test matching a token against a pattern entry."""
        entry = LexiconEntry(
            semantic_atom="ident",
            parse_forms=[ParseForm(ParseFormType.PATTERN, r"^[a-zA-Z_][a-zA-Z0-9_]*$")],
            semantics={},
            category="identifier"
        )
        
        assert entry.matches("foo") is True
        assert entry.matches("foo123") is True
        assert entry.matches("123foo") is False
        assert entry.matches("_test") is True
    
    def test_entry_serialization(self):
        """Test entry to_dict and from_dict."""
        entry = LexiconEntry(
            semantic_atom="test",
            parse_forms=[ParseForm(ParseFormType.SYMBOL, "test")],
            semantics={"key": "value"},
            category="test",
            is_reserved=False,
            metadata={"meta": True}
        )
        
        data = entry.to_dict()
        restored = LexiconEntry.from_dict(data)
        
        assert restored.semantic_atom == entry.semantic_atom
        assert len(restored.parse_forms) == len(entry.parse_forms)
        assert restored.category == entry.category
        assert restored.is_reserved == entry.is_reserved
        assert restored.semantics == entry.semantics


class TestLexiconManager(unittest.TestCase):
    """Tests for LexiconManager class."""
    
    def test_create_default_lexicon(self):
        """Test creating a default lexicon."""
        manager = LexiconManager()
        manager.create_default_lexicon()
        
        assert len(manager.entries) > 0
        
        # Check keywords are added
        if_entry = manager.get_entry("kw_if")
        assert if_entry is not None
        assert if_entry.is_reserved is True
        
        # Check operators are added
        plus_entry = manager.get_entry("op_plus")
        assert plus_entry is not None
        
        # Check delimiters are added
        lparen = manager.get_entry("delim_lparen")
        assert lparen is not None
    
    def test_add_entry(self):
        """Test adding entries to the lexicon."""
        manager = LexiconManager()
        
        entry = LexiconEntry(
            semantic_atom="custom",
            parse_forms=[ParseForm(ParseFormType.SYMBOL, "custom")],
            semantics={},
            category="custom"
        )
        
        assert manager.add_entry(entry) is True
        assert manager.add_entry(entry) is False  # Duplicate
    
    def test_get_entry(self):
        """Test getting entries by semantic atom."""
        manager = LexiconManager()
        manager.create_default_lexicon()
        
        entry = manager.get_entry("kw_if")
        assert entry is not None
        assert entry.semantic_atom == "kw_if"
        
        # Non-existent entry
        assert manager.get_entry("nonexistent") is None
    
    def test_lookup_token(self):
        """Test looking up entries by token."""
        manager = LexiconManager()
        manager.create_default_lexicon()
        
        entry = manager.lookup_token("if")
        assert entry is not None
        assert entry.semantic_atom == "kw_if"
        
        entry = manager.lookup_token("+")
        assert entry is not None
        assert entry.semantic_atom == "op_plus"
        
        # Non-existent token
        assert manager.lookup_token("???") is None
    
    def test_get_by_category(self):
        """Test getting entries by category."""
        manager = LexiconManager()
        manager.create_default_lexicon()
        
        keywords = manager.get_by_category("keyword")
        assert len(keywords) > 0
        assert all(e.category == "keyword" for e in keywords)
        
        operators = manager.get_by_category("operator")
        assert len(operators) > 0
        assert all(e.category == "operator" for e in operators)
    
    def test_get_reserved_words(self):
        """Test getting all reserved words."""
        manager = LexiconManager()
        manager.create_default_lexicon()
        
        reserved = manager.get_reserved_words()
        assert len(reserved) > 0
        assert all(e.is_reserved for e in reserved)
    
    def test_validate_integrity(self):
        """Test validating lexicon integrity."""
        manager = LexiconManager()
        manager.create_default_lexicon()
        
        assert manager.validate_integrity() is True
    
    def test_validate_integrity_after_modification(self):
        """Test integrity check after manual modification."""
        manager = LexiconManager()
        manager.create_default_lexicon()
        
        # Manually corrupt an entry
        entry = manager.get_entry("kw_if")
        entry.semantics["corrupted"] = True
        
        assert manager.validate_integrity() is False
    
    def test_repair_integrity(self):
        """Test repairing lexicon integrity."""
        manager = LexiconManager()
        manager.create_default_lexicon()
        
        # Corrupt an entry
        entry = manager.get_entry("kw_if")
        entry.semantics["corrupted"] = True
        
        # Repair
        repaired = manager.repair_integrity()
        assert repaired >= 1
        assert manager.validate_integrity() is True
    
    def test_save_and_load(self):
        """Test saving and loading lexicon to/from file."""
        manager = LexiconManager()
        manager.create_default_lexicon()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            # Save
            assert manager.save_to_file(filepath) is True
            
            # Load into new manager
            new_manager = LexiconManager()
            assert new_manager.load_from_file(filepath) is True
            
            # Compare
            assert len(new_manager.entries) == len(manager.entries)
            assert new_manager.get_entry("kw_if") is not None
        finally:
            os.unlink(filepath)
    
    def test_get_stats(self):
        """Test getting lexicon statistics."""
        manager = LexiconManager()
        manager.create_default_lexicon()
        
        stats = manager.get_stats()
        
        assert stats["total_entries"] > 0
        assert "keyword" in stats["categories"]
        assert stats["reserved_words"] > 0
        assert stats["is_valid"] is True
    
    def test_serialization_roundtrip(self):
        """Test JSON serialization roundtrip."""
        manager = LexiconManager()
        manager.create_default_lexicon()
        
        # To JSON
        json_str = manager.to_json()
        assert json_str
        
        # From JSON
        restored = LexiconManager.from_json(json_str)
        
        assert len(restored.entries) == len(manager.entries)
        assert restored.get_entry("kw_if") is not None


class TestLexiconEdgeCases(unittest.TestCase):
    """Edge case tests for lexicon."""
    
    def test_empty_lexicon(self):
        """Test operations on empty lexicon."""
        manager = LexiconManager()
        
        assert manager.get_entry("test") is None
        assert manager.lookup_token("test") is None
        assert manager.validate_integrity() is True
        assert manager.get_stats()["total_entries"] == 0
    
    def test_duplicate_tokens_different_entries(self):
        """Test that duplicate tokens from different entries work correctly."""
        manager = LexiconManager()
        
        # Add two entries with different semantic atoms but same token
        entry1 = LexiconEntry(
            semantic_atom="custom1",
            parse_forms=[ParseForm(ParseFormType.SYMBOL, "test")],
            semantics={},
            category="custom"
        )
        entry2 = LexiconEntry(
            semantic_atom="custom2",
            parse_forms=[ParseForm(ParseFormType.SYMBOL, "test")],
            semantics={},
            category="custom"
        )
        
        manager.add_entry(entry1)
        manager.add_entry(entry2)
        
        # Token lookup should find the first one indexed
        result = manager.lookup_token("test")
        assert result is not None
        assert result.semantic_atom in ("custom1", "custom2")
    
    def test_complex_pattern_matching(self):
        """Test pattern matching with complex regex."""
        manager = LexiconManager()
        
        entry = LexiconEntry(
            semantic_atom="email",
            parse_forms=[ParseForm(
                ParseFormType.PATTERN, 
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            )],
            semantics={},
            category="literal"
        )
        manager.add_entry(entry)
        
        assert entry.matches("user@example.com") is True
        assert entry.matches("invalid@") is False
        assert entry.matches("@example.com") is False

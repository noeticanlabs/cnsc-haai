"""
GHLL - Glyphic High-Level Language

This package provides the GHLL compiler infrastructure:
- lexicon: Lexicon and semantic atom management
- types: Type system for GHLL
- parser: EBNF-based parser for GHLL source code

References:
- cnsc-haai/spec/ghll/
"""

from cnsc.haai.ghll.lexicon import (
    LexiconManager,
    LexiconEntry,
    ParseForm,
    ParseFormType,
    ReceiptSignature,
)

from cnsc.haai.ghll.types import (
    GHLLType,
    PrimitiveType,
    BoolType,
    IntType,
    FloatType,
    StringType,
    SymbolType,
    NoneType,
    CompositeType,
    StructType,
    UnionType,
    SequenceType,
    OptionalType,
    FunctionType,
    TypeRegistry,
    TypeVariable,
    TypeChecker,
    TypeCategory,
)

from cnsc.haai.ghll.parser import (
    parse_ghll,
    tokenize_ghll,
    GHLLParser,
    Tokenizer,
    Token,
    TokenType,
    Span,
    ParseError,
    ParseResult,
)

__all__ = [
    # Lexicon
    "LexiconManager",
    "LexiconEntry",
    "ParseForm",
    "ParseFormType",
    "ReceiptSignature",
    # Types
    "GHLLType",
    "PrimitiveType",
    "BoolType",
    "IntType",
    "FloatType",
    "StringType",
    "SymbolType",
    "NoneType",
    "CompositeType",
    "StructType",
    "UnionType",
    "SequenceType",
    "OptionalType",
    "FunctionType",
    "TypeRegistry",
    "TypeVariable",
    "TypeChecker",
    "TypeCategory",
    # Parser
    "parse_ghll",
    "tokenize_ghll",
    "GHLLParser",
    "Tokenizer",
    "Token",
    "TokenType",
    "Span",
    "ParseError",
    "ParseResult",
]

__version__ = "1.0.0"

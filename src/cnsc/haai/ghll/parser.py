"""
GHLL Parser

This module provides the GHLL parser for parsing source code according to the EBNF grammar.
The parser includes:
- Token: Token representation with span information
- Tokenizer: Lexical analysis
- GHLLParser: Recursive descent parser
- ParseError: Structured error reporting
- ParseResult: Result of parsing with AST and provenance

References:
- cnsc-haai/spec/ghll/02_Grammar_EBNF.md
- cnsc-haai/spec/ghll/05_Normal_Forms_and_Canonicalization.md
- cnsc-haai/spec/ghll/06_Provenance_and_Span_Rules.md
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import re


class TokenType(Enum):
    """Token types for GHLL lexer."""
    # Keywords
    KW_IF = auto()
    KW_THEN = auto()
    KW_ELSE = auto()
    KW_ENDIF = auto()
    KW_WHILE = auto()
    KW_DO = auto()
    KW_ENDWHILE = auto()
    KW_FOR = auto()
    KW_ENDFOR = auto()
    KW_RETURN = auto()
    KW_ASSERT = auto()
    KW_LET = auto()
    KW_IN = auto()
    KW_WHERE = auto()
    KW_TRUE = auto()
    KW_FALSE = auto()
    KW_NONE = auto()
    KW_AND = auto()
    KW_OR = auto()
    KW_NOT = auto()
    KW_TO = auto()
    
    # Operators
    OP_ASSIGN = auto()
    OP_EQ = auto()
    OP_NEQ = auto()
    OP_LT = auto()
    OP_GT = auto()
    OP_LTE = auto()
    OP_GTE = auto()
    OP_AND = auto()
    OP_OR = auto()
    OP_NOT = auto()
    OP_PLUS = auto()
    OP_MINUS = auto()
    OP_MUL = auto()
    OP_DIV = auto()
    OP_CONCAT = auto()
    
    # Delimiters
    DELIM_LPAREN = auto()
    DELIM_RPAREN = auto()
    DELIM_LBRACKET = auto()
    DELIM_RBRACKET = auto()
    DELIM_LBRACE = auto()
    DELIM_RBRACE = auto()
    DELIM_COMMA = auto()
    DELIM_SEMICOLON = auto()
    DELIM_COLON = auto()
    DELIM_DOT = auto()
    
    # Literals and identifiers
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    SYMBOL = auto()
    
    # Special
    EOF = auto()
    INVALID = auto()


# Keyword and operator mappings
KEYWORDS = {
    "if": TokenType.KW_IF,
    "then": TokenType.KW_THEN,
    "else": TokenType.KW_ELSE,
    "endif": TokenType.KW_ENDIF,
    "while": TokenType.KW_WHILE,
    "do": TokenType.KW_DO,
    "endwhile": TokenType.KW_ENDWHILE,
    "for": TokenType.KW_FOR,
    "to": TokenType.KW_TO,
    "endfor": TokenType.KW_ENDFOR,
    "return": TokenType.KW_RETURN,
    "assert": TokenType.KW_ASSERT,
    "let": TokenType.KW_LET,
    "in": TokenType.KW_IN,
    "where": TokenType.KW_WHERE,
    "true": TokenType.KW_TRUE,
    "false": TokenType.KW_FALSE,
    "none": TokenType.KW_NONE,
    "and": TokenType.KW_AND,
    "or": TokenType.KW_OR,
    "not": TokenType.KW_NOT,
}

OPERATORS = {
    ":=": TokenType.OP_ASSIGN,
    "==": TokenType.OP_EQ,
    "!=": TokenType.OP_NEQ,
    "<": TokenType.OP_LT,
    ">": TokenType.OP_GT,
    "<=": TokenType.OP_LTE,
    ">=": TokenType.OP_GTE,
    "+": TokenType.OP_PLUS,
    "-": TokenType.OP_MINUS,
    "*": TokenType.OP_MUL,
    "/": TokenType.OP_DIV,
    "++": TokenType.OP_CONCAT,
}

DELIMITERS = {
    "(": TokenType.DELIM_LPAREN,
    ")": TokenType.DELIM_RPAREN,
    "[": TokenType.DELIM_LBRACKET,
    "]": TokenType.DELIM_RBRACKET,
    "{": TokenType.DELIM_LBRACE,
    "}": TokenType.DELIM_RBRACE,
    ",": TokenType.DELIM_COMMA,
    ";": TokenType.DELIM_SEMICOLON,
    ":": TokenType.DELIM_COLON,
    ".": TokenType.DELIM_DOT,
}


@dataclass
class Span:
    """
    Source span representing a range of characters.
    
    Attributes:
        start: Start position (line, column)
        end: End position (line, column)
        source: Source identifier
    """
    start: Tuple[int, int] = (1, 0)
    end: Tuple[int, int] = (1, 0)
    source: str = ""
    
    def __add__(self, other: 'Span') -> 'Span':
        """Combine two spans."""
        return Span(
            start=self.start,
            end=other.end,
            source=self.source or other.source
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start": list(self.start),
            "end": list(self.end),
            "source": self.source
        }


@dataclass
class Token:
    """
    A lexical token with type and span information.
    
    Attributes:
        token_type: The type of token
        value: The token's text value
        span: Source span of the token
    """
    token_type: TokenType
    value: str
    span: Span = field(default_factory=Span)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.token_type.name,
            "value": self.value,
            "span": self.span.to_dict()
        }
    
    def __str__(self) -> str:
        """Return token representation."""
        return f"Token({self.token_type.name}, '{self.value}')"


@dataclass
class ParseError:
    """
    A parsing error with location and message.
    
    Attributes:
        message: Error message
        span: Source span of the error
        expected: What was expected
        found: What was found instead
        can_recover: Whether parsing can continue after this error
    """
    message: str
    span: Span = field(default_factory=Span)
    expected: Optional[str] = None
    found: Optional[str] = None
    can_recover: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "span": self.span.to_dict(),
            "expected": self.expected,
            "found": self.found,
            "can_recover": self.can_recover
        }


@dataclass
class ParseResult:
    """
    Result of parsing.
    
    Attributes:
        success: Whether parsing succeeded
        ast: The abstract syntax tree
        errors: List of parsing errors
        warnings: List of warnings
        tokens: List of all tokens
        provenance: Provenance information
    """
    success: bool
    ast: Optional[Dict[str, Any]] = None
    errors: List[ParseError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    tokens: List[Token] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "ast": self.ast,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": self.warnings,
            "token_count": len(self.tokens),
            "provenance": self.provenance
        }
    
    @property
    def has_errors(self) -> bool:
        """Check if there are errors."""
        return len(self.errors) > 0


class Tokenizer:
    """
    Lexical analyzer for GHLL.
    
    Converts source code into tokens.
    
    Attributes:
        source: Source code to tokenize
        pos: Current position
        line: Current line number
        col: Current column number
        tokens: Generated tokens
    """
    
    def __init__(self, source: str, source_name: str = ""):
        """Initialize the tokenizer."""
        self.source = source
        self.source_name = source_name
        self.pos = 0
        self.line = 1
        self.col = 0
        self.tokens: List[Token] = []
        self._current_span = Span(source=source_name)
    
    def tokenize(self) -> List[Token]:
        """
        Tokenize the source code.
        
        Returns:
            List of tokens
        """
        while not self._at_end():
            self._current_span = Span(
                start=(self.line, self.col),
                end=(self.line, self.col),
                source=self.source_name
            )
            
            char = self._peek()
            
            # Whitespace
            if char.isspace():
                self._advance()
                continue
            
            # Comments
            if char == '#':
                self._skip_comment()
                continue
            
            # String literals
            if char == '"':
                self._tokenize_string()
                continue
            
            # Numbers
            if char.isdigit() or (char == '-' and self._peek_next().isdigit()):
                self._tokenize_number()
                continue
            
            # Identifiers and keywords
            if char.isalpha() or char == '_':
                self._tokenize_identifier()
                continue
            
            # Operators and delimiters (multi-character first)
            if self._try_tokenize_multi_char():
                continue
            
            # Single character tokens
            if char in DELIMITERS:
                self._add_token(DELIMITERS[char], char)
                self._advance()
                continue
            
            # Invalid character
            self._add_token(TokenType.INVALID, char)
            self._advance()
        
        # Add EOF token
        eof_span = Span(
            start=(self.line, self.col),
            end=(self.line, self.col),
            source=self.source_name
        )
        self.tokens.append(Token(TokenType.EOF, "", eof_span))
        
        return self.tokens
    
    def _at_end(self) -> bool:
        """Check if at end of source."""
        return self.pos >= len(self.source)
    
    def _peek(self) -> str:
        """Peek at current character."""
        return self.source[self.pos] if self.pos < len(self.source) else ''
    
    def _peek_next(self) -> str:
        """Peek at next character."""
        return self.source[self.pos + 1] if self.pos + 1 < len(self.source) else ''
    
    def _advance(self) -> str:
        """Advance to next character."""
        char = self.source[self.pos]
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.col = 0
        else:
            self.col += 1
        return char
    
    def _skip_comment(self) -> None:
        """Skip a comment."""
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self._advance()
    
    def _tokenize_string(self) -> None:
        """Tokenize a string literal."""
        start_span = Span(
            start=(self.line, self.col),
            end=(self.line, self.col),
            source=self.source_name
        )
        self._advance()  # Skip opening quote
        
        value = ""
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            char = self.source[self.pos]
            if char == '\\' and self.pos + 1 < len(self.source):
                # Escape sequence
                next_char = self.source[self.pos + 1]
                escape_map = {'n': '\n', 't': '\t', '"': '"', '\\': '\\'}
                value += escape_map.get(next_char, next_char)
                self._advance(2)
            else:
                value += char
                self._advance()
        
        self._advance()  # Skip closing quote
        
        end_span = Span(
            start=(self.line, self.col),
            end=(self.line, self.col),
            source=self.source_name
        )
        span = start_span + end_span
        self.tokens.append(Token(TokenType.STRING, value, span))
    
    def _tokenize_number(self) -> None:
        """Tokenize a number literal."""
        start_span = Span(
            start=(self.line, self.col),
            end=(self.line, self.col),
            source=self.source_name
        )
        
        value = ""
        if self._peek() == '-':
            value += self._advance()
        
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            value += self._advance()
        
        if self.pos < len(self.source) and self.source[self.pos] == '.':
            value += self._advance()
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                value += self._advance()
        
        end_span = Span(
            start=(self.line, self.col),
            end=(self.line, self.col),
            source=self.source_name
        )
        span = start_span + end_span
        self.tokens.append(Token(TokenType.NUMBER, value, span))
    
    def _tokenize_identifier(self) -> None:
        """Tokenize an identifier or keyword."""
        start_span = Span(
            start=(self.line, self.col),
            end=(self.line, self.col),
            source=self.source_name
        )
        
        value = ""
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            value += self._advance()
        
        # Check if it's a keyword
        token_type = KEYWORDS.get(value, TokenType.IDENTIFIER)
        
        end_span = Span(
            start=(self.line, self.col),
            end=(self.line, self.col),
            source=self.source_name
        )
        span = start_span + end_span
        self.tokens.append(Token(token_type, value, span))
    
    def _try_tokenize_multi_char(self) -> bool:
        """Try to tokenize multi-character operators."""
        remaining = self.source[self.pos:]
        
        for op in sorted(OPERATORS.keys(), key=len, reverse=True):
            if remaining.startswith(op):
                span = Span(
                    start=(self.line, self.col),
                    end=(self.line, self.col + len(op)),
                    source=self.source_name
                )
                self.tokens.append(Token(OPERATORS[op], op, span))
                self._advance(len(op))
                return True
        
        return False
    
    def _add_token(self, token_type: TokenType, value: str) -> None:
        """Add a token."""
        span = Span(
            start=(self.line, self.col),
            end=(self.line, self.col + len(value)),
            source=self.source_name
        )
        self.tokens.append(Token(token_type, value, span))
    
    def _advance(self, count: int = 1) -> str:
        """Advance by count characters."""
        chars = []
        for _ in range(count):
            if self.pos < len(self.source):
                char = self.source[self.pos]
                chars.append(char)
                self.pos += 1
                if char == '\n':
                    self.line += 1
                    self.col = 0
                else:
                    self.col += 1
        return ''.join(chars)


class GHLLParser:
    """
    GHLL Parser - Recursive descent parser for GHLL.
    
    Parses GHLL source code according to the EBNF grammar and produces
    an abstract syntax tree (AST) with provenance information.
    
    Grammar (simplified):
        program ::= statement*
        statement ::= let_stmt | if_stmt | while_stmt | for_stmt 
                     | return_stmt | assert_stmt | expr_stmt
        let_stmt ::= 'let' identifier '=' expr
        if_stmt ::= 'if' expr 'then' statement* ('else' statement*)? 'endif'
        while_stmt ::= 'while' expr 'do' statement* 'endwhile'
        for_stmt ::= 'for' identifier '=' expr 'to' expr 'do' statement* 'endfor'
        return_stmt ::= 'return' expr
        assert_stmt ::= 'assert' expr
        expr ::= logical_expr
        logical_expr ::= comparison_expr ('and' | 'or' comparison_expr)*
        comparison_expr ::= additive_expr ('==' | '!=' | '<' | '>' | '<=' | '>=' additive_expr)?
        additive_expr ::= multiplicative_expr (('+' | '-') multiplicative_expr)*
        multiplicative_expr ::= unary_expr (('*' | '/') unary_expr)*
        unary_expr ::= ('not' | '-') unary_expr | primary
        primary ::= identifier | number | string | '(' expr ')' | bool_literal | none_literal
    
    Attributes:
        tokens: Token stream
        pos: Current position in token stream
        errors: Parsing errors
        current_token: Current token
    """
    
    def __init__(self, tokens: List[Token]):
        """Initialize the parser."""
        self.tokens = tokens
        self.pos = 0
        self.errors: List[ParseError] = []
        self.warnings: List[str] = []
    
    @property
    def current_token(self) -> Optional[Token]:
        """Get current token."""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    @property
    def at_end(self) -> bool:
        """Check if at end of token stream."""
        return self.pos >= len(self.tokens) or self.current_token.token_type == TokenType.EOF
    
    def parse(self) -> ParseResult:
        """
        Parse the token stream.
        
        Returns:
            ParseResult with AST or errors
        """
        statements = []
        token_list = []
        
        while not self.at_end:
            token_list.append(self.current_token)
            if self.current_token.token_type != TokenType.EOF:
                stmt = self._parse_statement()
                if stmt:
                    statements.append(stmt)
        
        ast = {
            "type": "program",
            "body": statements,
            "span": self._get_span_from_tokens(statements) if statements else None
        }
        
        return ParseResult(
            success=len(self.errors) == 0,
            ast=ast,
            errors=self.errors,
            warnings=self.warnings,
            tokens=token_list
        )
    
    def _parse_statement(self) -> Optional[Dict[str, Any]]:
        """Parse a statement."""
        token = self.current_token
        
        if token.token_type in (TokenType.KW_LET,):
            return self._parse_let_stmt()
        elif token.token_type in (TokenType.KW_IF,):
            return self._parse_if_stmt()
        elif token.token_type in (TokenType.KW_WHILE,):
            return self._parse_while_stmt()
        elif token.token_type in (TokenType.KW_FOR,):
            return self._parse_for_stmt()
        elif token.token_type in (TokenType.KW_RETURN,):
            return self._parse_return_stmt()
        elif token.token_type in (TokenType.KW_ASSERT,):
            return self._parse_assert_stmt()
        else:
            # Try to parse as expression statement
            expr = self._parse_expr()
            if expr:
                return expr
            else:
                self._error(f"Unexpected token: {token.value}")
                self._advance()
                return None
    
    def _parse_let_stmt(self) -> Dict[str, Any]:
        """Parse a let statement: 'let' identifier '=' expr"""
        span_start = self._current_span()
        self._advance()  # 'let'
        
        if self.current_token.token_type != TokenType.IDENTIFIER:
            self._error("Expected identifier after 'let'", expected="identifier")
            return None
        
        name_token = self.current_token
        self._advance()
        
        if not self._match(TokenType.OP_ASSIGN):
            self._error("Expected ':=' after identifier", expected=":=")
            return None
        
        value = self._parse_expr()
        if not value:
            return None
        
        span = span_start + self._current_span()
        
        return {
            "type": "let_statement",
            "variable": name_token.value,
            "value": value,
            "span": span.to_dict()
        }
    
    def _parse_if_stmt(self) -> Dict[str, Any]:
        """Parse an if statement: 'if' expr 'then' statement* ('else' statement*)? 'endif'"""
        span_start = self._current_span()
        self._advance()  # 'if'
        
        condition = self._parse_expr()
        if not condition:
            return None
        
        if not self._match(TokenType.KW_THEN):
            self._error("Expected 'then' after condition", expected="then")
            return None
        
        then_branch = []
        while self.current_token and self.current_token.token_type not in (
            TokenType.KW_ELSE, TokenType.KW_ENDIF, TokenType.EOF
        ):
            stmt = self._parse_statement()
            if stmt:
                then_branch.append(stmt)
        
        else_branch = None
        if self._match(TokenType.KW_ELSE):
            else_branch = []
            while self.current_token and self.current_token.token_type not in (
                TokenType.KW_ENDIF, TokenType.EOF
            ):
                stmt = self._parse_statement()
                if stmt:
                    else_branch.append(stmt)
        
        if not self._match(TokenType.KW_ENDIF):
            self._error("Expected 'endif' to close if statement", expected="endif")
            return None
        
        span = span_start + self._current_span()
        
        result = {
            "type": "if_statement",
            "condition": condition,
            "then_branch": then_branch,
            "else_branch": else_branch,
            "span": span.to_dict()
        }
        
        return result
    
    def _parse_while_stmt(self) -> Dict[str, Any]:
        """Parse a while statement: 'while' expr 'do' statement* 'endwhile'"""
        span_start = self._current_span()
        self._advance()  # 'while'
        
        condition = self._parse_expr()
        if not condition:
            return None
        
        if not self._match(TokenType.KW_DO):
            self._error("Expected 'do' after condition", expected="do")
            return None
        
        body = []
        while self.current_token and self.current_token.token_type not in (
            TokenType.KW_ENDWHILE, TokenType.EOF
        ):
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
        
        if not self._match(TokenType.KW_ENDWHILE):
            self._error("Expected 'endwhile' to close while statement", expected="endwhile")
            return None
        
        span = span_start + self._current_span()
        
        return {
            "type": "while_statement",
            "condition": condition,
            "body": body,
            "span": span.to_dict()
        }
    
    def _parse_for_stmt(self) -> Dict[str, Any]:
        """Parse a for statement: 'for' identifier '=' expr 'to' expr 'do' statement* 'endfor'"""
        span_start = self._current_span()
        self._advance()  # 'for'
        
        if self.current_token.token_type != TokenType.IDENTIFIER:
            self._error("Expected identifier after 'for'", expected="identifier")
            return None
        
        var_name = self.current_token.value
        self._advance()
        
        if not self._match(TokenType.OP_ASSIGN):
            self._error("Expected ':=' after identifier", expected=":=")
            return None
        
        start = self._parse_expr()
        if not start:
            return None
        
        if not self._match(TokenType.KW_TO):
            self._error("Expected 'to' after start expression", expected="to")
            return None
        
        end = self._parse_expr()
        if not end:
            return None
        
        if not self._match(TokenType.KW_DO):
            self._error("Expected 'do' after end expression", expected="do")
            return None
        
        body = []
        while self.current_token and self.current_token.token_type not in (
            TokenType.KW_ENDFOR, TokenType.EOF
        ):
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
        
        if not self._match(TokenType.KW_ENDFOR):
            self._error("Expected 'endfor' to close for statement", expected="endfor")
            return None
        
        span = span_start + self._current_span()
        
        return {
            "type": "for_statement",
            "variable": var_name,
            "start": start,
            "end": end,
            "body": body,
            "span": span.to_dict()
        }
    
    def _parse_return_stmt(self) -> Dict[str, Any]:
        """Parse a return statement: 'return' expr"""
        span_start = self._current_span()
        self._advance()  # 'return'
        
        value = self._parse_expr()
        if not value:
            return None
        
        span = span_start + self._current_span()
        
        return {
            "type": "return_statement",
            "value": value,
            "span": span.to_dict()
        }
    
    def _parse_assert_stmt(self) -> Dict[str, Any]:
        """Parse an assert statement: 'assert' expr"""
        span_start = self._current_span()
        self._advance()  # 'assert'
        
        condition = self._parse_expr()
        if not condition:
            return None
        
        span = span_start + self._current_span()
        
        return {
            "type": "assert_statement",
            "condition": condition,
            "span": span.to_dict()
        }
    
    def _parse_expr(self) -> Optional[Dict[str, Any]]:
        """Parse an expression."""
        return self._parse_logical_expr()
    
    def _parse_logical_expr(self) -> Optional[Dict[str, Any]]:
        """Parse logical expression: comparison_expr ('and' | 'or' comparison_expr)*"""
        left = self._parse_comparison_expr()
        if not left:
            return None
        
        while self.current_token and self.current_token.token_type in (
            TokenType.KW_AND, TokenType.KW_OR
        ):
            op_token = self.current_token
            self._advance()
            right = self._parse_comparison_expr()
            if not right:
                return None
            
            left = {
                "type": "binary_expression",
                "operator": op_token.value,
                "left": left,
                "right": right,
                "span": self._get_span(left, right).to_dict()
            }
        
        return left
    
    def _parse_comparison_expr(self) -> Optional[Dict[str, Any]]:
        """Parse comparison expression: additive_expr ('==' | '!=' | '<' | '>' | '<=' | '>=' additive_expr)?"""
        left = self._parse_additive_expr()
        if not left:
            return None
        
        comparison_ops = {
            TokenType.OP_EQ: "==",
            TokenType.OP_NEQ: "!=",
            TokenType.OP_LT: "<",
            TokenType.OP_GT: ">",
            TokenType.OP_LTE: "<=",
            TokenType.OP_GTE: ">=",
        }
        
        if self.current_token and self.current_token.token_type in comparison_ops:
            op_token = self.current_token
            self._advance()
            right = self._parse_additive_expr()
            if not right:
                return None
            
            return {
                "type": "binary_expression",
                "operator": comparison_ops[op_token.token_type],
                "left": left,
                "right": right,
                "span": self._get_span(left, right).to_dict()
            }
        
        return left
    
    def _parse_additive_expr(self) -> Optional[Dict[str, Any]]:
        """Parse additive expression: multiplicative_expr (('+' | '-' | ':=') multiplicative_expr)*"""
        left = self._parse_multiplicative_expr()
        if not left:
            return None
        
        while self.current_token and self.current_token.token_type in (
            TokenType.OP_PLUS, TokenType.OP_MINUS, TokenType.OP_ASSIGN
        ):
            op_token = self.current_token
            self._advance()
            right = self._parse_multiplicative_expr()
            if not right:
                return None
            
            op_map = {
                TokenType.OP_PLUS: "+",
                TokenType.OP_MINUS: "-",
                TokenType.OP_ASSIGN: ":=",
            }
            
            left = {
                "type": "binary_expression",
                "operator": op_map[op_token.token_type],
                "left": left,
                "right": right,
                "span": self._get_span(left, right).to_dict()
            }
        
        return left
    
    def _parse_multiplicative_expr(self) -> Optional[Dict[str, Any]]:
        """Parse multiplicative expression: unary_expr (('*' | '/') unary_expr)*"""
        left = self._parse_unary_expr()
        if not left:
            return None
        
        while self.current_token and self.current_token.token_type in (
            TokenType.OP_MUL, TokenType.OP_DIV
        ):
            op_token = self.current_token
            self._advance()
            right = self._parse_unary_expr()
            if not right:
                return None
            
            left = {
                "type": "binary_expression",
                "operator": op_token.value,
                "left": left,
                "right": right,
                "span": self._get_span(left, right).to_dict()
            }
        
        return left
    
    def _parse_unary_expr(self) -> Optional[Dict[str, Any]]:
        """Parse unary expression: ('not' | '-') unary_expr | primary"""
        if self.current_token and self.current_token.token_type == TokenType.KW_NOT:
            op_token = self.current_token
            self._advance()
            operand = self._parse_unary_expr()
            if not operand:
                return None
            
            return {
                "type": "unary_expression",
                "operator": "not",
                "operand": operand,
                "span": self._get_span_single(operand).to_dict()
            }
        
        if self.current_token and self.current_token.token_type == TokenType.OP_MINUS:
            op_token = self.current_token
            self._advance()
            operand = self._parse_unary_expr()
            if not operand:
                return None
            
            return {
                "type": "unary_expression",
                "operator": "-",
                "operand": operand,
                "span": self._get_span_single(operand).to_dict()
            }
        
        return self._parse_primary()
    
    def _parse_primary(self) -> Optional[Dict[str, Any]]:
        """Parse primary expression: identifier | number | string | '(' expr ')' | bool_literal | none_literal"""
        token = self.current_token
        
        if not token:
            self._error("Unexpected end of input")
            return None
        
        # Parenthesized expression
        if token.token_type == TokenType.DELIM_LPAREN:
            self._advance()
            expr = self._parse_expr()
            if not expr:
                return None
            if not self._match(TokenType.DELIM_RPAREN):
                self._error("Expected ')' to close expression", expected=")")
                return None
            return expr
        
        # Boolean literals
        if token.token_type == TokenType.KW_TRUE:
            self._advance()
            return {
                "type": "literal",
                "value_type": "bool",
                "value": True,
                "span": token.span.to_dict()
            }
        
        if token.token_type == TokenType.KW_FALSE:
            self._advance()
            return {
                "type": "literal",
                "value_type": "bool",
                "value": False,
                "span": token.span.to_dict()
            }
        
        # None literal
        if token.token_type == TokenType.KW_NONE:
            self._advance()
            return {
                "type": "literal",
                "value_type": "none",
                "value": None,
                "span": token.span.to_dict()
            }
        
        # Number literal
        if token.token_type == TokenType.NUMBER:
            self._advance()
            num_value = token.value
            is_float = '.' in num_value
            return {
                "type": "literal",
                "value_type": "float" if is_float else "int",
                "value": float(num_value) if is_float else int(num_value),
                "span": token.span.to_dict()
            }
        
        # String literal
        if token.token_type == TokenType.STRING:
            self._advance()
            return {
                "type": "literal",
                "value_type": "string",
                "value": token.value,
                "span": token.span.to_dict()
            }
        
        # Identifier
        if token.token_type == TokenType.IDENTIFIER:
            self._advance()
            return {
                "type": "identifier",
                "name": token.value,
                "span": token.span.to_dict()
            }
        
        self._error(f"Unexpected token: {token.value}")
        self._advance()
        return None
    
    def _match(self, token_type: TokenType) -> bool:
        """Match and consume a token of the given type."""
        if self.current_token and self.current_token.token_type == token_type:
            self._advance()
            return True
        return False
    
    def _advance(self) -> Optional[Token]:
        """Advance to the next token."""
        self.pos += 1
        return self.current_token
    
    def _current_span(self) -> Span:
        """Get the span of the current token."""
        if self.current_token:
            return self.current_token.span
        return Span()
    
    def _get_span(self, left: Dict[str, Any], right: Dict[str, Any]) -> Span:
        """Get a span that encompasses both expressions."""
        left_span = Span(**left.get("span", {}))
        right_span = Span(**right.get("span", {}))
        return left_span + right_span
    
    def _get_span_single(self, expr: Dict[str, Any]) -> Span:
        """Get the span of a single expression."""
        return Span(**expr.get("span", {}))
    
    def _get_span_from_tokens(self, statements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get a span from a list of statements."""
        if not statements:
            return {}
        first_span = Span(**statements[0].get("span", {}))
        last_span = Span(**statements[-1].get("span", {}))
        return (first_span + last_span).to_dict()
    
    def _error(
        self,
        message: str,
        expected: Optional[str] = None,
        found: Optional[str] = None,
        can_recover: bool = True
    ) -> None:
        """Record a parsing error."""
        span = self._current_span()
        error = ParseError(
            message=message,
            span=span,
            expected=expected,
            found=found,
            can_recover=can_recover
        )
        self.errors.append(error)


def parse_ghll(source: str, source_name: str = "") -> ParseResult:
    """
    Parse GHLL source code.
    
    Args:
        source: GHLL source code
        source_name: Name of the source (for provenance)
        
    Returns:
        ParseResult with AST or errors
    """
    tokenizer = Tokenizer(source, source_name)
    tokens = tokenizer.tokenize()
    parser = GHLLParser(tokens)
    return parser.parse()


def tokenize_ghll(source: str, source_name: str = "") -> List[Token]:
    """
    Tokenize GHLL source code.
    
    Args:
        source: GHLL source code
        source_name: Name of the source (for provenance)
        
    Returns:
        List of tokens
    """
    tokenizer = Tokenizer(source, source_name)
    return tokenizer.tokenize()

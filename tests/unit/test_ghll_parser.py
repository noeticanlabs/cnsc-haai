"""
Unit tests for GHLL Parser.

Tests cover:
- Tokenizer: lexical analysis
- Parser: recursive descent parsing
- AST generation with provenance
- Error handling and recovery
"""

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


import unittest


class TestTokenizer(unittest.TestCase):
    """Tests for the Tokenizer class."""

    def test_tokenize_keywords(self):
        """Test tokenizing keywords."""
        source = "if then else endif"
        tokens = tokenize_ghll(source)

        token_types = [t.token_type for t in tokens if t.token_type != TokenType.EOF]
        assert TokenType.KW_IF in token_types
        assert TokenType.KW_THEN in token_types
        assert TokenType.KW_ELSE in token_types
        assert TokenType.KW_ENDIF in token_types

    def test_tokenize_operators(self):
        """Test tokenizing operators."""
        source = "+ - * / := == != < > <= >="
        tokens = tokenize_ghll(source)

        token_types = [t.token_type for t in tokens if t.token_type != TokenType.EOF]
        assert TokenType.OP_PLUS in token_types
        assert TokenType.OP_MINUS in token_types
        assert TokenType.OP_MUL in token_types
        assert TokenType.OP_DIV in token_types
        assert TokenType.OP_ASSIGN in token_types
        assert TokenType.OP_EQ in token_types

    def test_tokenize_delimiters(self):
        """Test tokenizing delimiters."""
        source = "( ) [ ] { } , ; : ."
        tokens = tokenize_ghll(source)

        token_types = [t.token_type for t in tokens if t.token_type != TokenType.EOF]
        assert TokenType.DELIM_LPAREN in token_types
        assert TokenType.DELIM_RPAREN in token_types
        assert TokenType.DELIM_LBRACKET in token_types
        assert TokenType.DELIM_RBRACKET in token_types
        assert TokenType.DELIM_LBRACE in token_types
        assert TokenType.DELIM_RBRACE in token_types

    def test_tokenize_identifier(self):
        """Test tokenizing identifiers."""
        source = "foo bar baz123 _private"
        tokens = tokenize_ghll(source)

        identifiers = [t for t in tokens if t.token_type == TokenType.IDENTIFIER]
        assert len(identifiers) == 4
        assert identifiers[0].value == "foo"
        assert identifiers[1].value == "bar"
        assert identifiers[2].value == "baz123"
        assert identifiers[3].value == "_private"

    def test_tokenize_number(self):
        """Test tokenizing numbers."""
        source = "42 3.14 -7"
        tokens = tokenize_ghll(source)

        numbers = [t for t in tokens if t.token_type == TokenType.NUMBER]
        assert len(numbers) == 3
        assert numbers[0].value == "42"
        assert numbers[1].value == "3.14"
        assert numbers[2].value == "-7"

    def test_tokenize_string(self):
        """Test tokenizing strings."""
        source = '"hello" "world"'
        tokens = tokenize_ghll(source)

        strings = [t for t in tokens if t.token_type == TokenType.STRING]
        assert len(strings) == 2
        assert strings[0].value == "hello"
        assert strings[1].value == "world"

    def test_tokenize_string_with_escape(self):
        """Test tokenizing strings with escape sequences."""
        source = '"hello\\nworld\\t"'
        tokens = tokenize_ghll(source)

        strings = [t for t in tokens if t.token_type == TokenType.STRING]
        assert len(strings) == 1
        assert strings[0].value == "hello\nworld\t"

    def test_tokenize_whitespace(self):
        """Test that whitespace is skipped."""
        source = "x   +    y"
        tokens = tokenize_ghll(source)

        identifiers = [t for t in tokens if t.token_type == TokenType.IDENTIFIER]
        operators = [t for t in tokens if t.token_type == TokenType.OP_PLUS]

        assert len(identifiers) == 2
        assert len(operators) == 1

    def test_tokenize_comments(self):
        """Test that comments are skipped."""
        source = "x + y # this is a comment"
        tokens = tokenize_ghll(source)

        identifiers = [t for t in tokens if t.token_type == TokenType.IDENTIFIER]
        operators = [t for t in tokens if t.token_type == TokenType.OP_PLUS]

        # Should still have x, +, y
        assert len(identifiers) == 2
        assert len(operators) == 1

    def test_tokenize_multiline(self):
        """Test tokenizing multiline source."""
        source = "x := 1\ny := 2\nz := x + y"
        tokens = tokenize_ghll(source)

        identifiers = [t for t in tokens if t.token_type == TokenType.IDENTIFIER]
        assert len(identifiers) == 5  # x, y, z, x, y

    def test_token_spans(self):
        """Test that token spans are correct."""
        source = "if x"
        tokens = tokenize_ghll(source)

        if_token = [t for t in tokens if t.token_type == TokenType.KW_IF][0]
        ident_token = [t for t in tokens if t.token_type == TokenType.IDENTIFIER][0]

        # if starts at (1, 0)
        assert if_token.span.start == (1, 0)
        # x starts at (1, 3)
        assert ident_token.span.start == (1, 3)

    def test_eof_token(self):
        """Test that EOF token is added."""
        source = "x"
        tokens = tokenize_ghll(source)

        eof_token = tokens[-1]
        assert eof_token.token_type == TokenType.EOF


class TestGHLLParser(unittest.TestCase):
    """Tests for the GHLL Parser class."""

    def test_parse_identifier(self):
        """Test parsing a single identifier."""
        result = parse_ghll("x")

        assert result.success is True
        assert result.ast is not None
        assert result.ast["type"] == "program"
        assert len(result.ast["body"]) == 1
        assert result.ast["body"][0]["type"] == "identifier"
        assert result.ast["body"][0]["name"] == "x"

    def test_parse_number_literal(self):
        """Test parsing number literals."""
        result = parse_ghll("42")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["type"] == "literal"
        assert body["value"] == 42
        assert body["value_type"] == "int"

    def test_parse_float_literal(self):
        """Test parsing float literals."""
        result = parse_ghll("3.14")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["value_type"] == "float"
        assert body["value"] == 3.14

    def test_parse_string_literal(self):
        """Test parsing string literals."""
        result = parse_ghll('"hello"')

        assert result.success is True
        body = result.ast["body"][0]
        assert body["type"] == "literal"
        assert body["value_type"] == "string"
        assert body["value"] == "hello"

    def test_parse_boolean_literals(self):
        """Test parsing boolean literals."""
        result_true = parse_ghll("true")
        result_false = parse_ghll("false")

        assert result_true.success is True
        assert result_true.ast["body"][0]["value"] is True

        assert result_false.success is True
        assert result_false.ast["body"][0]["value"] is False

    def test_parse_none_literal(self):
        """Test parsing none literal."""
        result = parse_ghll("none")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["type"] == "literal"
        assert body["value"] is None
        assert body["value_type"] == "none"

    def test_parse_let_statement(self):
        """Test parsing let statement."""
        result = parse_ghll("let x := 42")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["type"] == "let_statement"
        assert body["variable"] == "x"
        assert body["value"]["value"] == 42

    def test_parse_binary_expression(self):
        """Test parsing binary expressions."""
        result = parse_ghll("x + y")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["type"] == "binary_expression"
        assert body["operator"] == "+"
        assert body["left"]["name"] == "x"
        assert body["right"]["name"] == "y"

    def test_parse_nested_expressions(self):
        """Test parsing nested expressions."""
        result = parse_ghll("(x + y) * z")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["operator"] == "*"
        assert body["left"]["type"] == "binary_expression"
        assert body["left"]["operator"] == "+"

    def test_parse_comparison(self):
        """Test parsing comparison operators."""
        result = parse_ghll("x == y")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["operator"] == "=="

    def test_parse_all_operators(self):
        """Test parsing all operators."""
        ops = ["+", "-", "*", "/", "==", "!=", "<", ">", "<=", ">="]

        for op in ops:
            result = parse_ghll(f"x {op} y")
            assert result.success is True, f"Failed for operator: {op}"

    def test_parse_logical_operators(self):
        """Test parsing logical operators."""
        result = parse_ghll("x and y or z")

        assert result.success is True
        body = result.ast["body"][0]

        # Should be left-associative
        assert body["operator"] == "or"
        assert body["left"]["operator"] == "and"

    def test_parse_unary_not(self):
        """Test parsing unary not."""
        result = parse_ghll("not x")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["type"] == "unary_expression"
        assert body["operator"] == "not"

    def test_parse_unary_minus(self):
        """Test parsing unary minus."""
        result = parse_ghll("-x")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["type"] == "unary_expression"
        assert body["operator"] == "-"

    def test_parse_if_statement(self):
        """Test parsing if statement."""
        result = parse_ghll("if x then y endif")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["type"] == "if_statement"
        assert body["condition"]["name"] == "x"
        assert len(body["then_branch"]) == 1
        assert body["then_branch"][0]["name"] == "y"
        assert body["else_branch"] is None

    def test_parse_if_else_statement(self):
        """Test parsing if-else statement."""
        result = parse_ghll("if x then y else z endif")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["else_branch"] is not None
        assert body["else_branch"][0]["name"] == "z"

    def test_parse_while_statement(self):
        """Test parsing while statement."""
        result = parse_ghll("while x do y := y + 1 endwhile")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["type"] == "while_statement"
        assert body["condition"]["name"] == "x"
        assert len(body["body"]) == 1

    def test_parse_for_statement(self):
        """Test parsing for statement."""
        result = parse_ghll("for i := 1 to 10 do x := x + i endfor")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["type"] == "for_statement"
        assert body["variable"] == "i"
        assert body["start"]["value"] == 1
        assert body["end"]["value"] == 10

    def test_parse_return_statement(self):
        """Test parsing return statement."""
        result = parse_ghll("return x + 1")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["type"] == "return_statement"
        assert body["value"]["operator"] == "+"

    def test_parse_assert_statement(self):
        """Test parsing assert statement."""
        result = parse_ghll("assert x > 0")

        assert result.success is True
        body = result.ast["body"][0]
        assert body["type"] == "assert_statement"
        assert body["condition"]["operator"] == ">"

    def test_parse_multiple_statements(self):
        """Test parsing multiple statements."""
        result = parse_ghll("x := 1\ny := 2\nz := x + y")

        assert result.success is True
        assert len(result.ast["body"]) == 3

    def test_parse_nested_control_flow(self):
        """Test parsing nested control flow."""
        source = """
        if x then
            if y then
                z := 1
            endif
        endif
        """
        result = parse_ghll(source)

        assert result.success is True
        outer_if = result.ast["body"][0]
        inner_if = outer_if["then_branch"][0]
        assert inner_if["type"] == "if_statement"

    def test_parse_error_unexpected_token(self):
        """Test parsing error on unexpected token."""
        result = parse_ghll("x := @invalid")

        assert result.success is False
        assert len(result.errors) > 0

    def test_parse_error_missing_endif(self):
        """Test parsing error on missing endif."""
        result = parse_ghll("if x then y")

        assert result.success is False
        assert len(result.errors) > 0

    def test_parse_error_missing_semi(self):
        """Test that missing semicolons don't cause errors (GHLL uses newlines)."""
        result = parse_ghll("x := 1 y := 2")

        # This should be a single expression statement
        assert result.success is True

    def test_parse_result_tokens(self):
        """Test that parse result includes tokens."""
        result = parse_ghll("x + y")

        assert len(result.tokens) > 0

    def test_parse_result_provenance(self):
        """Test that parse result includes provenance."""
        result = parse_ghll("x + y")

        assert result.provenance is not None
        assert "source" in result.provenance or result.provenance == {}

    def test_parse_empty_program(self):
        """Test parsing empty program."""
        result = parse_ghll("")

        assert result.success is True
        assert result.ast["type"] == "program"
        assert len(result.ast["body"]) == 0

    def test_parse_complex_expression(self):
        """Test parsing complex expression."""
        source = "if (x + y) * z > 10 and not (a == b) then result := true endif"
        result = parse_ghll(source)

        assert result.success is True
        assert result.ast["body"][0]["type"] == "if_statement"

    def test_precedence_parsing(self):
        """Test that operator precedence is correct."""
        # * should bind tighter than +
        result = parse_ghll("x + y * z")

        body = result.ast["body"][0]
        assert body["operator"] == "+"
        assert body["right"]["operator"] == "*"

    def test_left_associativity(self):
        """Test left associativity of binary operators."""
        result = parse_ghll("x - y - z")

        body = result.ast["body"][0]
        assert body["operator"] == "-"
        # Left side should be another binary expression (x - y)
        assert body["left"]["type"] == "binary_expression"
        assert body["left"]["operator"] == "-"
        assert body["left"]["left"]["name"] == "x"
        assert body["left"]["right"]["name"] == "y"
        assert body["right"]["name"] == "z"


class TestSpan(unittest.TestCase):
    """Tests for Span class."""

    def test_span_creation(self):
        """Test creating a span."""
        span = Span(start=(1, 0), end=(1, 5), source="test.ghll")

        assert span.start == (1, 0)
        assert span.end == (1, 5)
        assert span.source == "test.ghll"

    def test_span_addition(self):
        """Test combining spans."""
        span1 = Span(start=(1, 0), end=(1, 3), source="test.ghll")
        span2 = Span(start=(1, 4), end=(1, 7), source="test.ghll")

        combined = span1 + span2

        assert combined.start == (1, 0)
        assert combined.end == (1, 7)

    def test_span_serialization(self):
        """Test span serialization."""
        span = Span(start=(1, 0), end=(1, 5), source="test.ghll")

        data = span.to_dict()

        assert data["start"] == [1, 0]
        assert data["end"] == [1, 5]
        assert data["source"] == "test.ghll"


class TestParseResult(unittest.TestCase):
    """Tests for ParseResult class."""

    def test_parse_result_success(self):
        """Test successful parse result."""
        result = parse_ghll("x")

        assert result.success is True
        assert result.has_errors is False
        assert result.ast is not None

    def test_parse_result_failure(self):
        """Test failed parse result."""
        result = parse_ghll("invalid@token")

        assert result.success is False
        assert result.has_errors is True
        assert len(result.errors) > 0

    def test_parse_result_serialization(self):
        """Test parse result serialization."""
        result = parse_ghll("x + y")

        data = result.to_dict()

        assert "success" in data
        assert "ast" in data
        assert "errors" in data
        assert "token_count" in data


class TestParserEdgeCases(unittest.TestCase):
    """Edge case tests for parser."""

    def test_whitespace_only(self):
        """Test parsing whitespace-only source."""
        result = parse_ghll("   \n\t\n   ")

        assert result.success is True
        assert len(result.ast["body"]) == 0

    def test_deep_nesting(self):
        """Test deep expression nesting."""
        source = "((((((x))))))"
        result = parse_ghll(source)

        assert result.success is True
        assert result.ast["body"][0]["name"] == "x"

    def test_all_keywords(self):
        """Test parsing all keywords in valid contexts."""
        # Keywords alone are not valid GHLL - they need proper syntax
        source = "if then else endif while do endwhile for to endfor return assert let in where true false none"
        result = parse_ghll(source)

        # This should fail because keywords need proper syntax
        assert result.success is False
        assert len(result.errors) > 0

    def test_complex_block(self):
        """Test parsing a complex code block."""
        source = """
        let x := 10
        let y := 20
        if x < y then
            let max := y
        else
            let max := x
        endif
        return max
        """
        result = parse_ghll(source)

        assert result.success is True
        assert len(result.ast["body"]) == 4  # let, let, if, return

    def test_mixed_case_keywords(self):
        """Test that keywords are case-sensitive."""
        result_if = parse_ghll("if x then y endif")
        result_if_upper = parse_ghll("IF x THEN y ENDIF")

        assert result_if.success is True
        # IF (uppercase) should be parsed as identifier, not keyword
        assert result_if_upper.success is True
        # When IF is uppercase, it's parsed as an identifier, not an if statement
        assert result_if_upper.ast["body"][0]["type"] == "identifier"
        assert result_if_upper.ast["body"][0]["name"] == "IF"

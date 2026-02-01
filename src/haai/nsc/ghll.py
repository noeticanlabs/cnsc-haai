"""
GHLL (Noetica High-Level Glyph Language) implementation.

Implements GHLL parser, semantic analyzer, operator semantics, and compiler
as defined in the GHLL specification.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import logging
import re
import ast

logger = logging.getLogger(__name__)


class GHLLOperator(Enum):
    """GHLL operators as defined in specification."""
    PHI = "φ"        # introduce θ
    CIRCLE = "◯"      # diffusion term ∇²θ
    RHO = "↻"        # curvature/topology coupling R·θ
    PLUS = "⊕"       # signed source/sink +s
    MINUS = "⊖"      # signed source/sink -s
    DELTA = "∆"       # close to EOM
    BOX = "□"         # boundary
    ARROW = "⇒"       # transform/time boundary


class GHLLTokenType(Enum):
    """GHLL token types."""
    OPERATOR = "operator"
    IDENTIFIER = "identifier"
    NUMBER = "number"
    STRING = "string"
    KEYWORD = "keyword"
    DELIMITER = "delimiter"
    CONTRACT = "contract"


@dataclass
class GHLLToken:
    """GHLL token."""
    type: GHLLTokenType
    value: str
    position: Tuple[int, int]  # (line, column)
    
    def __repr__(self) -> str:
        return f"Token({self.type.value}, '{self.value}', {self.position})"


@dataclass
class GHLLContract:
    """GHLL contract specification."""
    name: str
    requires: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)
    ensures: List[str] = field(default_factory=list)
    mode: str = "soft"  # hard/soft by mode
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'requires': self.requires,
            'invariants': self.invariants,
            'ensures': self.ensures,
            'mode': self.mode
        }


@dataclass
class GHLLOperatorNode:
    """GHLL operator AST node."""
    operator: GHLLOperator
    operands: List[Any] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    position: Tuple[int, int] = (0, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': 'operator',
            'operator': self.operator.value,
            'operands': [self._node_to_dict(op) for op in self.operands],
            'parameters': self.parameters,
            'position': self.position
        }
    
    def _node_to_dict(self, node: Any) -> Any:
        """Convert node to dictionary recursively."""
        if isinstance(node, GHLLOperatorNode):
            return node.to_dict()
        elif isinstance(node, GHLLContract):
            return node.to_dict()
        elif isinstance(node, GHLLIdentifier):
            return node.to_dict()
        elif isinstance(node, list):
            return [self._node_to_dict(item) for item in node]
        else:
            return node


@dataclass
class GHLLIdentifier:
    """GHLL identifier AST node."""
    name: str
    type_annotation: Optional[str] = None
    position: Tuple[int, int] = (0, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': 'identifier',
            'name': self.name,
            'type_annotation': self.type_annotation,
            'position': self.position
        }


class GHLLError(Exception):
    """GHLL-specific error."""
    pass


class GHLLLexer:
    """GHLL lexical analyzer."""
    
    KEYWORDS = {
        'requires', 'invariants', 'ensures', 'contract', 'hard', 'soft',
        'let', 'in', 'if', 'then', 'else', 'for', 'while', 'return'
    }
    
    OPERATORS = {
        'φ', '↻', '⊕', '⊖', '◯', '∆', '□', '⇒'
    }
    
    DELIMITERS = {
        '(', ')', '[', ']', '{', '}', ';', ':', ',', '=', '==', '!=', 
        '<', '>', '<=', '>=', '+', '-', '*', '/', '^'
    }
    
    def __init__(self):
        self.tokens: List[GHLLToken] = []
        self.position = (1, 1)
    
    def tokenize(self, input_text: str) -> List[GHLLToken]:
        """Tokenize input text."""
        self.tokens = []
        self.position = (1, 1)
        
        i = 0
        while i < len(input_text):
            char = input_text[i]
            
            # Skip whitespace
            if char.isspace():
                self._advance_position(char)
                i += 1
                continue
            
            # Check for operators (multi-character)
            operator_found = False
            for op in sorted(self.OPERATORS, key=len, reverse=True):
                if input_text.startswith(op, i):
                    self.tokens.append(GHLLToken(
                        GHLLTokenType.OPERATOR,
                        op,
                        self.position
                    ))
                    for c in op:
                        self._advance_position(c)
                    i += len(op)
                    operator_found = True
                    break
            
            if operator_found:
                continue
            
            # Check for delimiters (multi-character)
            delimiter_found = False
            for delim in sorted(self.DELIMITERS, key=len, reverse=True):
                if input_text.startswith(delim, i):
                    self.tokens.append(GHLLToken(
                        GHLLTokenType.DELIMITER,
                        delim,
                        self.position
                    ))
                    for c in delim:
                        self._advance_position(c)
                    i += len(delim)
                    delimiter_found = True
                    break
            
            if delimiter_found:
                continue
            
            # Check for numbers
            if char.isdigit() or char == '.':
                start_pos = self.position
                number = self._parse_number(input_text, i)
                self.tokens.append(GHLLToken(
                    GHLLTokenType.NUMBER,
                    number,
                    start_pos
                ))
                i += len(number)
                continue
            
            # Check for strings
            if char == '"' or char == "'":
                start_pos = self.position
                string = self._parse_string(input_text, i)
                self.tokens.append(GHLLToken(
                    GHLLTokenType.STRING,
                    string,
                    start_pos
                ))
                i += len(string) + 2  # +2 for quotes
                continue
            
            # Check for identifiers and keywords
            if char.isalpha() or char == '_':
                start_pos = self.position
                identifier = self._parse_identifier(input_text, i)
                
                token_type = (GHLLTokenType.KEYWORD 
                            if identifier in self.KEYWORDS 
                            else GHLLTokenType.IDENTIFIER)
                
                self.tokens.append(GHLLToken(
                    token_type,
                    identifier,
                    start_pos
                ))
                i += len(identifier)
                continue
            
            # Unknown character
            raise GHLLError(f"Unexpected character '{char}' at {self.position}")
        
        return self.tokens
    
    def _advance_position(self, char: str) -> None:
        """Advance position tracking."""
        if char == '\n':
            self.position = (self.position[0] + 1, 1)
        else:
            self.position = (self.position[0], self.position[1] + 1)
    
    def _parse_number(self, text: str, start: int) -> str:
        """Parse number from text."""
        i = start
        while i < len(text) and (text[i].isdigit() or text[i] == '.'):
            i += 1
        return text[start:i]
    
    def _parse_string(self, text: str, start: int) -> str:
        """Parse string from text."""
        quote_char = text[start]
        i = start + 1
        string_content = ""
        
        while i < len(text) and text[i] != quote_char:
            if text[i] == '\\':  # Escape sequence
                i += 1
                if i < len(text):
                    string_content += text[i]
                    i += 1
            else:
                string_content += text[i]
                i += 1
        
        return string_content
    
    def _parse_identifier(self, text: str, start: int) -> str:
        """Parse identifier from text."""
        i = start
        while i < len(text) and (text[i].isalnum() or text[i] == '_'):
            i += 1
        return text[start:i]


class GHLLParser:
    """GHLL parser that builds AST from tokens."""
    
    def __init__(self):
        self.tokens: List[GHLLToken] = []
        self.current = 0
    
    def parse(self, tokens: List[GHLLToken]) -> List[Any]:
        """Parse tokens into AST."""
        self.tokens = tokens
        self.current = 0
        nodes = []
        
        while not self._is_at_end():
            node = self._parse_statement()
            if node:
                nodes.append(node)
        
        return nodes
    
    def _parse_statement(self) -> Optional[Any]:
        """Parse a statement."""
        if self._match(GHLLTokenType.KEYWORD, 'contract'):
            return self._parse_contract()
        elif self._match(GHLLTokenType.OPERATOR):
            return self._parse_operator_expression()
        elif self._match(GHLLTokenType.IDENTIFIER):
            return self._parse_assignment()
        else:
            return self._parse_expression()
    
    def _parse_contract(self) -> GHLLContract:
        """Parse contract definition."""
        name = self._consume(GHLLTokenType.IDENTIFIER, "Expected contract name").value
        
        # Parse contract body
        contract = GHLLContract(name=name)
        
        while not self._is_at_end() and not self._check(GHLLTokenType.DELIMITER, '}'):
            if self._match(GHLLTokenType.KEYWORD, 'requires'):
                contract.requires.extend(self._parse_requirement_list())
            elif self._match(GHLLTokenType.KEYWORD, 'invariants'):
                contract.invariants.extend(self._parse_requirement_list())
            elif self._match(GHLLTokenType.KEYWORD, 'ensures'):
                contract.ensures.extend(self._parse_requirement_list())
            elif self._match(GHLLTokenType.KEYWORD, 'hard'):
                contract.mode = "hard"
            elif self._match(GHLLTokenType.KEYWORD, 'soft'):
                contract.mode = "soft"
            else:
                self._advance()
        
        return contract
    
    def _parse_requirement_list(self) -> List[str]:
        """Parse list of requirements."""
        requirements = []
        
        self._consume(GHLLTokenType.DELIMITER, ':', "Expected ':' after keyword")
        
        while not self._is_at_end() and not self._check(GHLLTokenType.DELIMITER, ';'):
            if self._check(GHLLTokenType.IDENTIFIER) or self._check(GHLLTokenType.STRING):
                requirements.append(self._advance().value)
            else:
                # Parse expression as string
                expr = self._parse_expression()
                requirements.append(str(expr))
            
            if self._match(GHLLTokenType.DELIMITER, ','):
                continue
        
        return requirements
    
    def _parse_operator_expression(self) -> GHLLOperatorNode:
        """Parse operator expression."""
        operator_token = self._previous()
        operator = GHLLOperator(operator_token.value)
        
        node = GHLLOperatorNode(
            operator=operator,
            position=operator_token.position
        )
        
        # Parse operands
        while not self._is_at_end() and not self._check(GHLLTokenType.DELIMITER, ';'):
            if self._check(GHLLTokenType.OPERATOR):
                operand = self._parse_operator_expression()
            elif self._check(GHLLTokenType.IDENTIFIER):
                operand = GHLLIdentifier(
                    name=self._advance().value,
                    position=self._previous().position
                )
            elif self._check(GHLLTokenType.NUMBER):
                operand = float(self._advance().value)
            else:
                break
            
            node.operands.append(operand)
        
        return node
    
    def _parse_assignment(self) -> Dict[str, Any]:
        """Parse assignment statement."""
        identifier = self._previous().value
        
        if self._match(GHLLTokenType.DELIMITER, '='):
            value = self._parse_expression()
            return {
                'type': 'assignment',
                'identifier': identifier,
                'value': value
            }
        
        return GHLLIdentifier(name=identifier, position=self._previous().position)
    
    def _parse_expression(self) -> Any:
        """Parse general expression."""
        # Simplified expression parsing
        if self._check(GHLLTokenType.NUMBER):
            return float(self._advance().value)
        elif self._check(GHLLTokenType.STRING):
            return self._advance().value
        elif self._check(GHLLTokenType.IDENTIFIER):
            return GHLLIdentifier(name=self._advance().value, position=self._previous().position)
        else:
            return self._advance()
    
    def _match(self, token_type: GHLLTokenType, value: Optional[str] = None) -> bool:
        """Check if current token matches."""
        if self._check(token_type, value):
            self._advance()
            return True
        return False
    
    def _check(self, token_type: GHLLTokenType, value: Optional[str] = None) -> bool:
        """Check current token."""
        if self._is_at_end():
            return False
        
        token = self.tokens[self.current]
        if token.type != token_type:
            return False
        
        if value is not None and token.value != value:
            return False
        
        return True
    
    def _advance(self) -> GHLLToken:
        """Advance to next token."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()
    
    def _is_at_end(self) -> bool:
        """Check if at end of tokens."""
        return self.current >= len(self.tokens)
    
    def _previous(self) -> GHLLToken:
        """Get previous token."""
        return self.tokens[self.current - 1]
    
    def _consume(self, token_type: GHLLTokenType, value: Union[str, None], message: str) -> GHLLToken:
        """Consume token with error checking."""
        if self._check(token_type, value):
            return self._advance()
        
        raise GHLLError(f"{message} at position {self.tokens[self.current].position if self.current < len(self.tokens) else 'EOF'}")


class GHLLSemanticAnalyzer:
    """GHLL semantic analyzer for type checking and validation."""
    
    def __init__(self):
        self.symbol_table: Dict[str, Dict[str, Any]] = {}
        self.contracts: Dict[str, GHLLContract] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def analyze(self, ast_nodes: List[Any]) -> Dict[str, Any]:
        """Analyze AST nodes."""
        self.errors.clear()
        self.warnings.clear()
        
        for node in ast_nodes:
            self._analyze_node(node)
        
        return {
            'success': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'symbol_table': self.symbol_table,
            'contracts': {name: contract.to_dict() for name, contract in self.contracts.items()}
        }
    
    def _analyze_node(self, node: Any) -> None:
        """Analyze individual AST node."""
        if isinstance(node, GHLLContract):
            self._analyze_contract(node)
        elif isinstance(node, GHLLOperatorNode):
            self._analyze_operator(node)
        elif isinstance(node, dict) and node.get('type') == 'assignment':
            self._analyze_assignment(node)
    
    def _analyze_contract(self, contract: GHLLContract) -> None:
        """Analyze contract."""
        if contract.name in self.contracts:
            self.errors.append(f"Contract '{contract.name}' already defined")
            return
        
        self.contracts[contract.name] = contract
        
        # Validate contract requirements
        for req in contract.requires:
            if not self._is_valid_requirement(req):
                self.warnings.append(f"Invalid requirement in contract '{contract.name}': {req}")
        
        # Validate invariants
        for invariant in contract.invariants:
            if not self._is_valid_requirement(invariant):
                self.warnings.append(f"Invalid invariant in contract '{contract.name}': {invariant}")
    
    def _analyze_operator(self, node: GHLLOperatorNode) -> None:
        """Analyze operator node."""
        # Check operator semantics
        if not self._validate_operator_semantics(node):
            self.errors.append(f"Invalid operator usage: {node.operator.value} at {node.position}")
        
        # Analyze operands
        for operand in node.operands:
            self._analyze_node(operand)
    
    def _analyze_assignment(self, assignment: Dict[str, Any]) -> None:
        """Analyze assignment."""
        identifier = assignment['identifier']
        value = assignment['value']
        
        # Check if identifier is already defined
        if identifier in self.symbol_table:
            self.warnings.append(f"Variable '{identifier}' redefined")
        
        # Add to symbol table
        self.symbol_table[identifier] = {
            'type': self._infer_type(value),
            'value': value
        }
    
    def _validate_operator_semantics(self, node: GHLLOperatorNode) -> bool:
        """Validate operator semantics according to specification."""
        operator = node.operator
        
        # Phase-1 operator meanings from specification
        if operator == GHLLOperator.PHI:
            # φ introduce θ - should have operands for θ definition
            return len(node.operands) >= 1
        elif operator == GHLLOperator.CIRCLE:
            # ◯ diffusion term ∇²θ - operates on θ
            return len(node.operands) >= 1
        elif operator == GHLLOperator.RHO:
            # ↻ curvature/topology coupling R·θ
            return len(node.operands) >= 1
        elif operator in [GHLLOperator.PLUS, GHLLOperator.MINUS]:
            # ⊕/⊖ signed source/sink ±s
            return len(node.operands) >= 1
        elif operator == GHLLOperator.DELTA:
            # ∆ close to EOM
            return True  # Can be standalone
        elif operator == GHLLOperator.BOX:
            # □ boundary
            return len(node.operands) >= 1
        elif operator == GHLLOperator.ARROW:
            # ⇒ transform/time boundary
            return len(node.operands) >= 2
        
        return False
    
    def _is_valid_requirement(self, requirement: str) -> bool:
        """Check if requirement is valid."""
        # Simplified validation - check if it's a valid expression
        try:
            # Try to parse as Python expression for basic validation
            ast.parse(requirement, mode='eval')
            return True
        except:
            return False
    
    def _infer_type(self, value: Any) -> str:
        """Infer type of value."""
        if isinstance(value, (int, float)):
            return 'number'
        elif isinstance(value, str):
            return 'string'
        elif isinstance(value, GHLLIdentifier):
            return 'identifier'
        elif isinstance(value, GHLLOperatorNode):
            return 'operator'
        else:
            return 'unknown'


class GHLLCompiler:
    """GHLL compiler that lowers to NSC IR with provenance."""
    
    def __init__(self):
        self.compilation_history: List[Dict[str, Any]] = []
        self.provenance_tracker: Dict[str, List[str]] = {}
    
    def compile_to_nsc(self, ast_nodes: List[Any], semantic_result: Dict[str, Any]) -> Dict[str, Any]:
        """Compile GHLL AST to NSC intermediate representation."""
        start_time = time.time()
        
        if not semantic_result['success']:
            return {
                'success': False,
                'errors': semantic_result['errors'],
                'compilation_time': time.time() - start_time
            }
        
        try:
            nsc_ir = []
            source_spans = []
            
            for i, node in enumerate(ast_nodes):
                compilation_result = self._compile_node(node, i)
                nsc_ir.extend(compilation_result['ir'])
                source_spans.extend(compilation_result['spans'])
            
            compilation_time = time.time() - start_time
            
            result = {
                'success': True,
                'nsc_ir': nsc_ir,
                'source_spans': source_spans,
                'compilation_time': compilation_time,
                'contracts': semantic_result['contracts']
            }
            
        except Exception as e:
            logger.error(f"GHLL compilation failed: {e}")
            result = {
                'success': False,
                'error': str(e),
                'compilation_time': time.time() - start_time
            }
        
        # Record compilation
        self.compilation_history.append({
            'timestamp': time.time(),
            'ast_nodes': len(ast_nodes),
            'result': result
        })
        
        return result
    
    def _compile_node(self, node: Any, node_index: int) -> Dict[str, Any]:
        """Compile individual AST node to NSC IR."""
        if isinstance(node, GHLLOperatorNode):
            return self._compile_operator(node, node_index)
        elif isinstance(node, GHLLContract):
            return self._compile_contract(node, node_index)
        elif isinstance(node, dict) and node.get('type') == 'assignment':
            return self._compile_assignment(node, node_index)
        else:
            return {'ir': [], 'spans': []}
    
    def _compile_operator(self, node: GHLLOperatorNode, node_index: int) -> Dict[str, Any]:
        """Compile operator to NSC IR."""
        ir_instructions = []
        spans = []
        
        # Map GHLL operators to NSC opcodes
        operator_mapping = {
            GHLLOperator.PHI: "φ",
            GHLLOperator.CIRCLE: "◯",
            GHLLOperator.RHO: "↻",
            GHLLOperator.PLUS: "⊕",
            GHLLOperator.MINUS: "⊖",
            GHLLOperator.DELTA: "∆",
            GHLLOperator.BOX: "□",
            GHLLOperator.ARROW: "⇒"
        }
        
        nsc_operator = operator_mapping.get(node.operator, node.operator.value)
        
        # Generate NSC instruction
        instruction = nsc_operator
        
        # Add operands as parameters
        for operand in node.operands:
            if isinstance(operand, GHLLIdentifier):
                instruction += f" {operand.name}"
            elif isinstance(operand, (int, float)):
                instruction += f" {operand}"
        
        ir_instructions.append(instruction)
        spans.append({
            'node_index': node_index,
            'operator': node.operator.value,
            'position': node.position
        })
        
        return {'ir': ir_instructions, 'spans': spans}
    
    def _compile_contract(self, contract: GHLLContract, node_index: int) -> Dict[str, Any]:
        """Compile contract to NSC IR (gate checks)."""
        ir_instructions = []
        spans = []
        
        # Compile contract as gate checks in NSC
        for requirement in contract.requires:
            instruction = f"check_requirement {requirement}"
            ir_instructions.append(instruction)
        
        for invariant in contract.invariants:
            instruction = f"check_invariant {invariant}"
            ir_instructions.append(instruction)
        
        spans.append({
            'node_index': node_index,
            'contract': contract.name,
            'type': 'contract'
        })
        
        return {'ir': ir_instructions, 'spans': spans}
    
    def _compile_assignment(self, assignment: Dict[str, Any], node_index: int) -> Dict[str, Any]:
        """Compile assignment to NSC IR."""
        ir_instructions = []
        spans = []
        
        identifier = assignment['identifier']
        value = assignment['value']
        
        instruction = f"let {identifier} = {value}"
        ir_instructions.append(instruction)
        
        spans.append({
            'node_index': node_index,
            'assignment': identifier,
            'type': 'assignment'
        })
        
        return {'ir': ir_instructions, 'spans': spans}


class GHLLProcessor:
    """High-level GHLL processor that coordinates parsing, analysis, and compilation."""
    
    def __init__(self):
        self.lexer = GHLLLexer()
        self.parser = GHLLParser()
        self.semantic_analyzer = GHLLSemanticAnalyzer()
        self.compiler = GHLLCompiler()
        self.processing_history: List[Dict[str, Any]] = []
    
    def process(self, input_text: str) -> Dict[str, Any]:
        """Process GHLL input end-to-end."""
        start_time = time.time()
        
        try:
            # Lexical analysis
            tokens = self.lexer.tokenize(input_text)
            
            # Parsing
            ast_nodes = self.parser.parse(tokens)
            
            # Semantic analysis
            semantic_result = self.semantic_analyzer.analyze(ast_nodes)
            
            # Compilation to NSC
            compilation_result = self.compiler.compile_to_nsc(ast_nodes, semantic_result)
            
            processing_time = time.time() - start_time
            
            result = {
                'success': compilation_result['success'],
                'tokens': len(tokens),
                'ast_nodes': len(ast_nodes),
                'semantic_result': semantic_result,
                'compilation_result': compilation_result,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"GHLL processing failed: {e}")
            result = {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
        
        # Record processing
        self.processing_history.append({
            'timestamp': time.time(),
            'input_length': len(input_text),
            'result': result
        })
        
        return result
    
    def get_processor_summary(self) -> Dict[str, Any]:
        """Get summary of processor state."""
        if not self.processing_history:
            return {"status": "no_history"}
        
        successful = sum(1 for h in self.processing_history if h['result']['success'])
        total = len(self.processing_history)
        
        return {
            'total_processed': total,
            'successful': successful,
            'success_rate': successful / total if total > 0 else 0.0,
            'compilation_history_size': len(self.compiler.compilation_history),
            'contracts_defined': len(self.semantic_analyzer.contracts),
            'symbols_defined': len(self.semantic_analyzer.symbol_table)
        }
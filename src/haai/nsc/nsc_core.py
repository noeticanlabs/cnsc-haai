"""
NSC (Noetic Compiler) core implementation.

Implements the NSC packet format, grammar compiler, bytecode generation,
and virtual machine as defined in the NSC specification.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import hashlib
import logging
import re

logger = logging.getLogger(__name__)


class NSCMode(Enum):
    """NSC execution modes."""
    SYMBOLIC = "symbolic"
    MATH = "math"
    EXEC = "exec"


@dataclass
class NSCPacket:
    """NSC packet format as defined in NSC specification."""
    header: Dict[str, Any]
    body: str
    footer: Dict[str, Any]
    
    def __init__(self, content: str, mode: NSCMode = NSCMode.SYMBOLIC, author: str = "HAAI"):
        self.header = {
            'version': '6.1',
            'author': author,
            'mode': mode.value,
            'timestamp': time.time()
        }
        self.body = content
        self.footer = {
            'hash': self._calculate_hash()
        }
    
    def _calculate_hash(self) -> str:
        """Calculate coherence CRC32 hash."""
        content = f"{self.header}{self.body}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def validate(self) -> bool:
        """Validate packet integrity."""
        calculated_hash = self._calculate_hash()
        return calculated_hash == self.footer.get('hash')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert packet to dictionary."""
        return {
            'header': self.header,
            'body': self.body,
            'footer': self.footer
        }


class NSCGlyph(Enum):
    """NSC glyphs as defined in specification."""
    PHI = "φ"        # load θ
    RHO = "↻"        # curvature coupling
    PLUS = "⊕"       # source +s
    MINUS = "⊖"      # sink -s
    CIRCLE = "◯"      # ∇²θ
    DELTA = "∆"       # close EOM
    ARROW = "⇒"      # time marker
    BOX = "□"         # boundary
    LEFT_ARROW = "⇐"  # reverse time
    CIRCLE_CCW = "↺"  # counter-clockwise


@dataclass
class NSCBytecode:
    """NSC bytecode instruction."""
    opcode: int
    operand: Optional[Union[str, float, int]] = None
    comment: str = ""
    
    def to_bytes(self) -> bytes:
        """Convert to byte representation."""
        result = bytes([self.opcode])
        if self.operand is not None:
            if isinstance(self.operand, str):
                operand_bytes = self.operand.encode('utf-8')
                result += len(operand_bytes).to_bytes(1, 'big') + operand_bytes
            elif isinstance(self.operand, (int, float)):
                operand_bytes = str(self.operand).encode('utf-8')
                result += len(operand_bytes).to_bytes(1, 'big') + operand_bytes
        return result


class NSCGrammar:
    """NSC grammar parser based on EBNF specification."""
    
    # Grammar rules from specification
    GRAMMAR_RULES = {
        'program': r'sentence(?:;sentence)*',
        'sentence': r'phrase(?:⇒phrase)?',
        'phrase': r'(?:atom|group)+',
        'group': r'\[phrase\]|\(phrase\)',
        'atom': r'[φ↻⊕⊖◯□∆↺⇐⇒]'
    }
    
    def __init__(self):
        self.compiled_rules = {}
        for rule_name, pattern in self.GRAMMAR_RULES.items():
            self.compiled_rules[rule_name] = re.compile(pattern)
    
    def parse(self, input_string: str) -> Dict[str, List[str]]:
        """Parse input string according to NSC grammar."""
        # Clean input
        cleaned = input_string.strip()
        
        # Parse program (top-level)
        sentences = re.split(r';', cleaned)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Parse each sentence
        parsed_sentences = []
        for sentence in sentences:
            parsed_sentence = self._parse_sentence(sentence)
            parsed_sentences.append(parsed_sentence)
        
        return {
            'program': parsed_sentences,
            'raw_input': input_string,
            'sentence_count': len(parsed_sentences)
        }
    
    def _parse_sentence(self, sentence: str) -> Dict[str, Any]:
        """Parse individual sentence."""
        # Check for transformation arrow
        if '⇒' in sentence:
            parts = sentence.split('⇒')
            left_phrase = parts[0].strip()
            right_phrase = parts[1].strip() if len(parts) > 1 else ""
            
            return {
                'type': 'transformation',
                'left_phrase': self._parse_phrase(left_phrase),
                'right_phrase': self._parse_phrase(right_phrase) if right_phrase else None
            }
        else:
            return {
                'type': 'statement',
                'phrase': self._parse_phrase(sentence)
            }
    
    def _parse_phrase(self, phrase: str) -> List[Dict[str, Any]]:
        """Parse phrase into atoms and groups."""
        result = []
        i = 0
        
        while i < len(phrase):
            char = phrase[i]
            
            if char in '([':
                # Handle group
                group_end = self._find_matching_bracket(phrase, i, char)
                if group_end == -1:
                    raise ValueError(f"Unmatched bracket at position {i}")
                
                group_content = phrase[i+1:group_end]
                parsed_group = self._parse_phrase(group_content)
                
                result.append({
                    'type': 'group',
                    'bracket': char,
                    'content': parsed_group
                })
                i = group_end + 1
            elif char in [glyph.value for glyph in NSCGlyph]:
                result.append({
                    'type': 'atom',
                    'glyph': char
                })
                i += 1
            else:
                # Skip whitespace and unknown characters
                i += 1
        
        return result
    
    def _find_matching_bracket(self, string: str, start: int, opening: str) -> int:
        """Find matching closing bracket."""
        closing = ']' if opening == '[' else ')'
        depth = 1
        i = start + 1
        
        while i < len(string) and depth > 0:
            if string[i] == opening:
                depth += 1
            elif string[i] == closing:
                depth -= 1
            i += 1
        
        return i - 1 if depth == 0 else -1


class NSCCompiler:
    """NSC compiler that parses grammar and generates bytecode."""
    
    # Opcode mapping from specification
    OPCODES = {
        NSCGlyph.PHI: 0x01,
        NSCGlyph.RHO: 0x02,
        NSCGlyph.PLUS: 0x03,
        NSCGlyph.MINUS: 0x04,
        NSCGlyph.CIRCLE: 0x05,
        NSCGlyph.DELTA: 0x06,
        NSCGlyph.ARROW: 0x07,
        NSCGlyph.BOX: 0x08,
        NSCGlyph.LEFT_ARROW: 0x09,
        NSCGlyph.CIRCLE_CCW: 0x0A
    }
    
    def __init__(self):
        self.grammar = NSCGrammar()
        self.compilation_history: List[Dict[str, Any]] = []
    
    def compile(self, packet: NSCPacket) -> List[NSCBytecode]:
        """Compile NSC packet to bytecode."""
        try:
            # Validate packet
            if not packet.validate():
                raise ValueError("Packet validation failed")
            
            # Parse grammar
            parsed = self.grammar.parse(packet.body)
            
            # Generate bytecode
            bytecode = self._generate_bytecode(parsed)
            
            # Record compilation
            self.compilation_history.append({
                'timestamp': time.time(),
                'packet_hash': packet.footer['hash'],
                'parsed_structure': parsed,
                'bytecode_length': len(bytecode),
                'success': True
            })
            
            return bytecode
            
        except Exception as e:
            logger.error(f"Compilation failed: {e}")
            self.compilation_history.append({
                'timestamp': time.time(),
                'packet_hash': packet.footer.get('hash', 'unknown'),
                'error': str(e),
                'success': False
            })
            raise
    
    def _generate_bytecode(self, parsed: Dict[str, Any]) -> List[NSCBytecode]:
        """Generate bytecode from parsed structure."""
        bytecode = []
        
        for sentence in parsed['program']:
            sentence_bytecode = self._compile_sentence(sentence)
            bytecode.extend(sentence_bytecode)
        
        return bytecode
    
    def _compile_sentence(self, sentence: Dict[str, Any]) -> List[NSCBytecode]:
        """Compile sentence to bytecode."""
        bytecode = []
        
        if sentence['type'] == 'transformation':
            # Compile left phrase
            left_bytecode = self._compile_phrase(sentence['left_phrase'])
            bytecode.extend(left_bytecode)
            
            # Add transformation arrow
            bytecode.append(NSCBytecode(
                opcode=self.OPCODES[NSCGlyph.ARROW],
                comment="transformation"
            ))
            
            # Compile right phrase if present
            if sentence['right_phrase']:
                right_bytecode = self._compile_phrase(sentence['right_phrase'])
                bytecode.extend(right_bytecode)
        
        elif sentence['type'] == 'statement':
            # Compile phrase
            phrase_bytecode = self._compile_phrase(sentence['phrase'])
            bytecode.extend(phrase_bytecode)
        
        return bytecode
    
    def _compile_phrase(self, phrase: List[Dict[str, Any]]) -> List[NSCBytecode]:
        """Compile phrase to bytecode."""
        bytecode = []
        
        for element in phrase:
            if element['type'] == 'atom':
                glyph = NSCGlyph(element['glyph'])
                opcode = self.OPCODES[glyph]
                bytecode.append(NSCBytecode(
                    opcode=opcode,
                    comment=f"glyph {element['glyph']}"
                ))
            
            elif element['type'] == 'group':
                # Compile group content
                group_bytecode = self._compile_phrase(element['content'])
                bytecode.extend(group_bytecode)
        
        return bytecode


class NSCVMState:
    """NSC virtual machine state."""
    
    def __init__(self):
        self.pc = 0  # Program counter
        self.stack: List[Any] = []
        self.environment: Dict[str, Any] = {}
        self.receipt_sink: List[Dict[str, Any]] = []
        self.theta: Optional[np.ndarray] = None
        self.running = True
        self.step_count = 0
    
    def push(self, value: Any) -> None:
        """Push value onto stack."""
        self.stack.append(value)
    
    def pop(self) -> Any:
        """Pop value from stack."""
        if not self.stack:
            raise ValueError("Stack underflow")
        return self.stack.pop()
    
    def peek(self) -> Any:
        """Peek at top of stack."""
        if not self.stack:
            return None
        return self.stack[-1]


class NSCVM:
    """NSC virtual machine for deterministic execution."""
    
    def __init__(self):
        self.state = NSCVMState()
        self.execution_history: List[Dict[str, Any]] = []
    
    def execute(self, bytecode: List[NSCBytecode], max_steps: int = 10000) -> Dict[str, Any]:
        """Execute bytecode with deterministic stepping."""
        self.state = NSCVMState()  # Reset state
        start_time = time.time()
        
        try:
            while self.state.running and self.state.pc < len(bytecode) and self.state.step_count < max_steps:
                instruction = bytecode[self.state.pc]
                self._execute_instruction(instruction)
                self.state.pc += 1
                self.state.step_count += 1
            
            execution_time = time.time() - start_time
            
            result = {
                'success': True,
                'final_state': {
                    'pc': self.state.pc,
                    'stack_size': len(self.state.stack),
                    'environment': self.state.environment.copy(),
                    'step_count': self.state.step_count,
                    'theta': self.state.theta.tolist() if self.state.theta is not None else None
                },
                'execution_time': execution_time,
                'receipts': self.state.receipt_sink.copy()
            }
            
        except Exception as e:
            logger.error(f"VM execution failed: {e}")
            result = {
                'success': False,
                'error': str(e),
                'final_state': {
                    'pc': self.state.pc,
                    'step_count': self.state.step_count
                },
                'execution_time': time.time() - start_time
            }
        
        # Record execution
        self.execution_history.append({
            'timestamp': time.time(),
            'bytecode_length': len(bytecode),
            'result': result
        })
        
        return result
    
    def _execute_instruction(self, instruction: NSCBytecode) -> None:
        """Execute individual instruction."""
        opcode = instruction.opcode
        
        # Generate receipt for this step
        receipt = {
            'step': self.state.step_count,
            'pc': self.state.pc,
            'opcode': opcode,
            'operand': instruction.operand,
            'stack_before': self.state.stack.copy(),
            'environment_before': self.state.environment.copy()
        }
        
        try:
            if opcode == 0x01:  # φ - load θ
                self._execute_load_theta(instruction.operand)
            elif opcode == 0x02:  # ↻ - curvature coupling
                self._execute_curvature_coupling()
            elif opcode == 0x03:  # ⊕ - source +s
                self._execute_source(instruction.operand)
            elif opcode == 0x04:  # ⊖ - sink -s
                self._execute_sink(instruction.operand)
            elif opcode == 0x05:  # ◯ - ∇²θ
                self._execute_laplacian()
            elif opcode == 0x06:  # ∆ - close EOM
                self._execute_close_eom()
            elif opcode == 0x07:  # ⇒ - time marker
                self._execute_time_marker()
            elif opcode == 0x08:  # □ - boundary
                self._execute_boundary(instruction.operand)
            else:
                raise ValueError(f"Unknown opcode: {opcode}")
            
            receipt['success'] = True
            
        except Exception as e:
            receipt['success'] = False
            receipt['error'] = str(e)
            raise
        
        finally:
            receipt['stack_after'] = self.state.stack.copy()
            receipt['environment_after'] = self.state.environment.copy()
            self.state.receipt_sink.append(receipt)
    
    def _execute_load_theta(self, operand: Optional[Any]) -> None:
        """Execute φ - load θ instruction."""
        if operand is not None:
            # Load specified value
            if isinstance(operand, (int, float)):
                self.state.theta = np.array([float(operand)])
            elif isinstance(operand, str):
                # Try to parse as number or load from environment
                if operand in self.state.environment:
                    self.state.theta = self.state.environment[operand]
                else:
                    try:
                        self.state.theta = np.array([float(operand)])
                    except ValueError:
                        self.state.theta = np.array([0.0])  # Default
        else:
            # Load from stack or create default
            if self.state.stack:
                value = self.state.pop()
                self.state.theta = np.array([float(value)])
            else:
                self.state.theta = np.array([0.0])  # Default
        
        self.state.push(self.state.theta)
    
    def _execute_curvature_coupling(self) -> None:
        """Execute ↻ - curvature coupling instruction."""
        if self.state.theta is None:
            raise ValueError("θ not loaded")
        
        # Apply curvature coupling: R·θ
        # For simplicity, use a fixed curvature matrix
        R = np.array([[0.5, -0.3], [0.3, 0.5]])
        
        if len(self.state.theta) == 1:
            # Extend to 2D for matrix multiplication
            theta_extended = np.array([self.state.theta[0], 0.0])
        else:
            theta_extended = self.state.theta[:2]
        
        result = np.dot(R, theta_extended)
        self.state.theta = result
        self.state.push(result)
    
    def _execute_source(self, operand: Optional[Any]) -> None:
        """Execute ⊕ - source +s instruction."""
        source_strength = float(operand) if operand is not None else 1.0
        
        if self.state.theta is None:
            self.state.theta = np.array([source_strength])
        else:
            self.state.theta = self.state.theta + source_strength
        
        self.state.push(self.state.theta)
    
    def _execute_sink(self, operand: Optional[Any]) -> None:
        """Execute ⊖ - sink -s instruction."""
        sink_strength = float(operand) if operand is not None else 1.0
        
        if self.state.theta is None:
            self.state.theta = np.array([-sink_strength])
        else:
            self.state.theta = self.state.theta - sink_strength
        
        self.state.push(self.state.theta)
    
    def _execute_laplacian(self) -> None:
        """Execute ◯ - ∇²θ instruction."""
        if self.state.theta is None:
            raise ValueError("θ not loaded")
        
        # Simplified Laplacian using finite differences
        if len(self.state.theta) > 1:
            laplacian = np.zeros_like(self.state.theta)
            laplacian[1:-1] = self.state.theta[2:] - 2*self.state.theta[1:-1] + self.state.theta[:-2]
            # Boundary conditions
            laplacian[0] = self.state.theta[1] - self.state.theta[0]
            laplacian[-1] = self.state.theta[-2] - self.state.theta[-1]
        else:
            laplacian = np.array([0.0])  # No Laplacian for single point
        
        self.state.theta = laplacian
        self.state.push(laplacian)
    
    def _execute_close_eom(self) -> None:
        """Execute ∆ - close EOM instruction."""
        # This would typically finalize the equation of motion
        # For now, just ensure we have a valid θ
        if self.state.theta is None:
            self.state.theta = np.array([0.0])
        
        # Store result in environment
        self.state.environment['final_theta'] = self.state.theta.copy()
        self.state.push(self.state.theta)
    
    def _execute_time_marker(self) -> None:
        """Execute ⇒ - time marker instruction."""
        # Record current time in environment
        self.state.environment['time_marker'] = time.time()
        self.state.push(time.time())
    
    def _execute_boundary(self, operand: Optional[Any]) -> None:
        """Execute □ - boundary instruction."""
        if self.state.theta is None:
            raise ValueError("θ not loaded")
        
        # Apply boundary conditions
        if operand is not None:
            boundary_value = float(operand)
            self.state.theta[0] = boundary_value
            self.state.theta[-1] = boundary_value
        else:
            # Default boundary conditions (Dirichlet: θ = 0 at boundaries)
            self.state.theta[0] = 0.0
            self.state.theta[-1] = 0.0
        
        self.state.push(self.state.theta)


class NSCProcessor:
    """High-level NSC processor that coordinates packet, compiler, and VM."""
    
    def __init__(self):
        self.compiler = NSCCompiler()
        self.vm = NSCVM()
        self.processing_history: List[Dict[str, Any]] = []
    
    def process(self, content: str, mode: NSCMode = NSCMode.SYMBOLIC, 
                author: str = "HAAI") -> Dict[str, Any]:
        """Process NSC content end-to-end."""
        start_time = time.time()
        
        try:
            # Create packet
            packet = NSCPacket(content, mode, author)
            
            # Compile to bytecode
            bytecode = self.compiler.compile(packet)
            
            # Execute in VM
            execution_result = self.vm.execute(bytecode)
            
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'packet': packet.to_dict(),
                'bytecode_length': len(bytecode),
                'execution_result': execution_result,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"NSC processing failed: {e}")
            result = {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
        
        # Record processing
        self.processing_history.append({
            'timestamp': time.time(),
            'content': content,
            'mode': mode.value,
            'result': result
        })
        
        return result
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of processing history."""
        if not self.processing_history:
            return {"status": "no_history"}
        
        successful = sum(1 for h in self.processing_history if h['result']['success'])
        total = len(self.processing_history)
        
        return {
            'total_processed': total,
            'successful': successful,
            'success_rate': successful / total if total > 0 else 0.0,
            'compilation_history_size': len(self.compiler.compilation_history),
            'execution_history_size': len(self.vm.execution_history)
        }
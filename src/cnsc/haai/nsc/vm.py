"""
NSC Bytecode VM

Stack-based bytecode virtual machine for NSC execution.

This module provides:
- VMStack: Operand stack implementation
- VMFrame: Stack frame for function calls
- VMState: VM execution state
- BytecodeEmitter: Generate bytecode from IR
- VM: Stack-based virtual machine with trace hooks
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from uuid import uuid4
from datetime import datetime

from cnsc.haai.nsc.ir import (
    NSCProgram,
    NSCFunction,
    NSCBlock,
    NSCInstruction,
    NSCOpcode,
    NSCType,
    NSCValue,
)


@dataclass
class VMStack:
    """
    VM Operand Stack.
    
    Stack implementation for VM operand management.
    """
    stack: List[Any] = field(default_factory=list)
    max_size: int = 1024
    
    def push(self, value: Any) -> bool:
        """Push value onto stack."""
        if len(self.stack) >= self.max_size:
            return False
        self.stack.append(value)
        return True
    
    def pop(self) -> Optional[Any]:
        """Pop value from stack."""
        if not self.stack:
            return None
        return self.stack.pop()
    
    def peek(self, offset: int = 0) -> Optional[Any]:
        """Peek at stack value without popping."""
        index = len(self.stack) - 1 - offset
        if 0 <= index < len(self.stack):
            return self.stack[index]
        return None
    
    def dup(self) -> bool:
        """Duplicate top value."""
        if not self.stack:
            return False
        return self.push(self.stack[-1])
    
    def swap(self) -> bool:
        """Swap top two values."""
        if len(self.stack) < 2:
            return False
        self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]
        return True
    
    def clear(self) -> None:
        """Clear the stack."""
        self.stack.clear()
    
    def size(self) -> int:
        """Get stack size."""
        return len(self.stack)
    
    def is_empty(self) -> bool:
        """Check if stack is empty."""
        return len(self.stack) == 0
    
    def to_list(self) -> List[Any]:
        """Get stack as list."""
        return self.stack.copy()


@dataclass
class VMFrame:
    """
    VM Stack Frame.
    
    Function call frame with local variables and return address.
    """
    function_id: str
    function_name: str
    return_address: Optional[int] = None
    return_value: Any = None
    
    # Local storage
    locals: Dict[str, Any] = field(default_factory=dict)
    local_types: Dict[str, Optional[NSCType]] = field(default_factory=dict)
    
    # Stack
    stack: VMStack = field(default_factory=VMStack)
    
    # Block context
    current_block_id: Optional[str] = None
    instruction_pointer: int = 0
    
    def load(self, name: str) -> Optional[Any]:
        """Load local variable."""
        return self.locals.get(name)
    
    def store(self, name: str, value: Any, value_type: Optional[NSCType] = None) -> None:
        """Store local variable."""
        self.locals[name] = value
        if value_type:
            self.local_types[name] = value_type
    
    def alloc(self, name: str, value_type: NSCType) -> None:
        """Allocate local variable."""
        self.locals[name] = None
        self.local_types[name] = value_type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "function_id": self.function_id,
            "function_name": self.function_name,
            "return_address": self.return_address,
            "return_value": self.return_value,
            "local_count": len(self.locals),
            "stack_size": self.stack.size(),
        }


@dataclass
class VMState:
    """
    VM Execution State.
    
    Complete state of VM execution.
    """
    # Program and function
    program: NSCProgram
    current_function: Optional[NSCFunction] = None
    current_block: Optional[NSCBlock] = None
    
    # Call stack
    call_stack: List[VMFrame] = field(default_factory=list)
    
    # Program counter
    instruction_pointer: int = 0
    program_counter: int = 0
    
    # State
    is_running: bool = False
    is_halted: bool = False
    halt_reason: Optional[str] = None
    
    # Coherence
    coherence_level: float = 1.0
    coherence_check_enabled: bool = True
    
    # Trace hooks
    on_instruction: Optional[Callable] = None
    on_trace: Optional[Callable] = None
    on_gate: Optional[Callable] = None
    on_receipt: Optional[Callable] = None
    
    # Metrics
    instruction_count: int = 0
    cycle_count: int = 0
    start_time: Optional[datetime] = None
    
    def push_frame(self, frame: VMFrame) -> None:
        """Push frame onto call stack."""
        self.call_stack.append(frame)
    
    def pop_frame(self) -> Optional[VMFrame]:
        """Pop frame from call stack."""
        if self.call_stack:
            return self.call_stack.pop()
        return None
    
    def get_current_frame(self) -> Optional[VMFrame]:
        """Get current frame."""
        if self.call_stack:
            return self.call_stack[-1]
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "instruction_count": self.instruction_count,
            "cycle_count": self.cycle_count,
            "call_stack_depth": len(self.call_stack),
            "is_running": self.is_running,
            "is_halted": self.is_halted,
            "coherence_level": self.coherence_level,
        }


class BytecodeEmitter:
    """
    Bytecode Emitter.
    
    Generates bytecode from NSC IR instructions.
    """
    
    def __init__(self, program: NSCProgram):
        self.program = program
        self.bytecode: List[int] = []
        self.labels: Dict[str, int] = {}
    
    def emit(self, opcode: NSCOpcode, *operands: Any) -> int:
        """Emit instruction to bytecode."""
        pos = len(self.bytecode)
        self.bytecode.append(opcode.value)
        for operand in operands:
            if isinstance(operand, bool):
                self.bytecode.append(1 if operand else 0)
            elif isinstance(operand, int):
                self.emit_int(operand)
            elif isinstance(operand, float):
                self.emit_float(operand)
            elif isinstance(operand, str):
                self.emit_string(operand)
            elif isinstance(operand, NSCType):
                self.emit_string(operand.type_id)
            else:
                self.emit_string(str(operand))
        return pos
    
    def emit_int(self, value: int) -> None:
        """Emit integer constant."""
        self.bytecode.extend([0x10])  # INT marker
        self.bytecode.extend(value.to_bytes(8, 'big', signed=True))
    
    def emit_float(self, value: float) -> None:
        """Emit float constant."""
        self.bytecode.extend([0x11])  # FLOAT marker
        self.bytecode.extend(bytearray(value.to_bytes(8, 'big')))
    
    def emit_string(self, value: str) -> None:
        """Emit string constant."""
        self.bytecode.extend([0x12])  # STRING marker
        encoded = value.encode('utf-8')
        self.bytecode.extend(len(encoded).to_bytes(4, 'big'))
        self.bytecode.extend(encoded)
    
    def emit_label(self, name: str) -> int:
        """Emit label and return its position."""
        pos = len(self.bytecode)
        self.labels[name] = pos
        return pos
    
    def resolve_labels(self) -> None:
        """Resolve label references in bytecode."""
        # Label resolution is done at runtime via jump table
        pass
    
    def get_bytecode(self) -> bytes:
        """Get final bytecode."""
        return bytes(self.bytecode)
    
    def get_bytecode_list(self) -> List[int]:
        """Get bytecode as list of integers."""
        return self.bytecode.copy()
    
    def emit_function(self, func: NSCFunction) -> bytes:
        """Emit function bytecode."""
        emitter = BytecodeEmitter(self.program)
        
        for block_id, block in func.blocks.items():
            for instruction in block.instructions:
                emitter.emit_instruction(instruction)
        
        return bytes(emitter.bytecode)
    
    def emit_instruction(self, instruction: NSCInstruction) -> int:
        """Emit single instruction."""
        return self.emit(instruction.opcode, *instruction.operands)


class VM:
    """
    NSC Virtual Machine.
    
    Stack-based bytecode interpreter with trace hooks and receipt emission.
    """
    
    def __init__(self, program: NSCProgram):
        self.program = program
        self.state = VMState(program=program)
        self.bytecode: bytes = b''
        self.pc_to_block: Dict[int, Tuple[str, int]] = {}
    
    def load(self) -> bool:
        """Load program bytecode."""
        emitter = BytecodeEmitter(self.program)
        
        for func_id, func in self.program.functions.items():
            for block_id, block in func.blocks.items():
                for instruction in block.instructions:
                    pos = emitter.emit_instruction(instruction)
                    self.pc_to_block[pos] = (block_id, pos)
        
        self.bytecode = bytes(emitter.bytecode)
        return True
    
    def run(
        self,
        function_id: Optional[str] = None,
        args: Optional[List[Any]] = None,
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute program.
        
        Returns:
            Tuple of (success, result, error_message)
        """
        func_id = function_id or self.program.entry_function
        if not func_id:
            return False, None, "No entry function specified"
        
        func = self.program.get_function(func_id)
        if not func:
            return False, None, f"Function {func_id} not found"
        
        # Initialize state
        self.state.is_running = True
        self.state.is_halted = False
        self.state.start_time = datetime.utcnow()
        self.state.instruction_count = 0
        self.state.cycle_count = 0
        
        # Create initial frame
        frame = VMFrame(
            function_id=func_id,
            function_name=func.name,
        )
        
        # Store arguments
        if args:
            for i, arg in enumerate(args):
                if i < len(func.param_types):
                    param_name = f"arg_{i}"
                    frame.store(param_name, arg, func.param_types[i])
        
        self.state.push_frame(frame)
        
        # Execute
        try:
            result = self._execute(func)
            self.state.is_running = False
            self.state.is_halted = True
            return True, result, None
        except Exception as e:
            self.state.is_running = False
            self.state.is_halted = True
            return False, None, str(e)
    
    def _execute(self, func: NSCFunction) -> Any:
        """Execute function."""
        frame = self.state.get_current_frame()
        if not frame:
            return None
        
        # Set entry block
        if func.entry_block:
            frame.current_block_id = func.entry_block
            block = func.blocks.get(func.entry_block)
            if block:
                self.state.current_block = block
        
        # Main execution loop
        while self.state.is_running and not self.state.is_halted:
            frame = self.state.get_current_frame()
            if not frame:
                break
            
            # Get current instruction
            if not self._execute_instruction():
                break
            
            self.state.instruction_count += 1
            self.state.cycle_count += 1
        
        # Return value
        return frame.return_value
    
    def _execute_instruction(self) -> bool:
        """Execute single instruction."""
        frame = self.state.get_current_frame()
        if not frame:
            return False
        
        # Get instruction at PC
        if self.state.program_counter >= len(self.bytecode):
            self.state.is_halted = True
            return False
        
        opcode_value = self.bytecode[self.state.program_counter]
        opcode = NSCOpcode(opcode_value)
        self.state.program_counter += 1
        
        # Decode operands
        operands = self._decode_operands()
        
        # Execute
        return self._dispatch(opcode, operands, frame)
    
    def _decode_operands(self) -> List[Any]:
        """Decode operands from bytecode."""
        operands = []
        while self.state.program_counter < len(self.bytecode):
            marker = self.bytecode[self.state.program_counter]
            self.state.program_counter += 1
            
            if marker == 0x10:  # INT
                value = int.from_bytes(
                    self.bytecode[self.state.program_counter:self.state.program_counter + 8],
                    'big', signed=True
                )
                self.state.program_counter += 8
                operands.append(value)
            elif marker == 0x11:  # FLOAT
                value = float.from_bytes(
                    self.bytecode[self.state.program_counter:self.state.program_counter + 8],
                    'big'
                )
                self.state.program_counter += 8
                operands.append(value)
            elif marker == 0x12:  # STRING
                length = int.from_bytes(
                    self.bytecode[self.state.program_counter:self.state.program_counter + 4],
                    'big'
                )
                self.state.program_counter += 4
                value = self.bytecode[self.state.program_counter:self.state.program_counter + length].decode('utf-8')
                self.state.program_counter += length
                operands.append(value)
            else:
                # Not an operand, backtrack
                self.state.program_counter -= 1
                break
        
        return operands
    
    def _dispatch(
        self,
        opcode: NSCOpcode,
        operands: List[Any],
        frame: VMFrame,
    ) -> bool:
        """Dispatch and execute opcode."""
        
        # Call instruction hook
        if self.state.on_instruction:
            self.state.on_instruction(opcode, operands, frame)
        
        # Stack operations
        if opcode == NSCOpcode.PUSH:
            frame.stack.push(operands[0] if operands else None)
        
        elif opcode == NSCOpcode.POP:
            frame.stack.pop()
        
        elif opcode == NSCOpcode.DUP:
            frame.stack.dup()
        
        elif opcode == NSCOpcode.SWAP:
            frame.stack.swap()
        
        # Local operations
        elif opcode == NSCOpcode.LOAD:
            name = operands[0] if operands else None
            value = frame.load(name)
            if value is not None:
                frame.stack.push(value)
        
        elif opcode == NSCOpcode.STORE:
            name = operands[0] if operands else None
            value = frame.stack.pop()
            frame.store(name, value)
        
        elif opcode == NSCOpcode.ALLOC:
            name = operands[0] if operands else None
            value_type = self._get_type(operands[1] if len(operands) > 1 else None)
            frame.alloc(name, value_type)
        
        # Arithmetic
        elif opcode == NSCOpcode.ADD:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.push(a + b)
        
        elif opcode == NSCOpcode.SUB:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.push(a - b)
        
        elif opcode == NSCOpcode.MUL:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.push(a * b)
        
        elif opcode == NSCOpcode.DIV:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.push(a / b)
        
        elif opcode == NSCOpcode.NEG:
            a = frame.stack.pop()
            frame.stack.push(-a)
        
        # Comparison
        elif opcode == NSCOpcode.EQ:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.push(a == b)
        
        elif opcode == NSCOpcode.NE:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.push(a != b)
        
        elif opcode == NSCOpcode.LT:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.push(a < b)
        
        elif opcode == NSCOpcode.GT:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.push(a > b)
        
        # Logical
        elif opcode == NSCOpcode.AND:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.push(a and b)
        
        elif opcode == NSCOpcode.OR:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.push(a or b)
        
        elif opcode == NSCOpcode.NOT:
            a = frame.stack.pop()
            frame.stack.push(not a)
        
        # Control flow
        elif opcode == NSCOpcode.JUMP:
            target = operands[0] if operands else 0
            self.state.program_counter = target
        
        elif opcode == NSCOpcode.JUMP_IF:
            condition = frame.stack.pop()
            target = operands[0] if operands else 0
            if condition:
                self.state.program_counter = target
        
        elif opcode == NSCOpcode.JUMP_IF_NOT:
            condition = frame.stack.pop()
            target = operands[0] if operands else 0
            if not condition:
                self.state.program_counter = target
        
        elif opcode == NSCOpcode.RET:
            frame.return_value = frame.stack.pop()
            return False  # Exit frame
        
        elif opcode == NSCOpcode.CALL:
            func_name = operands[0] if operands else None
            func = self.program.get_function(func_name)
            if func:
                # Push new frame
                new_frame = VMFrame(
                    function_id=func.function_id,
                    function_name=func.name,
                    return_address=self.state.program_counter,
                )
                self.state.push_frame(new_frame)
        
        # Coherence operations
        elif opcode == NSCOpcode.COHERENCE_READ:
            self.state.coherence_level = frame.stack.pop()
        
        elif opcode == NSCOpcode.COHERENCE_WRITE:
            value = frame.stack.pop()
            frame.stack.push(self.state.coherence_level)
        
        elif opcode == NSCOpcode.COHERENCE_CHECK:
            required = operands[0] if operands else 0.5
            if self.state.coherence_level < required:
                raise RuntimeError(f"Coherence check failed: {self.state.coherence_level} < {required}")
        
        # Gate operations
        elif opcode == NSCOpcode.GATE_EVAL:
            gate_name = operands[0] if operands else None
            result = self._evaluate_gate(gate_name)
            frame.stack.push(result)
        
        # Trace operations
        elif opcode == NSCOpcode.TRACE_EVENT:
            event_type = operands[0] if operands else "generic"
            if self.state.on_trace:
                self.state.on_trace(event_type, frame.stack.pop())
        
        elif opcode == NSCOpcode.EMIT_RECEIPT:
            if self.state.on_receipt:
                receipt = self.state.on_receipt()
                frame.stack.push(receipt)
        
        # Special
        elif opcode == NSCOpcode.HALT:
            self.state.is_halted = True
            self.state.halt_reason = operands[0] if operands else "normal"
        
        elif opcode == NSCOpcode.NOP:
            pass
        
        return True
    
    def _get_type(self, type_id: Optional[str]) -> Optional[NSCType]:
        """Get type by ID."""
        if not type_id:
            return None
        return self.program.types.get(type_id)
    
    def _evaluate_gate(self, gate_name: str) -> bool:
        """Evaluate gate."""
        if self.state.on_gate:
            return self.state.on_gate(gate_name)
        return True
    
    def step(self) -> bool:
        """Execute single instruction."""
        if self.state.is_halted:
            return False
        
        frame = self.state.get_current_frame()
        if not frame:
            return False
        
        return self._execute_instruction()
    
    def reset(self) -> None:
        """Reset VM state."""
        self.state = VMState(program=self.program)
        self.state.program_counter = 0
    
    def get_state(self) -> Dict[str, Any]:
        """Get current VM state."""
        frame = self.state.get_current_frame()
        return {
            "program_counter": self.state.program_counter,
            "instruction_count": self.state.instruction_count,
            "coherence_level": self.state.coherence_level,
            "is_running": self.state.is_running,
            "is_halted": self.state.is_halted,
            "current_function": frame.function_name if frame else None,
            "stack_size": frame.stack.size() if frame else 0,
        }


def create_vm(program: NSCProgram) -> VM:
    """Create new VM instance."""
    vm = VM(program)
    vm.load()
    return vm

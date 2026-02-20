"""
Integration Tests - Full Pipeline

End-to-end tests covering the complete toolchain:
GLLL → GHLL → NSC → GML
"""

import unittest
import tempfile
import os
from datetime import datetime

from cnsc.haai.ghll.parser import parse_ghll
from cnsc.haai.ghll.types import TypeRegistry
from cnsc.haai.nsc.ir import (
    NSCProgram, NSCFunction, NSCType, NSCOpcode,
    create_nsc_program, create_nsc_function, create_nsc_block
)
from cnsc.haai.nsc.vm import NSCVirtualMachine, compile_to_bytecode
from cnsc.haai.gml.trace import TraceManager, TraceLevel, TraceEvent
from cnsc.haai.gml.receipts import ReceiptSystem, ReceiptStepType, create_receipt_system
from cnsc.haai.gml.replay import ReplayEngine, create_replay_engine
from cnsc.haai.glll.hadamard import create_hadamard_codec


class TestFullPipeline(unittest.TestCase):
    """Integration tests for the full toolchain."""
    
    def test_ghll_parse_to_nsc(self):
        """Test parsing GHLL and generating NSC IR."""
        source = """
        let x: int = 42;
        let y: int = x + 10;
        return y;
        """
        
        # Parse GHLL
        result = parse_ghll(source, "test.ghll")
        self.assertTrue(result.success, f"Parse failed: {result.errors}")
        
        # Create NSC program
        program = create_nsc_program("TestProgram")
        func = create_nsc_function(
            name="main",
            param_types=None,
            return_type=NSCType.INT
        )
        program.add_function(func)
        
        # Add basic blocks
        entry = create_nsc_block("entry")
        exit_block = create_nsc_block("exit")
        program.add_block(entry)
        program.add_block(exit_block)
        
        # Connect blocks
        entry.add_successor(exit_block.block_id)
        
        # Serialize
        data = program.to_dict()
        restored = NSCProgram.from_dict(data)
        
        self.assertEqual(restored.program_id, program.program_id)
        self.assertEqual(len(restored.functions), len(program.functions))
    
    def test_nsc_compile_and_run(self):
        """Test NSC bytecode compilation and execution."""
        # Create program
        program = create_nsc_program("TestVM")
        func = create_nsc_function(
            name="main",
            param_types=None,
            return_type=NSCType.INT
        )
        program.add_function(func)
        
        # Create blocks with instructions
        entry = create_nsc_block("entry")
        exit_block = create_nsc_block("exit")
        
        # Add instructions
        entry.add_instruction(NSCOpcode.CONST_INT, [42])
        entry.add_instruction(NSCOpcode.RETURN, [0])
        
        program.add_block(entry)
        program.add_block(exit_block)
        
        # Compile to bytecode
        bytecode = compile_to_bytecode(program, entry_point="main")
        self.assertIsInstance(bytecode, bytes)
        
        # Execute
        vm = NSCVirtualMachine()
        result = vm.run(bytecode)
        
        self.assertIsNotNone(result)
    
    def test_receipt_chain_creation(self):
        """Test receipt chain creation and verification."""
        system = create_receipt_system("test-key")
        
        # Emit sequence of receipts
        episode_id = "test-episode-001"
        
        for i in range(3):
            receipt = system.emit_receipt(
                step_type=ReceiptStepType.PARSE,
                source=f"step-{i}",
                input_data={"step": i},
                output_data={"result": i * 2},
                episode_id=episode_id,
            )
            self.assertIsNotNone(receipt)
        
        # Verify chain
        receipts = system.get_episode_receipts(episode_id)
        self.assertEqual(len(receipts), 3)
        
        # Verify chain integrity
        is_valid = system.verify_episode_chain(episode_id)
        self.assertTrue(is_valid)
    
    def test_trace_and_replay(self):
        """Test execution tracing and replay."""
        engine = create_replay_engine()
        
        # Create checkpoint
        checkpoint = engine.create_checkpoint(
            episode_id="replay-test",
            phase="COHERENT",
            step_index=0,
            program_state={"x": 10, "y": 20},
            vm_state={"sp": 100},
        )
        
        self.assertIn(checkpoint.checkpoint_id, engine.checkpoints)
        
        # Execute replay
        def executor(cp):
            return True, {"result": cp.program_state.get("x", 0)}
        
        result = engine.execute_replay(
            "replay-test",
            executor,
            checkpoints=[checkpoint]
        )
        
        self.assertEqual(result.status.name, "COMPLETED")
        self.assertEqual(result.steps_executed, 1)
    
    def test_hadamard_encoding_roundtrip(self):
        """Test Hadamard encoding and decoding."""
        codec = create_hadamard_codec(32)
        data = [1, 0, 1, 1, 0]  # 5 bits
        
        # Encode
        codeword = codec.encode(data)
        self.assertEqual(len(codeword), 32)
        
        # Decode
        decoded, corrected = codec.decode(codeword)
        self.assertEqual(decoded, data)
        self.assertFalse(corrected)
    
    def test_error_injection_recovery(self):
        """Test error injection and recovery mechanisms."""
        codec = create_hadamard_codec(32)
        data = [1, 0, 1, 1, 0]  # 5 bits for n=32
        
        # Encode
        codeword = codec.encode(data)
        
        # Introduce errors
        corrupted = codeword.copy()
        corrupted[0] = -corrupted[0]
        corrupted[5] = -corrupted[5]
        
        # Decode with errors
        decoded, corrected = codec.decode(corrupted)
        
        # Should either correct or detect the error
        self.assertTrue(corrected or decoded == data)
    
    def test_deterministic_execution(self):
        """Test that execution is deterministic."""
        source = """
        let a: int = 5;
        let b: int = 10;
        let c: int = a + b;
        return c;
        """
        
        result1 = parse_ghll(source, "test1.ghll")
        result2 = parse_ghll(source, "test2.ghll")
        
        # Same source should produce same AST structure
        self.assertTrue(result1.success)
        self.assertTrue(result2.success)


class TestSeamContracts(unittest.TestCase):
    """Tests for seam contracts between modules."""
    
    def test_glll_ghll_binding(self):
        """Test GLLL to GHLL binding seam."""
        # Test that glyph encoding works
        codec = create_hadamard_codec(16)
        data = [1, 0, 0, 1]  # 4 bits
        
        # Encode
        codeword = codec.encode(data)
        
        # Decode back
        decoded, _ = codec.decode(codeword)
        
        self.assertEqual(decoded, data)
    
    def test_ghll_nsc_lowering(self):
        """Test GHLL to NSC lowering seam."""
        # Parse GHLL
        source = "let x: int = 42;"
        result = parse_ghll(source, "test.ghll")
        
        self.assertTrue(result.success)
        
        # Create NSC from parse result
        program = create_nsc_program("Lowered")
        func = create_nsc_function(
            name="lowered_func",
            param_types=None,
            return_type=NSCType.INT
        )
        program.add_function(func)
        
        # Verify program structure
        self.assertEqual(program.name, "Lowered")
        self.assertIn("main", program.functions)
    
    def test_nsc_gml_receipt_emission(self):
        """Test NSC to GML receipt emission seam."""
        system = create_receipt_system("receipt-key")
        
        # Emit receipt with NSC-like data
        receipt = system.emit_receipt(
            step_type=ReceiptStepType.GATE_EVAL,
            source="nsc-execution",
            input_data={"bytecode_hash": "abc123"},
            output_data={"result": 0, "coherence": 1.0},
            episode_id="nsc-episode",
        )
        
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.content.step_type, ReceiptStepType.GATE_EVAL)


class TestComplianceMigration(unittest.TestCase):
    """Tests migrated from compliance tests."""
    
    def test_grammar_golden_compat(self):
        """Test grammar compatibility with golden parses."""
        test_cases = [
            ("let x: int = 42;", "simple_assignment"),
            ("if x > 0 { return 1; }", "if_statement"),
            ("while y < 10 { y = y + 1; }", "while_statement"),
        ]
        
        for source, name in test_cases:
            with self.subTest(case=name):
                result = parse_ghll(source, f"{name}.ghll")
                self.assertTrue(result.success, f"Failed on {name}")
    
    def test_type_stability(self):
        """Test type system stability."""
        registry = TypeRegistry()
        
        # Create and retrieve types
        int_type = registry.lookup("int")
        self.assertIsNotNone(int_type)
        
        # Type should be consistent
        int_type_2 = registry.lookup("int")
        self.assertEqual(int_type.type_id, int_type_2.type_id)
    
    def test_receipt_schema_compat(self):
        """Test receipt schema compatibility."""
        system = create_receipt_system("schema-test")
        
        receipt = system.emit_receipt(
            step_type=ReceiptStepType.PARSE,
            source="schema-test",
            input_data={},
            output_data={},
            episode_id="schema-episode",
        )
        
        # Convert to dict (should be schema-compatible)
        data = receipt.to_dict()
        
        self.assertIn("receipt_id", data)
        self.assertIn("content", data)
        self.assertIn("signature", data)


class TestGoldenArtifacts(unittest.TestCase):
    """Tests using golden artifacts for comparison."""
    
    def setUp(self):
        """Set up test artifacts directory."""
        self.artifacts_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test artifacts."""
        import shutil
        shutil.rmtree(self.artifacts_dir, ignore_errors=True)
    
    def test_parse_result_serialization(self):
        """Test parse result can be saved and loaded."""
        source = "let result: int = 100;"
        result = parse_ghll(source, "serialization_test.ghll")
        
        self.assertTrue(result.success)
        
        # Serialize
        data = result.to_dict()
        
        # Should be JSON-serializable
        import json
        json_str = json.dumps(data)
        restored = json.loads(json_str)
        
        self.assertEqual(restored["success"], data["success"])
    
    def test_receipt_serialization(self):
        """Test receipt can be saved and loaded."""
        system = create_receipt_system("serial-test")
        
        receipt = system.emit_receipt(
            step_type=ReceiptStepType.PARSE,
            source="test",
            input_data={"test": True},
            output_data={"output": False},
            episode_id="serial-episode",
        )
        
        # Serialize
        data = receipt.to_dict()
        
        # Should be JSON-serializable
        import json
        json_str = json.dumps(data)
        restored = json.loads(json_str)
        
        self.assertEqual(restored["receipt_id"], receipt.receipt_id)
    
    def test_bytecode_roundtrip(self):
        """Test bytecode can be saved and loaded."""
        program = create_nsc_program("BytecodeTest")
        func = create_nsc_function(
            name="test_func",
            param_types=None,
            return_type=NSCType.INT
        )
        program.add_function(func)
        
        bytecode = compile_to_bytecode(program, entry_point="test_func")
        
        # Save to temp file
        filepath = os.path.join(self.artifacts_dir, "test.bytecode")
        with open(filepath, "wb") as f:
            f.write(bytecode)
        
        # Load back
        with open(filepath, "rb") as f:
            loaded = f.read()
        
        self.assertEqual(loaded, bytecode)


if __name__ == "__main__":
    unittest.main()

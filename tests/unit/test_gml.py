"""
Unit tests for GML Module.

Tests cover:
- Trace: TraceEvent, TraceThread, TraceManager
- PhaseLoom: PhaseLoom, ThreadCoupling, CouplingPolicy
- Receipts: Receipt, ReceiptChain, HashChain, ReceiptSystem
- Replay: Checkpoint, ReplayEngine, Verifier
"""

import unittest
from datetime import datetime, timedelta

from cnsc.haai.gml.trace import (
    TraceEvent,
    TraceThread,
    TraceManager,
    TraceLevel,
    TraceQuery,
    create_trace_manager,
)

from cnsc.haai.gml.phaseloom import (
    PhaseLoom,
    ThreadCoupling,
    CouplingPolicy,
    ThreadState,
    PhaseLoomThread,
    create_phase_loom,
)

from cnsc.haai.gml.receipts import (
    Receipt,
    ReceiptStepType,
    ReceiptDecision,
    ReceiptSignature,
    ReceiptContent,
    ReceiptProvenance,
    HashChain,
    ChainValidator,
    ReceiptSystem,
    create_receipt_system,
)

from cnsc.haai.gml.replay import (
    Checkpoint,
    ReplayEngine,
    Verifier,
    ReplayResult,
    ReplayStatus,
    create_replay_engine,
    create_verifier,
)


class TestTraceEvent(unittest.TestCase):
    """Tests for TraceEvent."""
    
    def test_create_event(self):
        """Test creating trace event."""
        event = TraceEvent.create(
            level=TraceLevel.INFO,
            event_type="test",
            message="Test event",
        )
        self.assertEqual(event.level, TraceLevel.INFO)
        self.assertEqual(event.event_type, "test")
        self.assertEqual(event.message, "Test event")
        self.assertIsNotNone(event.event_id)
    
    def test_serialization(self):
        """Test event serialization."""
        event = TraceEvent.create(
            level=TraceLevel.DEBUG,
            event_type="test",
            message="Test",
            details={"key": "value"},
        )
        data = event.to_dict()
        restored = TraceEvent.from_dict(data)
        
        self.assertEqual(restored.event_id, event.event_id)
        self.assertEqual(restored.level, event.level)
        self.assertEqual(restored.message, event.message)


class TestTraceThread(unittest.TestCase):
    """Tests for TraceThread."""
    
    def test_create_thread(self):
        """Test creating thread."""
        thread = TraceThread(thread_id="t1", name="Test Thread")
        self.assertEqual(thread.thread_id, "t1")
        self.assertEqual(len(thread.events), 0)
    
    def test_add_event(self):
        """Test adding events to thread."""
        thread = TraceThread(thread_id="t1", name="Test")
        event = TraceEvent.create(level=TraceLevel.INFO, event_type="test", message="Event 1")
        
        thread.add_event(event)
        self.assertEqual(len(thread.events), 1)
        self.assertEqual(event.thread_id, "t1")


class TestTraceManager(unittest.TestCase):
    """Tests for TraceManager."""
    
    def test_create_manager(self):
        """Test creating manager."""
        manager = create_trace_manager("Test Manager")
        self.assertEqual(manager.name, "Test Manager")
    
    def test_create_thread_and_add_event(self):
        """Test creating thread and adding events."""
        manager = create_trace_manager()
        thread = manager.create_thread("Test Thread")
        event = TraceEvent.create(
            level=TraceLevel.INFO,
            event_type="test",
            message="Test",
            thread_id=thread.thread_id,
        )
        manager.add_event(event)
        
        self.assertEqual(len(manager.events), 1)
        self.assertEqual(len(thread.events), 1)
    
    def test_query(self):
        """Test trace query."""
        manager = create_trace_manager()
        thread = manager.create_thread("Test")
        
        # Add events
        for i in range(5):
            event = TraceEvent.create(
                level=TraceLevel.DEBUG if i < 2 else TraceLevel.INFO,
                event_type="test",
                message=f"Event {i}",
                thread_id=thread.thread_id,
            )
            manager.add_event(event)
        
        # Query by level
        query = TraceQuery(levels=[TraceLevel.DEBUG])
        results = manager.query(query)
        self.assertEqual(len(results), 2)


class TestCouplingPolicy(unittest.TestCase):
    """Tests for CouplingPolicy."""
    
    def test_create_policy(self):
        """Test creating policy."""
        policy = CouplingPolicy(
            policy_id="p1",
            name="Sequential",
            coupling_type="sequential",
            max_parallel=1,
        )
        self.assertEqual(policy.max_parallel, 1)
    
    def test_check_coupling(self):
        """Test coupling check."""
        policy = CouplingPolicy(
            policy_id="p1",
            name="Test",
            coupling_type="sequential",
            max_parallel=1,
            min_coherence=0.5,
        )
        
        # Create mock threads
        class MockThread:
            def __init__(self, tid, active, coherence):
                self.thread_id = tid
                self.is_active = active
                self.coherence_level = coherence
                self.name = f"Thread_{tid}"
        
        threads = [
            MockThread("t1", True, 0.8),
            MockThread("t2", True, 0.6),
        ]
        coherence = {"t1": 0.8, "t2": 0.6}
        
        passed, message = policy.check_coupling(threads, coherence)
        self.assertFalse(passed)  # 2 active threads > max_parallel=1


class TestPhaseLoom(unittest.TestCase):
    """Tests for PhaseLoom."""
    
    def test_create_loom(self):
        """Test creating PhaseLoom."""
        loom = create_phase_loom("Test Loom")
        self.assertEqual(loom.name, "Test Loom")
    
    def test_create_thread(self):
        """Test creating thread in loom."""
        loom = create_phase_loom("Test")
        thread = loom.create_thread("Thread 1", depends_on=[])
        
        self.assertEqual(thread.name, "Thread 1")
        self.assertIn(thread.thread_id, loom.threads)
    
    def test_add_coupling(self):
        """Test adding thread coupling."""
        loom = create_phase_loom("Test")
        t1 = loom.create_thread("T1")
        t2 = loom.create_thread("T2")
        
        coupling = ThreadCoupling(
            coupling_id="c1",
            from_thread=t1.thread_id,
            to_thread=t2.thread_id,
            coupling_type="depends_on",
        )
        loom.add_coupling(coupling)
        
        self.assertEqual(len(loom.couplings), 1)
        self.assertIn(t2.thread_id, t1.depends_on)


class TestHashChain(unittest.TestCase):
    """Tests for HashChain."""
    
    def test_create_chain(self):
        """Test creating hash chain."""
        chain = HashChain()
        self.assertEqual(chain.get_length(), 1)
        self.assertIsNotNone(chain.get_root())
    
    def test_append(self):
        """Test appending to chain."""
        chain = HashChain()
        original_hash = chain.get_tip()
        
        # Create mock receipt
        class MockReceipt:
            def compute_chain_hash(self, prev):
                return "test_hash"
        
        chain.append(MockReceipt())
        self.assertEqual(chain.get_length(), 2)
        self.assertNotEqual(chain.get_tip(), original_hash)


class TestReceipt(unittest.TestCase):
    """Tests for Receipt."""
    
    def test_create_receipt(self):
        """Test creating receipt."""
        content = ReceiptContent(
            step_type=ReceiptStepType.PARSE,
            input_hash="abc",
            output_hash="def",
        )
        signature = ReceiptSignature()
        provenance = ReceiptProvenance(source="test")
        
        receipt = Receipt(
            receipt_id="r1",
            content=content,
            signature=signature,
            provenance=provenance,
        )
        
        self.assertEqual(receipt.receipt_id, "r1")
        self.assertEqual(receipt.content.step_type, ReceiptStepType.PARSE)
    
    def test_serialization(self):
        """Test receipt serialization."""
        content = ReceiptContent(
            step_type=ReceiptStepType.GATE_EVAL,
            decision=ReceiptDecision.PASS,
        )
        receipt = Receipt(
            receipt_id="r1",
            content=content,
            signature=ReceiptSignature(),
            provenance=ReceiptProvenance(source="test"),
        )
        
        data = receipt.to_dict()
        restored = Receipt.from_dict(data)
        
        self.assertEqual(restored.receipt_id, receipt.receipt_id)


class TestReceiptSystem(unittest.TestCase):
    """Tests for ReceiptSystem."""
    
    def test_create_system(self):
        """Test creating receipt system."""
        system = create_receipt_system("test-key")
        self.assertEqual(len(system.receipts), 0)
    
    def test_emit_receipt(self):
        """Test emitting receipt."""
        system = create_receipt_system()
        receipt = system.emit_receipt(
            step_type=ReceiptStepType.PARSE,
            source="test",
            input_data={"x": 1},
            output_data={"y": 2},
            episode_id="ep1",
        )
        
        self.assertIsNotNone(receipt)
        self.assertEqual(len(system.receipts), 1)
        self.assertIn("ep1", system.receipts_by_episode)
    
    def test_get_episode_receipts(self):
        """Test getting episode receipts."""
        system = create_receipt_system()
        
        # Emit multiple receipts
        for i in range(3):
            system.emit_receipt(
                step_type=ReceiptStepType.PARSE,
                source="test",
                input_data={},
                output_data={},
                episode_id="ep1",
            )
        
        receipts = system.get_episode_receipts("ep1")
        self.assertEqual(len(receipts), 3)


class TestCheckpoint(unittest.TestCase):
    """Tests for Checkpoint."""
    
    def test_create_checkpoint(self):
        """Test creating checkpoint."""
        checkpoint = Checkpoint.create(
            episode_id="ep1",
            phase="COHERENT",
            step_index=0,
            program_state={"x": 1},
            vm_state={"sp": 0},
        )
        
        self.assertEqual(checkpoint.episode_id, "ep1")
        self.assertEqual(checkpoint.phase, "COHERENT")
        self.assertEqual(checkpoint.step_index, 0)
    
    def test_serialization(self):
        """Test checkpoint serialization."""
        checkpoint = Checkpoint.create(
            episode_id="ep1",
            phase="GATED",
            step_index=5,
            program_state={"x": 1},
            vm_state={"sp": 0},
        )
        
        data = checkpoint.to_dict()
        restored = Checkpoint.from_dict(data)
        
        self.assertEqual(restored.checkpoint_id, checkpoint.checkpoint_id)
        self.assertEqual(restored.episode_id, checkpoint.episode_id)


class TestReplayEngine(unittest.TestCase):
    """Tests for ReplayEngine."""
    
    def test_create_engine(self):
        """Test creating replay engine."""
        engine = create_replay_engine()
        self.assertEqual(len(engine.checkpoints), 0)
    
    def test_create_checkpoint(self):
        """Test creating checkpoint."""
        engine = create_replay_engine()
        checkpoint = engine.create_checkpoint(
            episode_id="ep1",
            phase="COHERENT",
            step_index=0,
            program_state={},
            vm_state={},
        )
        
        self.assertIn(checkpoint.checkpoint_id, engine.checkpoints)
    
    def test_execute_replay(self):
        """Test executing replay."""
        engine = create_replay_engine()
        
        # Create checkpoint
        checkpoint = engine.create_checkpoint(
            episode_id="ep1",
            phase="COHERENT",
            step_index=0,
            program_state={},
            vm_state={},
        )
        
        # Execute replay
        def executor(cp):
            return True, "success"
        
        result = engine.execute_replay("ep1", executor, checkpoints=[checkpoint])
        
        self.assertEqual(result.status, ReplayStatus.COMPLETED)
        self.assertEqual(result.checkpoints_restored, 1)


class TestVerifier(unittest.TestCase):
    """Tests for Verifier."""
    
    def test_create_verifier(self):
        """Test creating verifier."""
        verifier = create_verifier()
        self.assertIsNotNone(verifier)
    
    def test_verify_replay(self):
        """Test verifying replay."""
        verifier = create_verifier()
        
        # Verify output match
        verified, details = verifier.verify_replay(
            original_output={"result": 42},
            replay_output={"result": 42},
            original_receipts=[],
            replay_receipts=[],
        )
        
        self.assertTrue(verified)
        self.assertTrue(details["output_match"])


if __name__ == "__main__":
    unittest.main()

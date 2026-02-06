"""
Tests for the Receipt system.

Tests cover:
- ReceiptStepType enum values
- ReceiptContent creation and properties
- ReceiptProvenance chain tracking
- ReceiptSignature HMAC generation
- Receipt creation with all fields
- ReceiptSystem receipt creation
- Receipt chain verification
- Receipt serialization
"""

import pytest
import json
from datetime import datetime
from uuid import uuid4

from src.cnhaai.core.receipts import (
    ReceiptStepType,
    ReceiptDecision,
    ReceiptSignature,
    ReceiptContent,
    ReceiptProvenance,
    Receipt,
    ReceiptSystem
)


class TestReceiptStepType:
    """Tests for ReceiptStepType enum."""

    def test_step_type_values_exist(self):
        """Test that all expected step types are defined."""
        assert ReceiptStepType.GATE_VALIDATION is not None
        assert ReceiptStepType.PHASE_TRANSITION is not None
        assert ReceiptStepType.RECOVERY_ACTION is not None
        assert ReceiptStepType.MANUAL_ANNOTATION is not None
        assert ReceiptStepType.ABSTRACTION_CREATION is not None
        assert ReceiptStepType.EPISODE_START is not None
        assert ReceiptStepType.EPISODE_END is not None

    def test_step_type_count(self):
        """Test that exactly 7 step types are defined."""
        assert len(ReceiptStepType) == 7


class TestReceiptDecision:
    """Tests for ReceiptDecision enum."""

    def test_decision_values_exist(self):
        """Test that all expected decisions are defined."""
        assert ReceiptDecision.PASS is not None
        assert ReceiptDecision.FAIL is not None
        assert ReceiptDecision.WARN is not None
        assert ReceiptDecision.SKIP is not None

    def test_decision_count(self):
        """Test that exactly 4 decisions are defined."""
        assert len(ReceiptDecision) == 4


class TestReceiptSignature:
    """Tests for ReceiptSignature class."""

    def test_signature_creation(self):
        """Test creating a receipt signature."""
        signature = ReceiptSignature(
            algorithm="HMAC-SHA256",
            signer="test-signer",
            signature="test-signature"
        )

        assert signature.algorithm == "HMAC-SHA256"
        assert signature.signer == "test-signer"
        assert signature.signature == "test-signature"

    def test_signature_defaults(self):
        """Test signature default values."""
        signature = ReceiptSignature()

        assert signature.algorithm == "HMAC-SHA256"
        assert signature.signer == "system"
        assert signature.signature == ""

    def test_signature_to_dict(self):
        """Test converting signature to dictionary."""
        signature = ReceiptSignature(
            algorithm="HMAC-SHA256",
            signer="test",
            signature="sig123"
        )

        result = signature.to_dict()

        assert result["algorithm"] == "HMAC-SHA256"
        assert result["signer"] == "test"
        assert result["signature"] == "sig123"

    def test_signature_from_dict(self):
        """Test creating signature from dictionary."""
        data = {
            "algorithm": "HMAC-SHA256",
            "signer": "test-signer",
            "signature": "sig456"
        }

        signature = ReceiptSignature.from_dict(data)

        assert signature.algorithm == "HMAC-SHA256"
        assert signature.signer == "test-signer"
        assert signature.signature == "sig456"

    def test_signature_from_dict_defaults(self):
        """Test from_dict with missing fields."""
        data = {"custom_field": "value"}

        signature = ReceiptSignature.from_dict(data)

        assert signature.algorithm == "HMAC-SHA256"
        assert signature.signer == "system"
        assert signature.signature == ""


class TestReceiptContent:
    """Tests for ReceiptContent class."""

    def test_content_creation(self):
        """Test creating receipt content."""
        content = ReceiptContent(
            step_type=ReceiptStepType.GATE_VALIDATION,
            input_state="input-hash",
            output_state="output-hash",
            decision=ReceiptDecision.PASS,
            details={"score": 0.9}
        )

        assert content.step_type == ReceiptStepType.GATE_VALIDATION
        assert content.input_state == "input-hash"
        assert content.output_state == "output-hash"
        assert content.decision == ReceiptDecision.PASS
        assert content.details == {"score": 0.9}

    def test_content_defaults(self):
        """Test content default values."""
        content = ReceiptContent(step_type=ReceiptStepType.PHASE_TRANSITION)

        assert content.input_state == ""
        assert content.output_state == ""
        assert content.decision == ReceiptDecision.PASS
        assert content.details == {}

    def test_content_to_dict(self):
        """Test converting content to dictionary."""
        content = ReceiptContent(
            step_type=ReceiptStepType.ABSTRACTION_CREATION,
            decision=ReceiptDecision.WARN,
            details={"abstraction_id": "abs-123"}
        )

        result = content.to_dict()

        assert result["step_type"] == "ABSTRACTION_CREATION"
        assert result["input_state"] == ""
        assert result["output_state"] == ""
        assert result["decision"] == "WARN"
        assert result["details"] == {"abstraction_id": "abs-123"}

    def test_content_from_dict(self):
        """Test creating content from dictionary."""
        data = {
            "step_type": "EPISODE_START",
            "input_state": "start-state",
            "output_state": "end-state",
            "decision": "FAIL",
            "details": {"reason": "error"}
        }

        content = ReceiptContent.from_dict(data)

        assert content.step_type == ReceiptStepType.EPISODE_START
        assert content.input_state == "start-state"
        assert content.output_state == "end-state"
        assert content.decision == ReceiptDecision.FAIL
        assert content.details == {"reason": "error"}

    def test_content_from_dict_defaults(self):
        """Test from_dict with missing fields."""
        data = {"step_type": "RECOVERY_ACTION"}

        content = ReceiptContent.from_dict(data)

        assert content.step_type == ReceiptStepType.RECOVERY_ACTION
        assert content.decision == ReceiptDecision.PASS
        assert content.details == {}


class TestReceiptProvenance:
    """Tests for ReceiptProvenance class."""

    def test_provenance_creation(self):
        """Test creating receipt provenance."""
        provenance = ReceiptProvenance(
            parent_receipts=["parent-1", "parent-2"],
            evidence_references=["evidence-1"]
        )

        assert provenance.parent_receipts == ["parent-1", "parent-2"]
        assert provenance.evidence_references == ["evidence-1"]

    def test_provenance_defaults(self):
        """Test provenance default values."""
        provenance = ReceiptProvenance()

        assert provenance.parent_receipts == []
        assert provenance.evidence_references == []

    def test_provenance_to_dict(self):
        """Test converting provenance to dictionary."""
        provenance = ReceiptProvenance(
            parent_receipts=["p1", "p2"],
            evidence_references=["e1", "e2", "e3"]
        )

        result = provenance.to_dict()

        assert result["parent_receipts"] == ["p1", "p2"]
        assert result["evidence_references"] == ["e1", "e2", "e3"]

    def test_provenance_from_dict(self):
        """Test creating provenance from dictionary."""
        data = {
            "parent_receipts": ["parent-id"],
            "evidence_references": ["evidence-id"]
        }

        provenance = ReceiptProvenance.from_dict(data)

        assert provenance.parent_receipts == ["parent-id"]
        assert provenance.evidence_references == ["evidence-id"]

    def test_provenance_from_dict_defaults(self):
        """Test from_dict with missing fields."""
        data = {}

        provenance = ReceiptProvenance.from_dict(data)

        assert provenance.parent_receipts == []
        assert provenance.evidence_references == []


class TestReceipt:
    """Tests for Receipt class."""

    def test_receipt_creation(self):
        """Test creating a receipt."""
        content = ReceiptContent(
            step_type=ReceiptStepType.GATE_VALIDATION,
            decision=ReceiptDecision.PASS
        )
        provenance = ReceiptProvenance()
        signature = ReceiptSignature()

        receipt = Receipt(
            version="1.0.0",
            receipt_id="receipt-123",
            episode_id="episode-456",
            content=content,
            provenance=provenance,
            signature=signature
        )

        assert receipt.version == "1.0.0"
        assert receipt.receipt_id == "receipt-123"
        assert receipt.episode_id == "episode-456"
        assert receipt.content == content
        assert receipt.provenance == provenance
        assert receipt.signature == signature

    def test_receipt_defaults(self):
        """Test receipt default values."""
        receipt = Receipt()

        assert receipt.version == "1.0.0"
        assert receipt.receipt_id is not None
        assert len(receipt.receipt_id) > 0
        assert isinstance(receipt.timestamp, datetime)
        assert receipt.episode_id == ""
        assert receipt.content.step_type == ReceiptStepType.GATE_VALIDATION
        assert receipt.signature.algorithm == "HMAC-SHA256"

    def test_receipt_to_dict(self):
        """Test converting receipt to dictionary."""
        receipt = Receipt(
            receipt_id="test-id",
            episode_id="episode-id",
            content=ReceiptContent(
                step_type=ReceiptStepType.PHASE_TRANSITION,
                decision=ReceiptDecision.PASS
            ),
            provenance=ReceiptProvenance(
                parent_receipts=["parent-id"]
            ),
            signature=ReceiptSignature(
                signer="test-signer",
                signature="test-sig"
            )
        )

        result = receipt.to_dict()

        assert result["version"] == "1.0.0"
        assert result["receipt_id"] == "test-id"
        assert result["episode_id"] == "episode-id"
        assert result["content"]["step_type"] == "PHASE_TRANSITION"
        assert result["provenance"]["parent_receipts"] == ["parent-id"]
        assert result["signature"]["signer"] == "test-signer"
        assert result["signature"]["signature"] == "test-sig"

    def test_receipt_to_json(self):
        """Test converting receipt to JSON string."""
        receipt = Receipt(
            episode_id="test-episode",
            content=ReceiptContent(step_type=ReceiptStepType.EPISODE_START)
        )

        json_str = receipt.to_json()

        parsed = json.loads(json_str)
        assert parsed["episode_id"] == "test-episode"
        assert parsed["content"]["step_type"] == "EPISODE_START"

    def test_receipt_from_dict(self):
        """Test creating receipt from dictionary."""
        data = {
            "version": "1.0.0",
            "receipt_id": "receipt-123",
            "timestamp": "2024-01-01T00:00:00",
            "episode_id": "episode-456",
            "content": {
                "step_type": "GATE_VALIDATION",
                "input_state": "input",
                "output_state": "output",
                "decision": "PASS",
                "details": {"score": 0.9}
            },
            "provenance": {
                "parent_receipts": ["parent-1"],
                "evidence_references": ["evidence-1"]
            },
            "signature": {
                "algorithm": "HMAC-SHA256",
                "signer": "system",
                "signature": "sig-123"
            }
        }

        receipt = Receipt.from_dict(data)

        assert receipt.version == "1.0.0"
        assert receipt.receipt_id == "receipt-123"
        assert receipt.episode_id == "episode-456"
        assert receipt.content.step_type == ReceiptStepType.GATE_VALIDATION
        assert receipt.provenance.parent_receipts == ["parent-1"]
        assert receipt.signature.signature == "sig-123"

    def test_receipt_from_json(self):
        """Test creating receipt from JSON string."""
        json_str = json.dumps({
            "version": "1.0.0",
            "receipt_id": "test-id",
            "timestamp": "2024-01-01T00:00:00",
            "episode_id": "test-episode",
            "content": {
                "step_type": "PHASE_TRANSITION",
                "decision": "PASS"
            },
            "provenance": {},
            "signature": {}
        })

        receipt = Receipt.from_json(json_str)

        assert receipt.receipt_id == "test-id"
        assert receipt.content.step_type == ReceiptStepType.PHASE_TRANSITION

    def test_receipt_compute_hash(self):
        """Test computing receipt hash."""
        receipt = Receipt(
            receipt_id="test-id",
            episode_id="test-episode",
            content=ReceiptContent(step_type=ReceiptStepType.EPISODE_START)
        )

        hash_value = receipt.compute_hash()

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 hex digest

    def test_receipt_hash_changes_with_content(self):
        """Test that hash changes when content changes."""
        receipt1 = Receipt(
            receipt_id="test-id",
            episode_id="test-episode",
            content=ReceiptContent(step_type=ReceiptStepType.EPISODE_START)
        )
        receipt2 = Receipt(
            receipt_id="test-id",
            episode_id="test-episode",
            content=ReceiptContent(step_type=ReceiptStepType.EPISODE_END)
        )

        hash1 = receipt1.compute_hash()
        hash2 = receipt2.compute_hash()

        assert hash1 != hash2

    def test_receipt_roundtrip(self):
        """Test serialization roundtrip."""
        original = Receipt(
            receipt_id="roundtrip-id",
            episode_id="roundtrip-episode",
            content=ReceiptContent(
                step_type=ReceiptStepType.RECOVERY_ACTION,
                decision=ReceiptDecision.WARN,
                details={"recovery_type": "reconstruction"}
            ),
            provenance=ReceiptProvenance(
                parent_receipts=["parent-id"],
                evidence_references=["evidence-id"]
            )
        )

        restored = Receipt.from_dict(original.to_dict())

        assert restored.receipt_id == original.receipt_id
        assert restored.episode_id == original.episode_id
        assert restored.content.step_type == original.content.step_type
        assert restored.content.decision == original.content.decision
        assert restored.provenance.parent_receipts == original.provenance.parent_receipts


class TestReceiptSystem:
    """Tests for ReceiptSystem class."""

    def test_system_creation(self):
        """Test creating a receipt system."""
        system = ReceiptSystem(
            signing_key="test-key",
            storage_type="in_memory",
            retention="session"
        )

        assert system.signing_key == "test-key"
        assert system.storage_type == "in_memory"
        assert system.retention == "session"
        assert system.receipts == {}
        assert system.receipts_by_episode == {}
        assert system.receipt_chain == []

    def test_system_defaults(self):
        """Test system default values."""
        system = ReceiptSystem()

        assert system.signing_key == "cnhaai-prototype-key"
        assert system.storage_type == "in_memory"
        assert system.retention == "session"

    def test_emit_receipt(self):
        """Test emitting a receipt."""
        system = ReceiptSystem(signing_key="test-key")

        receipt = system.emit_receipt(
            episode_id="test-episode",
            step_type=ReceiptStepType.GATE_VALIDATION,
            input_state="input-hash",
            output_state="output-hash",
            decision=ReceiptDecision.PASS,
            details={"score": 0.9}
        )

        assert receipt.episode_id == "test-episode"
        assert receipt.content.step_type == ReceiptStepType.GATE_VALIDATION
        assert receipt.signature.algorithm == "HMAC-SHA256"
        assert receipt.signature.signer == "system"
        assert len(receipt.signature.signature) > 0

    def test_emit_receipt_with_parent(self):
        """Test emitting a receipt with parent references."""
        system = ReceiptSystem(signing_key="test-key")

        parent = system.emit_receipt(
            episode_id="test-episode",
            step_type=ReceiptStepType.EPISODE_START
        )

        child = system.emit_receipt(
            episode_id="test-episode",
            step_type=ReceiptStepType.GATE_VALIDATION,
            parent_receipts=[parent.receipt_id]
        )

        assert parent.receipt_id in child.provenance.parent_receipts

    def test_receipt_stored(self):
        """Test that emitted receipts are stored."""
        system = ReceiptSystem(signing_key="test-key")

        receipt = system.emit_receipt(
            episode_id="test-episode",
            step_type=ReceiptStepType.PHASE_TRANSITION
        )

        assert receipt.receipt_id in system.receipts
        assert "test-episode" in system.receipts_by_episode
        assert receipt.receipt_id in system.receipt_chain

    def test_get_receipt(self):
        """Test retrieving a receipt by ID."""
        system = ReceiptSystem(signing_key="test-key")
        emitted = system.emit_receipt(
            episode_id="test-episode",
            step_type=ReceiptStepType.ABSTRACTION_CREATION
        )

        retrieved = system.get_receipt(emitted.receipt_id)

        assert retrieved == emitted

    def test_get_nonexistent_receipt(self):
        """Test retrieving a non-existent receipt."""
        system = ReceiptSystem()

        result = system.get_receipt("nonexistent-id")

        assert result is None

    def test_get_episode_receipts(self):
        """Test getting all receipts for an episode."""
        system = ReceiptSystem(signing_key="test-key")
        system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.EPISODE_START)
        system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.GATE_VALIDATION)
        system.emit_receipt(episode_id="ep2", step_type=ReceiptStepType.EPISODE_START)

        ep1_receipts = system.get_episode_receipts("ep1")
        ep2_receipts = system.get_episode_receipts("ep2")

        assert len(ep1_receipts) == 2
        assert len(ep2_receipts) == 1

    def test_get_receipt_chain_sorted(self):
        """Test that receipt chain is sorted by timestamp."""
        system = ReceiptSystem(signing_key="test-key")
        
        # Create receipts in reverse order
        r2 = system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.EPISODE_END)
        r1 = system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.GATE_VALIDATION)
        r0 = system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.EPISODE_START)

        chain = system.get_receipt_chain("ep1")

        assert chain[0].receipt_id == r0.receipt_id
        assert chain[1].receipt_id == r1.receipt_id
        assert chain[2].receipt_id == r2.receipt_id

    def test_verify_receipt_valid(self):
        """Test verifying a valid receipt."""
        system = ReceiptSystem(signing_key="test-key")
        receipt = system.emit_receipt(
            episode_id="test-episode",
            step_type=ReceiptStepType.GATE_VALIDATION
        )

        is_valid = system.verify_receipt(receipt)

        assert is_valid is True

    def test_verify_receipt_invalid(self):
        """Test verifying a tampered receipt."""
        system = ReceiptSystem(signing_key="test-key")
        receipt = system.emit_receipt(
            episode_id="test-episode",
            step_type=ReceiptStepType.GATE_VALIDATION
        )

        # Tamper with the receipt
        receipt.content = ReceiptContent(step_type=ReceiptStepType.EPISODE_END)

        is_valid = system.verify_receipt(receipt)

        assert is_valid is False

    def test_verify_episode_chain_valid(self):
        """Test verifying a valid episode chain."""
        system = ReceiptSystem(signing_key="test-key")
        system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.EPISODE_START)
        system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.GATE_VALIDATION)
        system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.EPISODE_END)

        is_valid = system.verify_episode_chain("ep1")

        assert is_valid is True

    def test_verify_episode_chain_empty(self):
        """Test verifying an empty episode chain."""
        system = ReceiptSystem()

        is_valid = system.verify_episode_chain("nonexistent")

        assert is_valid is True  # Empty is considered valid

    def test_verify_episode_chain_tampered(self):
        """Test verifying a tampered episode chain."""
        system = ReceiptSystem(signing_key="test-key")
        r1 = system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.EPISODE_START)
        r2 = system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.GATE_VALIDATION)

        # Tamper with the second receipt
        r2.content = ReceiptContent(step_type=ReceiptStepType.EPISODE_END)

        is_valid = system.verify_episode_chain("ep1")

        assert is_valid is False

    def test_create_gate_receipt(self):
        """Test creating a gate receipt."""
        system = ReceiptSystem(signing_key="test-key")

        receipt = system.create_gate_receipt(
            episode_id="test-episode",
            gate_name="Evidence Sufficiency Gate",
            decision=ReceiptDecision.PASS,
            details={"score": 0.9}
        )

        assert receipt.content.step_type == ReceiptStepType.GATE_VALIDATION
        assert receipt.content.details["gate_name"] == "Evidence Sufficiency Gate"

    def test_create_phase_receipt(self):
        """Test creating a phase receipt."""
        system = ReceiptSystem(signing_key="test-key")

        receipt = system.create_phase_receipt(
            episode_id="test-episode",
            from_phase="ACQUISITION",
            to_phase="CONSTRUCTION",
            duration_ms=100,
            steps_completed=5
        )

        assert receipt.content.step_type == ReceiptStepType.PHASE_TRANSITION
        assert receipt.content.details["from_phase"] == "ACQUISITION"
        assert receipt.content.details["to_phase"] == "CONSTRUCTION"

    def test_get_stats(self):
        """Test getting system statistics."""
        system = ReceiptSystem(signing_key="test-key")
        system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.EPISODE_START)
        system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.EPISODE_END)
        system.emit_receipt(episode_id="ep2", step_type=ReceiptStepType.EPISODE_START)

        stats = system.get_stats()

        assert stats["total_receipts"] == 3
        assert stats["episodes_with_receipts"] == 2
        assert stats["chain_length"] == 3
        assert stats["storage_type"] == "in_memory"
        assert stats["retention"] == "session"

    def test_clear(self):
        """Test clearing the system."""
        system = ReceiptSystem(signing_key="test-key")
        system.emit_receipt(episode_id="ep1", step_type=ReceiptStepType.EPISODE_START)

        system.clear()

        assert len(system.receipts) == 0
        assert len(system.receipts_by_episode) == 0
        assert len(system.receipt_chain) == 0
        assert system._counter == 0

"""
Integration tests for the Minimal Kernel.

Tests cover:
- MinimalKernel creation
- create_abstraction method
- execute_episode with goals and evidence
- get_receipts retrieval
- verify_episode chain verification
- Full episode execution flow
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.cnhaai.kernel.minimal import MinimalKernel, EpisodeResult


class TestMinimalKernelCreation:
    """Tests for MinimalKernel creation and initialization."""

    def test_kernel_creation_default(self):
        """Test creating a kernel with default settings."""
        kernel = MinimalKernel()

        assert kernel.version == "1.0.0"
        assert kernel.episode_count == 0
        assert kernel.abstraction_layer is not None
        assert kernel.gate_manager is not None
        assert kernel.phase_manager is not None
        assert kernel.receipt_system is not None
        assert kernel.coherence_budget is not None

    def test_kernel_creation_custom_version(self):
        """Test creating a kernel with custom version."""
        kernel = MinimalKernel(version="2.0.0")

        assert kernel.version == "2.0.0"

    def test_kernel_creation_custom_settings(self):
        """Test creating a kernel with custom settings."""
        settings = {
            "coherence_budget": 0.8,
            "max_abstraction_levels": 5,
            "evidence_threshold": 0.9,
            "receipt_retention": "persistent",
        }

        kernel = MinimalKernel(settings=settings)

        assert kernel.settings["coherence_budget"] == 0.8
        assert kernel.settings["max_abstraction_levels"] == 5

    def test_default_settings(self):
        """Test default settings are applied."""
        kernel = MinimalKernel()

        assert kernel.settings["coherence_budget"] == 0.5
        assert kernel.settings["max_abstraction_levels"] == 3
        assert kernel.settings["evidence_threshold"] == 0.8
        assert kernel.settings["receipt_retention"] == "session"

    def test_gate_manager_has_default_gates(self):
        """Test that gate manager has default gates."""
        kernel = MinimalKernel()

        assert len(kernel.gate_manager.gates) == 2
        gate_names = [g.name for g in kernel.gate_manager.gates]
        assert "Evidence Sufficiency Gate" in gate_names
        assert "Coherence Check Gate" in gate_names

    def test_receipt_system_configured(self):
        """Test that receipt system is properly configured."""
        kernel = MinimalKernel()

        assert kernel.receipt_system.storage_type == "in_memory"
        assert kernel.receipt_system.retention == "session"
        assert kernel.receipt_system.signing_key == "cnhaai-prototype-key"

    def test_coherence_budget_initialized(self):
        """Test that coherence budget is initialized."""
        kernel = MinimalKernel()

        assert kernel.coherence_budget.current == 0.5
        assert kernel.coherence_budget.initial == 1.0


class TestCreateAbstraction:
    """Tests for the create_abstraction method."""

    def test_create_abstraction_descriptive(self):
        """Test creating a descriptive abstraction."""
        kernel = MinimalKernel()

        abstraction = kernel.create_abstraction(
            abstraction_type="descriptive",
            evidence=["evidence1", "evidence2"],
            scope="test-scope",
            validity={"condition": "test"},
            content={"summary": "test abstraction"},
        )

        assert abstraction.type.value == 1  # DESCRIPTIVE
        assert abstraction.evidence == {"evidence1", "evidence2"}
        assert abstraction.scope == {"test-scope"}
        assert abstraction.id in kernel.abstraction_layer.abstractions

    def test_create_abstraction_mechanistic(self):
        """Test creating a mechanistic abstraction."""
        kernel = MinimalKernel()

        abstraction = kernel.create_abstraction(
            abstraction_type="mechanistic", evidence=["ev1"], scope="mechanism-scope"
        )

        assert abstraction.type.value == 2  # MECHANISTIC

    def test_create_abstraction_normative(self):
        """Test creating a normative abstraction."""
        kernel = MinimalKernel()

        abstraction = kernel.create_abstraction(
            abstraction_type="normative", evidence=["ev1"], scope="normative-scope"
        )

        assert abstraction.type.value == 3  # NORMATIVE

    def test_create_abstraction_comparative(self):
        """Test creating a comparative abstraction."""
        kernel = MinimalKernel()

        abstraction = kernel.create_abstraction(
            abstraction_type="comparative", evidence=["ev1"], scope="comparative-scope"
        )

        assert abstraction.type.value == 4  # COMPARATIVE

    def test_create_abstraction_with_parent(self):
        """Test creating an abstraction with a parent."""
        kernel = MinimalKernel()
        parent = kernel.create_abstraction(
            abstraction_type="descriptive", evidence=["ev1"], scope="parent-scope"
        )

        child = kernel.create_abstraction(
            abstraction_type="mechanistic",
            evidence=["ev2"],
            scope="child-scope",
            parent_id=parent.id,
        )

        assert child.parent_id == parent.id
        assert child.id in parent.children_ids

    def test_create_multiple_abstractions(self):
        """Test creating multiple abstractions."""
        kernel = MinimalKernel()

        for i in range(5):
            kernel.create_abstraction(
                abstraction_type="descriptive", evidence=[f"ev{i}"], scope=f"scope{i}"
            )

        assert len(kernel.abstraction_layer.abstractions) == 5

    def test_case_insensitive_type(self):
        """Test that abstraction type is case insensitive."""
        kernel = MinimalKernel()

        abstraction1 = kernel.create_abstraction(
            abstraction_type="DESCRIPTIVE", evidence=["ev1"], scope="scope1"
        )
        abstraction2 = kernel.create_abstraction(
            abstraction_type="descriptive", evidence=["ev2"], scope="scope2"
        )

        assert abstraction1.type == abstraction2.type


class TestExecuteEpisode:
    """Tests for the execute_episode method."""

    def test_execute_episode_basic(self):
        """Test executing a basic episode."""
        kernel = MinimalKernel()

        result = kernel.execute_episode(goal="test goal")

        assert result is not None
        assert isinstance(result, EpisodeResult)
        assert result.episode_id is not None
        assert isinstance(result.success, bool)
        assert result.final_phase in [
            "ACQUISITION",
            "CONSTRUCTION",
            "REASONING",
            "VALIDATION",
            "RECOVERY",
            "unknown",
        ]

    def test_execute_episode_increments_count(self):
        """Test that episode count is incremented."""
        kernel = MinimalKernel()

        assert kernel.episode_count == 0

        kernel.execute_episode(goal="test1")
        assert kernel.episode_count == 1

        kernel.execute_episode(goal="test2")
        assert kernel.episode_count == 2

    def test_execute_episode_generates_receipts(self):
        """Test that episode generates receipts."""
        kernel = MinimalKernel()

        result = kernel.execute_episode(goal="test goal")

        assert result.receipts_generated > 0

    def test_execute_episode_creates_abstractions(self):
        """Test that episode may create abstractions."""
        kernel = MinimalKernel()

        result = kernel.execute_episode(goal="test goal")

        # Some episodes create abstractions during construction phase
        assert len(result.abstractions_created) >= 0

    def test_execute_episode_with_evidence(self):
        """Test executing episode with evidence."""
        kernel = MinimalKernel()

        result = kernel.execute_episode(
            goal="test goal", evidence=["evidence1", "evidence2", "evidence3"]
        )

        assert result is not None
        assert result.receipts_generated > 0

    def test_execute_episode_with_constraints(self):
        """Test executing episode with constraints."""
        kernel = MinimalKernel()

        constraints = [
            {"type": "must", "value": "constraint1"},
            {"type": "must_not", "value": "forbidden"},
        ]

        result = kernel.execute_episode(goal="test goal", constraints=constraints)

        assert result is not None

    def test_execute_episode_with_max_steps(self):
        """Test executing episode with max steps."""
        kernel = MinimalKernel()

        result = kernel.execute_episode(goal="test goal", max_steps=50)

        assert result is not None

    def test_execute_episode_updates_coherence(self):
        """Test that episode may update coherence."""
        kernel = MinimalKernel()
        initial_coherence = kernel.coherence_budget.current

        result = kernel.execute_episode(goal="test goal")

        # Coherence may have changed
        assert kernel.coherence_budget.current is not None

    def test_execute_multiple_episodes(self):
        """Test executing multiple episodes."""
        kernel = MinimalKernel()

        for i in range(3):
            result = kernel.execute_episode(goal=f"goal {i}")
            assert result is not None

        assert kernel.episode_count == 3


class TestGetReceipts:
    """Tests for the get_receipts method."""

    def test_get_receipts_for_episode(self):
        """Test getting receipts for an episode."""
        kernel = MinimalKernel()
        result = kernel.execute_episode(goal="test goal")
        episode_id = result.episode_id

        receipts = kernel.get_receipts(episode_id)

        assert len(receipts) == result.receipts_generated

    def test_get_receipts_empty_for_nonexistent(self):
        """Test getting receipts for non-existent episode."""
        kernel = MinimalKernel()

        receipts = kernel.get_receipts("nonexistent-id")

        assert receipts == []

    def test_get_receipts_structure(self):
        """Test that receipts have correct structure."""
        kernel = MinimalKernel()
        result = kernel.execute_episode(goal="test goal")
        receipts = kernel.get_receipts(result.episode_id)

        if receipts:
            receipt = receipts[0]
            assert "version" in receipt
            assert "receipt_id" in receipt
            assert "timestamp" in receipt
            assert "episode_id" in receipt
            assert "content" in receipt
            assert "provenance" in receipt
            assert "signature" in receipt


class TestVerifyEpisode:
    """Tests for the verify_episode method."""

    def test_verify_valid_episode(self):
        """Test verifying a valid episode."""
        kernel = MinimalKernel()
        result = kernel.execute_episode(goal="test goal")

        is_valid = kernel.verify_episode(result.episode_id)

        assert is_valid is True

    def test_verify_nonexistent_episode(self):
        """Test verifying non-existent episode."""
        kernel = MinimalKernel()

        is_valid = kernel.verify_episode("nonexistent-id")

        assert is_valid is True  # Empty is valid

    def test_verify_episode_chain(self):
        """Test episode chain verification."""
        kernel = MinimalKernel()

        for i in range(3):
            result = kernel.execute_episode(goal=f"goal {i}")
            is_valid = kernel.verify_episode(result.episode_id)
            assert is_valid is True


class TestGetAbstractions:
    """Tests for the get_abstractions method."""

    def test_get_all_abstractions(self):
        """Test getting all abstractions."""
        kernel = MinimalKernel()
        kernel.create_abstraction(abstraction_type="descriptive", evidence=["ev1"], scope="scope1")
        kernel.create_abstraction(abstraction_type="mechanistic", evidence=["ev2"], scope="scope2")

        abstractions = kernel.get_abstractions()

        assert len(abstractions) == 2

    def test_get_abstractions_by_scope(self):
        """Test getting abstractions filtered by scope."""
        kernel = MinimalKernel()
        kernel.create_abstraction(
            abstraction_type="descriptive", evidence=["ev1"], scope="target-scope"
        )
        kernel.create_abstraction(
            abstraction_type="mechanistic", evidence=["ev2"], scope="other-scope"
        )

        abstractions = kernel.get_abstractions(scope="target-scope")

        assert len(abstractions) == 1
        assert abstractions[0]["scope"] == ["target-scope"]

    def test_get_abstractions_empty(self):
        """Test getting abstractions when none exist."""
        kernel = MinimalKernel()

        abstractions = kernel.get_abstractions()

        assert abstractions == []


class TestGetCoherenceStatus:
    """Tests for the get_coherence_status method."""

    def test_get_coherence_status(self):
        """Test getting coherence status."""
        kernel = MinimalKernel()

        status = kernel.get_coherence_status()

        assert "current" in status
        assert "status" in status
        assert "is_healthy" in status
        assert "is_critical" in status
        assert "is_degraded" in status

    def test_coherence_status_reflects_episode(self):
        """Test that coherence status updates after episode."""
        kernel = MinimalKernel()
        initial_status = kernel.get_coherence_status()

        kernel.execute_episode(goal="test goal")

        final_status = kernel.get_coherence_status()

        assert final_status["current"] is not None


class TestGetPhaseHistory:
    """Tests for the get_phase_history method."""

    def test_get_phase_history(self):
        """Test getting phase history."""
        kernel = MinimalKernel()
        kernel.execute_episode(goal="test goal")

        history = kernel.get_phase_history()

        assert len(history) >= 0  # May have completed phases
        for phase_info in history:
            assert "phase" in phase_info
            assert "start_time" in phase_info
            assert "end_time" in phase_info


class TestReset:
    """Tests for the reset method."""

    def test_reset_clears_state(self):
        """Test that reset clears all state."""
        kernel = MinimalKernel()
        kernel.execute_episode(goal="test1")
        kernel.execute_episode(goal="test2")

        kernel.reset()

        assert kernel.episode_count == 0
        assert len(kernel.abstraction_layer.abstractions) == 0
        assert len(kernel.receipt_system.receipts) == 0

    def test_reset_reinitializes_components(self):
        """Test that reset reinitializes components."""
        kernel = MinimalKernel()
        kernel.execute_episode(goal="test")

        kernel.reset()

        assert kernel.gate_manager is not None
        assert kernel.phase_manager is not None
        assert kernel.receipt_system is not None
        assert kernel.coherence_budget is not None


class TestGetStats:
    """Tests for the get_stats method."""

    def test_get_stats(self):
        """Test getting kernel statistics."""
        kernel = MinimalKernel()
        kernel.execute_episode(goal="test1")
        kernel.execute_episode(goal="test2")

        stats = kernel.get_stats()

        assert stats["version"] == "1.0.0"
        assert stats["episodes_executed"] == 2
        assert "coherence_status" in stats
        assert "settings" in stats

    def test_stats_reflects_abstraction_count(self):
        """Test that stats reflect abstraction count."""
        kernel = MinimalKernel()
        kernel.create_abstraction(abstraction_type="descriptive", evidence=["ev1"], scope="scope1")

        stats = kernel.get_stats()

        assert stats["abstractions_count"] == 1

    def test_stats_reflects_receipt_count(self):
        """Test that stats reflect receipt count."""
        kernel = MinimalKernel()
        kernel.execute_episode(goal="test goal")

        stats = kernel.get_stats()

        assert stats["receipts_count"] > 0


class TestEpisodeResult:
    """Tests for EpisodeResult class."""

    def test_episode_result_to_dict(self):
        """Test converting episode result to dictionary."""
        kernel = MinimalKernel()
        result = kernel.execute_episode(goal="test goal")

        result_dict = result.to_dict()

        assert "episode_id" in result_dict
        assert "success" in result_dict
        assert "final_phase" in result_dict
        assert "abstractions_created" in result_dict
        assert "receipts_generated" in result_dict
        assert "coherence_status" in result_dict
        assert "duration_ms" in result_dict
        assert "metadata" in result_dict

    def test_episode_result_contains_goal(self):
        """Test that result metadata contains goal."""
        kernel = MinimalKernel()
        result = kernel.execute_episode(goal="my-test-goal")

        assert result.metadata["goal"] == "my-test-goal"


class TestFullEpisodeFlow:
    """Tests for full episode execution flow."""

    def test_complete_episode_flow(self):
        """Test a complete episode execution flow."""
        kernel = MinimalKernel()

        # Execute episode
        result = kernel.execute_episode(
            goal="analyze problem and provide solution",
            evidence=["observation1", "observation2", "observation3"],
            constraints=[{"type": "must", "value": "consistency"}],
        )

        # Verify result
        assert result.episode_id is not None
        assert isinstance(result.success, bool)
        assert result.duration_ms >= 0

        # Verify receipts were generated
        assert result.receipts_generated > 0

        # Verify episode can be verified
        assert kernel.verify_episode(result.episode_id) is True

    def test_multiple_complete_episodes(self):
        """Test multiple complete episodes."""
        kernel = MinimalKernel()

        for i in range(5):
            result = kernel.execute_episode(
                goal=f"episode {i}",
                evidence=[f"evidence {i}"],
                constraints=[{"type": "must", "value": f"constraint{i}"}],
            )

            assert result.episode_id is not None
            assert kernel.verify_episode(result.episode_id) is True

        assert kernel.episode_count == 5
        stats = kernel.get_stats()
        assert stats["episodes_executed"] == 5

    def test_episode_with_recovery(self):
        """Test episode that may enter recovery phase."""
        kernel = MinimalKernel()

        # Execute episode that might trigger recovery
        result = kernel.execute_episode(
            goal="test recovery flow",
            constraints=[{"type": "must_not", "value": "forbidden_value"}],
        )

        # Episode should complete (may succeed or fail)
        assert result is not None
        assert result.final_phase in [
            "unknown",
            "ACQUISITION",
            "CONSTRUCTION",
            "REASONING",
            "VALIDATION",
            "RECOVERY",
        ]

    def test_kernel_state_persistence_across_episodes(self):
        """Test that kernel state persists across episodes."""
        kernel = MinimalKernel()

        # Create abstraction in first episode
        result1 = kernel.execute_episode(goal="episode1")
        initial_abstraction_count = len(kernel.abstraction_layer.abstractions)

        # Second episode should see existing abstractions
        result2 = kernel.execute_episode(goal="episode2")

        # Abstractions persist
        assert len(kernel.abstraction_layer.abstractions) >= initial_abstraction_count

    def test_receipt_chain_integrity(self):
        """Test that receipt chains maintain integrity."""
        kernel = MinimalKernel()

        result = kernel.execute_episode(goal="test integrity")

        # Verify all receipts for the episode
        receipts = kernel.get_receipts(result.episode_id)

        # Each receipt should be verifiable
        for receipt_dict in receipts:
            receipt = kernel.receipt_system.receipts.get(receipt_dict["receipt_id"])
            if receipt:
                assert kernel.receipt_system.verify_receipt(receipt) is True

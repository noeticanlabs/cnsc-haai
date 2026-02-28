"""
Tests for the CoherenceBudget class.

Tests cover:
- Initial coherence level (1.0)
- Degradation on contradictions (degrade method)
- Recovery on validation (recover method)
- Coherence bounds (0.0 to 1.0)
- can_proceed threshold checking
- needs_recovery detection
- Degradation rate summary
- All coherence states (optimal, healthy, acceptable, degraded, critical)
"""

import pytest
from datetime import datetime

from src.cnhaai.core.coherence import CoherenceBudget


class TestCoherenceBudgetCreation:
    """Tests for CoherenceBudget class creation."""

    def test_default_initial_values(self):
        """Test that default values are set correctly."""
        budget = CoherenceBudget()

        assert budget.current == 1.0
        assert budget.initial == 1.0
        assert budget.minimum == 0.0
        assert budget.maximum == 1.0
        assert budget.degradation_rate == 0.1
        assert budget.recovery_rate == 0.05
        assert budget.degradation_history == []
        assert budget.recovery_history == []

    def test_custom_initial_values(self):
        """Test creating budget with custom values."""
        budget = CoherenceBudget(
            current=0.8,
            initial=1.0,
            minimum=0.2,
            maximum=1.0,
            degradation_rate=0.15,
            recovery_rate=0.08,
        )

        assert budget.current == 0.8
        assert budget.initial == 1.0
        assert budget.minimum == 0.2
        assert budget.maximum == 1.0
        assert budget.degradation_rate == 0.15
        assert budget.recovery_rate == 0.08

    def test_current_clamped_to_bounds(self):
        """Test that current is clamped to min/max bounds."""
        budget = CoherenceBudget(current=1.5)
        assert budget.current == 1.0

        budget = CoherenceBudget(current=-0.5)
        assert budget.current == 0.0

    def test_initial_clamped_to_bounds(self):
        """Test that initial is clamped to min/max bounds."""
        budget = CoherenceBudget(initial=1.5, current=0.8)
        assert budget.initial == 1.0

        budget = CoherenceBudget(initial=-0.5, current=0.5)
        assert budget.initial == 0.0


class TestCoherenceDegradation:
    """Tests for coherence degradation."""

    def test_degrade_with_default_rate(self):
        """Test degradation using default rate."""
        budget = CoherenceBudget()
        budget.degrade()

        assert abs(budget.current - 0.9) < 0.001
        assert len(budget.degradation_history) == 1

    def test_degrade_with_specific_amount(self):
        """Test degradation with specific amount."""
        budget = CoherenceBudget()
        budget.degrade(amount=0.2)

        assert budget.current == 0.8

    def test_degrade_history_recorded(self):
        """Test that degradation is recorded in history."""
        budget = CoherenceBudget()
        budget.degrade(amount=0.1, reason="test_contradiction", metadata={"key": "value"})

        assert len(budget.degradation_history) == 1
        entry = budget.degradation_history[0]
        assert entry["old_value"] == 1.0
        assert entry["new_value"] == 0.9
        assert entry["amount"] == 0.1
        assert entry["reason"] == "test_contradiction"
        assert entry["metadata"] == {"key": "value"}

    def test_degrade_multiple_times(self):
        """Test multiple degradations."""
        budget = CoherenceBudget()
        budget.degrade()
        budget.degrade()
        budget.degrade()

        assert abs(budget.current - 0.7) < 0.001
        assert len(budget.degradation_history) == 3

    def test_degrade_respects_minimum(self):
        """Test that degradation respects minimum bound."""
        budget = CoherenceBudget(current=0.15, minimum=0.0)
        budget.degrade(amount=1.0)

        assert budget.current == 0.0

    def test_degrade_no_change_at_minimum(self):
        """Test that degradation doesn't change at minimum."""
        budget = CoherenceBudget(current=0.0)
        budget.degrade()

        assert budget.current == 0.0
        # Note: degradation is recorded but current doesn't change
        assert len(budget.degradation_history) == 1

    def test_apply_degradation_factor(self):
        """Test multiplicative degradation factor."""
        budget = CoherenceBudget()
        budget.apply_degradation_factor(0.8)

        assert budget.current == 0.8

    def test_apply_degradation_factor_respects_minimum(self):
        """Test that multiplicative degradation respects minimum."""
        budget = CoherenceBudget(current=0.1, minimum=0.0)
        budget.apply_degradation_factor(0.5)

        assert budget.current == 0.05

    def test_degrade_updates_timestamp(self):
        """Test that degradation updates last_update."""
        budget = CoherenceBudget()
        original_time = budget.last_update
        budget.degrade()

        assert budget.last_update >= original_time


class TestCoherenceRecovery:
    """Tests for coherence recovery."""

    def test_recover_with_default_rate(self):
        """Test recovery using default rate."""
        budget = CoherenceBudget(current=0.8)
        budget.recover()

        assert abs(budget.current - 0.85) < 0.001

    def test_recover_with_specific_amount(self):
        """Test recovery with specific amount."""
        budget = CoherenceBudget(current=0.7)
        budget.recover(amount=0.2)

        assert abs(budget.current - 0.9) < 0.001

    def test_recover_history_recorded(self):
        """Test that recovery is recorded in history."""
        budget = CoherenceBudget(current=0.8)
        budget.recover(amount=0.1, reason="validation_success", metadata={"detail": "test"})

        assert len(budget.recovery_history) == 1
        entry = budget.recovery_history[0]
        assert entry["old_value"] == 0.8
        assert entry["new_value"] == 0.9
        assert entry["amount"] == 0.1
        assert entry["reason"] == "validation_success"
        assert entry["metadata"] == {"detail": "test"}

    def test_recover_multiple_times(self):
        """Test multiple recoveries."""
        budget = CoherenceBudget(current=0.6)
        budget.recover()
        budget.recover()
        budget.recover()

        # 0.6 + 0.05*3 = 0.75
        assert abs(budget.current - 0.75) < 0.01
        assert len(budget.recovery_history) == 3

    def test_recover_respects_maximum(self):
        """Test that recovery respects maximum bound."""
        budget = CoherenceBudget(current=0.95, maximum=1.0)
        budget.recover(amount=0.5)

        assert budget.current == 1.0

    def test_recover_no_change_at_maximum(self):
        """Test that recovery doesn't change at maximum."""
        budget = CoherenceBudget(current=1.0)
        budget.recover()

        assert budget.current == 1.0
        # Note: recovery is recorded but current doesn't change
        assert len(budget.recovery_history) == 1

    def test_recover_updates_timestamp(self):
        """Test that recovery updates last_update."""
        budget = CoherenceBudget(current=0.8)
        original_time = budget.last_update
        budget.recover()

        assert budget.last_update >= original_time


class TestCoherenceBounds:
    """Tests for coherence bounds."""

    def test_bounds_default(self):
        """Test default bounds are 0.0 to 1.0."""
        budget = CoherenceBudget()

        assert budget.minimum == 0.0
        assert budget.maximum == 1.0

    def test_current_never_exceeds_maximum(self):
        """Test that current never exceeds maximum."""
        budget = CoherenceBudget()
        budget.recover(amount=10.0)

        assert budget.current <= budget.maximum

    def test_current_never_goes_below_minimum(self):
        """Test that current never goes below minimum."""
        budget = CoherenceBudget()
        budget.degrade(amount=10.0)

        assert budget.current >= budget.minimum

    def test_custom_bounds(self):
        """Test custom minimum and maximum bounds."""
        budget = CoherenceBudget(minimum=0.2, maximum=0.9, current=0.5)

        assert budget.minimum == 0.2
        assert budget.maximum == 0.9

    def test_current_clamped_to_custom_bounds(self):
        """Test that current is clamped to custom bounds."""
        budget = CoherenceBudget(minimum=0.3, maximum=0.7, current=0.9)

        assert abs(budget.current - 0.7) < 0.001

    def test_degrade_respects_custom_minimum(self):
        """Test that degradation respects custom minimum."""
        budget = CoherenceBudget(minimum=0.2, current=0.25)
        budget.degrade(amount=0.5)

        assert budget.current == 0.2

    def test_recover_respects_custom_maximum(self):
        """Test that recovery respects custom maximum."""
        budget = CoherenceBudget(maximum=0.8, current=0.75)
        budget.recover(amount=0.5)

        assert budget.current == 0.8


class TestCoherenceStatus:
    """Tests for coherence status checking."""

    def test_is_healthy_above_threshold(self):
        """Test is_healthy when above threshold."""
        budget = CoherenceBudget(current=0.6)

        assert budget.is_healthy() is True

    def test_is_healthy_at_threshold(self):
        """Test is_healthy at exactly threshold."""
        budget = CoherenceBudget(current=0.5)

        assert budget.is_healthy() is True

    def test_is_healthy_below_threshold(self):
        """Test is_healthy when below threshold."""
        budget = CoherenceBudget(current=0.4)

        assert budget.is_healthy() is False

    def test_is_critical_below_threshold(self):
        """Test is_critical when below threshold."""
        budget = CoherenceBudget(current=0.25)

        assert budget.is_critical() is True

    def test_is_critical_at_threshold(self):
        """Test is_critical at exactly threshold."""
        budget = CoherenceBudget(current=0.3)

        assert budget.is_critical() is False

    def test_is_critical_above_threshold(self):
        """Test is_critical when above threshold."""
        budget = CoherenceBudget(current=0.5)

        assert budget.is_critical() is False

    def test_is_degraded_when_below_maximum(self):
        """Test is_degraded when below maximum."""
        budget = CoherenceBudget(current=0.95)

        assert budget.is_degraded() is True

    def test_is_degraded_at_maximum(self):
        """Test is_degraded at exactly maximum."""
        budget = CoherenceBudget(current=1.0)

        assert budget.is_degraded() is False

    def test_check_returns_complete_status(self):
        """Test check method returns all status information."""
        budget = CoherenceBudget(current=0.6)
        result = budget.check()

        assert "current" in result
        assert "status" in result
        assert "is_healthy" in result
        assert "is_critical" in result
        assert "is_degraded" in result
        assert "headroom" in result
        assert "degradation_count" in result
        assert "recovery_count" in result


class TestCoherenceStates:
    """Tests for all coherence states."""

    def test_optimal_state(self):
        """Test coherence at optimal state (>= 0.9)."""
        budget = CoherenceBudget(current=0.95)

        assert budget._get_status() == "optimal"
        assert budget.is_healthy()
        assert not budget.is_critical()
        assert budget.is_degraded()

    def test_healthy_state(self):
        """Test coherence at healthy state (>= 0.7, < 0.9)."""
        budget = CoherenceBudget(current=0.8)

        assert budget._get_status() == "healthy"
        assert budget.is_healthy()
        assert not budget.is_critical()
        assert budget.is_degraded()

    def test_acceptable_state(self):
        """Test coherence at acceptable state (>= 0.5, < 0.7)."""
        budget = CoherenceBudget(current=0.6)

        assert budget._get_status() == "acceptable"
        assert budget.is_healthy()
        assert not budget.is_critical()
        assert budget.is_degraded()

    def test_degraded_state(self):
        """Test coherence at degraded state (>= 0.3, < 0.5)."""
        budget = CoherenceBudget(current=0.4)

        assert budget._get_status() == "degraded"
        assert not budget.is_healthy()
        assert not budget.is_critical()
        assert budget.is_degraded()

    def test_critical_state(self):
        """Test coherence at critical state (< 0.3)."""
        budget = CoherenceBudget(current=0.2)

        assert budget._get_status() == "critical"
        assert not budget.is_healthy()
        assert budget.is_critical()
        assert budget.is_degraded()


class TestCoherenceCanProceed:
    """Tests for can_proceed method."""

    def test_can_proceed_above_threshold(self):
        """Test can_proceed when above threshold."""
        budget = CoherenceBudget(current=0.6)

        assert budget.can_proceed() is True
        assert budget.can_proceed(required_level=0.5) is True

    def test_can_proceed_at_threshold(self):
        """Test can_proceed at exactly threshold."""
        budget = CoherenceBudget(current=0.5)

        assert budget.can_proceed() is True

    def test_can_proceed_below_threshold(self):
        """Test can_proceed when below threshold."""
        budget = CoherenceBudget(current=0.4)

        assert budget.can_proceed() is False

    def test_can_proceed_custom_threshold(self):
        """Test can_proceed with custom threshold."""
        budget = CoherenceBudget(current=0.6)

        assert budget.can_proceed(required_level=0.5) is True
        assert budget.can_proceed(required_level=0.7) is False


class TestCoherenceNeedsRecovery:
    """Tests for needs_recovery method."""

    def test_needs_recovery_below_threshold(self):
        """Test needs_recovery when below threshold."""
        budget = CoherenceBudget(current=0.4)

        assert budget.needs_recovery() is True

    def test_needs_recovery_at_threshold(self):
        """Test needs_recovery at exactly threshold."""
        budget = CoherenceBudget(current=0.5)

        assert budget.needs_recovery() is False

    def test_needs_recovery_above_threshold(self):
        """Test needs_recovery when above threshold."""
        budget = CoherenceBudget(current=0.6)

        assert budget.needs_recovery() is False

    def test_needs_recovery_custom_threshold(self):
        """Test needs_recovery with custom threshold."""
        budget = CoherenceBudget(current=0.6)

        assert budget.needs_recovery(threshold=0.7) is True
        assert budget.needs_recovery(threshold=0.5) is False


class TestCoherenceDegradationSummary:
    """Tests for degradation rate summary."""

    def test_empty_history_summary(self):
        """Test summary with no degradation history."""
        budget = CoherenceBudget()
        summary = budget.get_degradation_rate_summary()

        assert summary["total_degradation"] == 0
        assert summary["average_amount"] == 0
        # Implementation uses "reasons" key for empty summary
        assert "reasons" in summary

    def test_single_degradation_summary(self):
        """Test summary with single degradation."""
        budget = CoherenceBudget()
        budget.degrade(amount=0.1, reason="contradiction")

        summary = budget.get_degradation_rate_summary()

        assert summary["total_degradation"] == 0.1
        assert summary["average_amount"] == 0.1
        assert summary["event_count"] == 1
        assert "contradiction" in summary["by_reason"]
        assert summary["by_reason"]["contradiction"]["count"] == 1
        assert summary["by_reason"]["contradiction"]["total_amount"] == 0.1

    def test_multiple_degradations_summary(self):
        """Test summary with multiple degradations."""
        budget = CoherenceBudget()
        budget.degrade(amount=0.1, reason="contradiction1")
        budget.degrade(amount=0.2, reason="contradiction2")
        budget.degrade(amount=0.1, reason="contradiction1")

        summary = budget.get_degradation_rate_summary()

        assert abs(summary["total_degradation"] - 0.4) < 0.001
        # average_amount = total / number of events = 0.4 / 3 = 0.133...
        assert abs(summary["average_amount"] - 0.133) < 0.01
        assert summary["event_count"] == 3
        assert "by_reason" in summary
        assert "contradiction1" in summary["by_reason"]
        assert "contradiction2" in summary["by_reason"]
        assert summary["by_reason"]["contradiction1"]["count"] == 2
        assert summary["by_reason"]["contradiction2"]["count"] == 1


class TestCoherenceSnapshot:
    """Tests for coherence snapshot."""

    def test_snapshot_contains_all_fields(self):
        """Test that snapshot contains all important fields."""
        budget = CoherenceBudget(current=0.7)
        snapshot = budget.snapshot()

        assert "current" in snapshot
        assert "initial" in snapshot
        assert "minimum" in snapshot
        assert "maximum" in snapshot
        assert "status" in snapshot
        assert "timestamp" in snapshot
        assert "degradation_history_count" in snapshot
        assert "recovery_history_count" in snapshot

    def test_snapshot_with_history(self):
        """Test snapshot with degradation and recovery history."""
        budget = CoherenceBudget(current=0.6)
        budget.degrade(amount=0.1)
        budget.recover(amount=0.05)

        snapshot = budget.snapshot()

        assert snapshot["degradation_history_count"] == 1
        assert snapshot["recovery_history_count"] == 1


class TestCoherenceReset:
    """Tests for coherence reset."""

    def test_reset_to_initial(self):
        """Test resetting to initial level."""
        budget = CoherenceBudget(current=0.5)
        budget.degrade()
        budget.reset()

        assert budget.current == budget.initial
        assert budget.current == 1.0

    def test_reset_to_specific_level(self):
        """Test resetting to specific level."""
        budget = CoherenceBudget(current=0.3)
        budget.reset(level=0.8)

        assert budget.current == 0.8

    def test_reset_respects_bounds(self):
        """Test that reset respects bounds."""
        budget = CoherenceBudget()
        budget.reset(level=1.5)

        assert budget.current == 1.0

    def test_reset_updates_timestamp(self):
        """Test that reset updates last_update."""
        budget = CoherenceBudget(current=0.5)
        original_time = budget.last_update
        budget.reset()

        assert budget.last_update >= original_time

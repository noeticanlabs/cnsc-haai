"""
Tests for Evidence Filters.

Verifies cross-scenario filtering and taint handling.
"""

import pytest
import sys

sys.path.insert(0, "/workspaces/cnsc-haai/src")

from npe.retrieval.filters import (
    apply_filters,
    scenario_scope_filter,
    time_scope_filter,
    privacy_scope_filter,
    trust_scope_filter,
    taint_filter,
)


class TestScenarioScopeFilter:
    """Tests for scenario scope filtering."""

    def test_cross_scenario_evidence_filtered(self):
        """Evidence from different scenario is filtered out."""
        evidence = [
            {"evidence_id": "e1", "scope": {"scenario_id": "scenario_A"}},
            {"evidence_id": "e2", "scope": {"scenario_id": "scenario_B"}},
            {"evidence_id": "e3", "scope": {}},
        ]

        filtered = scenario_scope_filter(evidence, "scenario_A")

        # e1 should be kept (same scenario)
        # e2 should be filtered (different scenario)
        # e3 should be kept (no scenario = universal)
        assert len(filtered) == 2
        evidence_ids = [e["evidence_id"] for e in filtered]
        assert "e1" in evidence_ids
        assert "e3" in evidence_ids
        assert "e2" not in evidence_ids

    def test_filter_adds_applied_tag(self):
        """Filter adds 'filters_applied' tag to filtered items."""
        evidence = [
            {"evidence_id": "e1", "scope": {"scenario_id": "scenario_A"}},
            {"evidence_id": "e2", "scope": {}},
        ]

        filtered = scenario_scope_filter(evidence, "scenario_B")

        for item in filtered:
            assert "scenario_scope" in item.get("filters_applied", [])

    def test_no_scenario_evidence_included(self):
        """Evidence without scenario is considered universal."""
        evidence = [
            {"evidence_id": "e1", "scope": {}},
            {"evidence_id": "e2", "scope": {"scenario_id": "scenario_Y"}},
        ]

        filtered = scenario_scope_filter(evidence, "scenario_Y")

        # Both should be included (e1 is universal, e2 matches scenario_Y)
        assert len(filtered) == 2


class TestTimeScopeFilter:
    """Tests for time scope filtering."""

    def test_filter_by_time_bounds(self):
        """Filter evidence by time bounds."""
        evidence = [
            {"evidence_id": "e1", "scope": {"timestamp": 1000}},
            {"evidence_id": "e2", "scope": {"timestamp": 2000}},
            {"evidence_id": "e3", "scope": {"timestamp": 3000}},
            {"evidence_id": "e4", "scope": {}},
        ]

        time_scope = {"after": 1500, "before": 3500}
        filtered = time_scope_filter(evidence, time_scope)

        # e1: 1000 < after, should be filtered
        # e2: 1500 < 2000 < 3500, should be kept
        # e3: 2000 < 3000 < 3500, should be kept
        # e4: no timestamp, should be kept
        assert len(filtered) == 3
        evidence_ids = [e["evidence_id"] for e in filtered]
        assert "e2" in evidence_ids
        assert "e3" in evidence_ids
        assert "e4" in evidence_ids
        assert "e1" not in evidence_ids

    def test_only_after_filter(self):
        """Filter with only 'after' bound."""
        evidence = [
            {"evidence_id": "e1", "scope": {"timestamp": 1000}},
            {"evidence_id": "e2", "scope": {"timestamp": 2000}},
        ]

        time_scope = {"after": 1500}
        filtered = time_scope_filter(evidence, time_scope)

        assert len(filtered) == 1
        assert filtered[0]["evidence_id"] == "e2"

    def test_only_before_filter(self):
        """Filter with only 'before' bound."""
        evidence = [
            {"evidence_id": "e1", "scope": {"timestamp": 1000}},
            {"evidence_id": "e2", "scope": {"timestamp": 2000}},
        ]

        time_scope = {"before": 1500}
        filtered = time_scope_filter(evidence, time_scope)

        assert len(filtered) == 1
        assert filtered[0]["evidence_id"] == "e1"

    def test_empty_time_scope_returns_all(self):
        """Empty time scope returns all evidence."""
        evidence = [
            {"evidence_id": "e1", "scope": {"timestamp": 1000}},
            {"evidence_id": "e2", "scope": {"timestamp": 2000}},
        ]

        filtered = time_scope_filter(evidence, {})

        assert len(filtered) == 2


class TestPrivacyScopeFilter:
    """Tests for privacy scope filtering."""

    def test_privacy_tags_filtered(self):
        """Evidence with non-matching privacy tags is filtered."""
        evidence = [
            {"evidence_id": "e1", "taint_tags": ["privacy:internal"]},
            {"evidence_id": "e2", "taint_tags": ["privacy:public"]},
            {"evidence_id": "e3", "taint_tags": ["privacy:confidential"]},
        ]

        policy_tags = ["privacy:internal", "privacy:public"]
        filtered = privacy_scope_filter(evidence, policy_tags)

        # e1 and e2 should be kept, e3 filtered
        assert len(filtered) == 2
        evidence_ids = [e["evidence_id"] for e in filtered]
        assert "e1" in evidence_ids
        assert "e2" in evidence_ids
        assert "e3" not in evidence_ids

    def test_no_policy_tags_allows_all(self):
        """No policy tags allows all evidence."""
        evidence = [
            {"evidence_id": "e1", "taint_tags": ["privacy:secret"]},
            {"evidence_id": "e2", "taint_tags": []},
        ]

        filtered = privacy_scope_filter(evidence, [])

        assert len(filtered) == 2

    def test_no_privacy_tags_included(self):
        """Evidence without privacy tags is included."""
        evidence = [
            {"evidence_id": "e1", "taint_tags": []},
            {"evidence_id": "e2", "taint_tags": ["other_tag"]},
        ]

        policy_tags = ["privacy:internal"]
        filtered = privacy_scope_filter(evidence, policy_tags)

        # Both should be included (no privacy tags means no restriction)
        assert len(filtered) == 2


class TestTrustScopeFilter:
    """Tests for trust scope filtering."""

    def test_filter_by_source_type(self):
        """Filter evidence by source type."""
        evidence = [
            {"evidence_id": "e1", "source_type": "corpus"},
            {"evidence_id": "e2", "source_type": "receipt"},
            {"evidence_id": "e3", "source_type": "codebook"},
        ]

        allowed_sources = ["corpus", "codebook"]
        filtered = trust_scope_filter(evidence, allowed_sources)

        assert len(filtered) == 2
        evidence_ids = [e["evidence_id"] for e in filtered]
        assert "e1" in evidence_ids
        assert "e3" in evidence_ids
        assert "e2" not in evidence_ids

    def test_no_allowed_sources_returns_all(self):
        """No allowed sources returns all evidence."""
        evidence = [
            {"evidence_id": "e1", "source_type": "corpus"},
            {"evidence_id": "e2", "source_type": "receipt"},
        ]

        filtered = trust_scope_filter(evidence, [])

        assert len(filtered) == 2


class TestTaintFilter:
    """Tests for taint tag filtering."""

    def test_exclude_by_taint_tag(self):
        """Evidence with excluded taint tags is filtered."""
        evidence = [
            {"evidence_id": "e1", "taint_tags": ["taint:malicious"]},
            {"evidence_id": "e2", "taint_tags": []},
            {"evidence_id": "e3", "taint_tags": ["taint:suspicious"]},
        ]

        exclude_tags = ["taint:malicious", "taint:suspicious"]
        filtered = taint_filter(evidence, exclude_tags)

        assert len(filtered) == 1
        assert filtered[0]["evidence_id"] == "e2"

    def test_no_exclude_tags_returns_all(self):
        """No exclude tags returns all evidence."""
        evidence = [
            {"evidence_id": "e1", "taint_tags": ["taint:bad"]},
            {"evidence_id": "e2", "taint_tags": ["taint:worst"]},
        ]

        filtered = taint_filter(evidence, None)

        assert len(filtered) == 2


class TestApplyFilters:
    """Tests for the combined apply_filters function."""

    def test_all_filters_applied(self):
        """All applicable filters are applied."""
        evidence = [
            {
                "evidence_id": "e1",
                "scope": {"scenario_id": "s1", "timestamp": 2000},
                "source_type": "corpus",
                "taint_tags": [],
            },
            {
                "evidence_id": "e2",
                "scope": {"scenario_id": "s2", "timestamp": 1000},
                "source_type": "receipt",
                "taint_tags": ["privacy:secret"],
            },
        ]

        context = {
            "context": {
                "scenario_id": "s1",
                "time_scope": {"after": 1500},
                "allowed_sources": ["corpus"],
                "policy_tags": ["privacy:public"],
            }
        }

        filtered = apply_filters(evidence, context)

        # e1 should pass all filters
        # e2 should fail: different scenario, before time bound, wrong source, privacy tag
        assert len(filtered) == 1
        assert filtered[0]["evidence_id"] == "e1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Pytest configuration for compliance tests.

This module provides shared fixtures and markers for the compliance test suite.

MARKERS:
- @pytest.mark.determinism: Tests that verify deterministic behavior
- @pytest.mark.contract: Tests that verify contract/invariant requirements  
- @pytest.mark.adversarial: Tests that verify adversarial resilience

Run specific marker tests:
    pytest -m determinism    # Run all determinism tests
    pytest -m contract       # Run all contract tests
    pytest -m adversarial    # Run all adversarial tests
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", 
        "determinism: tests that verify deterministic behavior requirements"
    )
    config.addinivalue_line(
        "markers",
        "contract: tests that verify contract/invariant requirements"
    )
    config.addinivalue_line(
        "markers", 
        "adversarial: tests that verify adversarial resilience"
    )


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on file location."""
    for item in items:
        # Add determinism marker to tests in gml/test_receipt_chain_hash.py
        if "test_receipt_chain_hash" in item.nodeid:
            item.add_marker(pytest.mark.determinism)
            item.add_marker(pytest.mark.contract)


# Shared fixtures
@pytest.fixture
def fixed_timestamp():
    """Provide a fixed timestamp for deterministic tests.
    
    Returns:
        datetime: A fixed epoch timestamp for reproducibility.
    """
    from datetime import datetime
    return datetime(2024, 1, 1, 0, 0, 0)


@pytest.fixture
def fixed_timestamp_iso():
    """Provide a fixed ISO timestamp string for deterministic tests.
    
    Returns:
        str: A fixed ISO timestamp string.
    """
    return "2024-01-01T00:00:00"

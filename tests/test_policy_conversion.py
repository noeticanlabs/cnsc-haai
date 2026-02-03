import pytest

from src.haai.governance import policy_engine
from src.haai.governance import cgl


def test_policy_engine_accepts_dict_policy():
    engine = policy_engine.PolicyEngine()

    legacy_policy = {
        "policy_id": "legacy_1",
        "name": "Legacy Policy",
        "description": "A legacy dict-shaped policy",
        "rules": [
            {
                "type": "constraint",
                "constraint": {
                    "type": "range",
                    "field": "memory_usage_mb",
                    "min": 0,
                    "max": 512
                }
            }
        ],
        "metadata": {"source": "test"}
    }

    # Should not raise
    engine.add_policy(legacy_policy)

    assert "legacy_1" in engine.policies


def test_policy_engine_accepts_cgl_policy_object():
    engine = policy_engine.PolicyEngine()

    cgl_policy = cgl.Policy(
        policy_id="cgl_1",
        name="CGL Policy",
        description="CGL object policy",
        rules=[
            {"type": "condition", "condition": {"field": "operation_type", "operator": "exists"}}
        ],
        constraints={},
        priority=1,
        created_at=__import__("datetime").datetime.now()
    )

    engine.add_policy(cgl_policy)
    assert "cgl_1" in engine.policies


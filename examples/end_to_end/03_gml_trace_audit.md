# Example 03: GML Trace and Audit

**Purpose**: Demonstrate GML trace collection and audit verification

---

## Overview

GML (Governance Metadata Language) provides trace, receipts, and replay verification for forensics.

---

## Collecting Trace

```python
from cnsc.haai.gml.trace import TraceManager, TraceLevel

# Create trace manager
manager = TraceManager()

# Start trace
manager.start_trace(episode_id="episode_001")

# Log events
manager.log_event(
    level=TraceLevel.INFO,
    event_type="gate_evaluation",
    message="Evidence gate passed",
    details={"threshold": 0.8, "actual": 0.9}
)

# End trace
trace = manager.end_trace()
```

---

## Auditing Trace

```python
from cnsc.haai.gml.replay import ReplayVerifier

# Create verifier
verifier = ReplayVerifier()

# Verify replay
result = verifier.verify(trace)

print(f"Replay valid: {result.is_valid}")
print(f"Deterministic: {result.is_deterministic}")
```

---

## Querying Trace

```python
# Query events
events = manager.query(
    level=TraceLevel.ERROR,
    event_type="gate_failure"
)

for event in events:
    print(f"{event.timestamp}: {event.message}")
```

---

## Running the Example

```bash
python -c "
from cnsc.haai.gml.trace import TraceManager, TraceLevel

manager = TraceManager()
manager.start_trace('test')
manager.log_event(TraceLevel.INFO, 'test', 'Hello')
trace = manager.end_trace()
print(f'Trace contains {len(trace.events)} events')
"
```

---

## Expected Output

```
Trace contains 2 events
```

---

## Related Documents

- [GML Goals and Run Truth](../../spec/gml/00_GML_Goals_and_Run_Truth.md)
- [Trace Model](../../spec/gml/01_Trace_Model.md)
- [Receipt Spec and Hash Chains](../../spec/gml/03_Receipt_Spec_and_Hash_Chains.md)

# GML Trace Audit (End-to-End)

**Layer:** GML (Governance Markup Language)  
**Purpose:** Demonstrates trace collection, receipt chain verification, replay, and audit queries

This walkthrough shows how to:
1. Collect execution traces with receipts
2. Verify receipt chain integrity
3. Perform replay verification
4. Execute audit queries

## Prerequisites

```python
from cnsc.haai.gml.trace import TraceManager, TraceEvent, TraceLevel, TraceQuery
from cnsc.haai.gml.receipts import ReceiptSystem, Receipt, ReceiptStepType, ReceiptDecision
from cnsc.haai.gml.replay import ReplayVerifier, ReplayResult
```

## Step 1: Create Trace Manager

```python
# Create trace manager for collecting execution events
trace_manager = TraceManager(
    trace_id="audit-session-001",
    thread_id="main-thread",
)

print("✓ Trace manager created")
print(f"  Trace ID: {trace_manager.trace_id}")
print(f"  Thread ID: {trace_manager.thread_id}")
```

## Step 2: Simulate Execution with Trace Collection

```python
# Simulate an execution with various events
events = [
    ("vm_start", TraceLevel.INFO, "VM started execution"),
    ("load_constant", TraceLevel.DEBUG, "Loaded constant 42"),
    ("store_variable", TraceLevel.DEBUG, "Stored to variable x"),
    ("gate_check", TraceLevel.INFO, "Gate 'evidence_sufficiency' evaluated"),
    ("gate_pass", TraceLevel.INFO, "Gate passed with value 0.95"),
    ("branch_taken", TraceLevel.INFO, "Branching to true path"),
    ("return_value", TraceLevel.DEBUG, "Preparing return value"),
    ("vm_complete", TraceLevel.INFO, "VM execution complete"),
]

print("=" * 60)
print("Simulating Execution with Trace Collection")
print("=" * 60)

for event_type, level, message in events:
    event = trace_manager.log_event(
        level=level,
        event_type=event_type,
        message=message,
        details={"source": "nsc-vm"},
    )
    print(f"  [{level.to_string()}] {event.event_id}: {message}")

print(f"\n✓ Collected {trace_manager.get_event_count()} events")
```

**Output:**
```
============================================================
Simulating Execution with Trace Collection
============================================================
  [INFO] evt-001: VM started execution
  [DEBUG] evt-002: Loaded constant 42
  [DEBUG] evt-003: Stored to variable x
  [INFO] evt-004: Gate 'evidence_sufficiency' evaluated
  [INFO] evt-005: Gate passed with value 0.95
  [INFO] evt-006: Branching to true path
  [DEBUG] evt-007: Preparing return value
  [INFO] evt-008: VM execution complete

✓ Collected 8 events
```

## Step 3: Create Receipt System with Chain

```python
# Create receipt system
receipts = ReceiptSystem(signing_key="audit-demo-key")

# Simulate execution with receipts
execution_steps = [
    (ReceiptStepType.PARSE, "ghll-parser", "Parsing GHLL source", "AST with 45 nodes"),
    (ReceiptStepType.TYPE_CHECK, "ghll-type-checker", "Type checking", "All types inferred"),
    (ReceiptStepType.VM_EXECUTION, "nsc-vm", "Executing bytecode", "Step 1: LOAD_CONST"),
    (ReceiptStepType.VM_EXECUTION, "nsc-vm", "Executing bytecode", "Step 2: STORE"),
    (ReceiptStepType.GATE_EVAL, "nsc-gates", "Evaluating evidence_sufficiency", "Decision: PASS (0.95)"),
    (ReceiptStepType.VM_EXECUTION, "nsc-vm", "Executing bytecode", "Step 3: GT"),
    (ReceiptStepType.PHASE_TRANSITION, "phaseloom", "Phase transition", "From execution to completion"),
    (ReceiptStepType.CHECKPOINT, "gml-audit", "Final checkpoint", "Execution complete"),
]

print("\n" + "=" * 60)
print("Creating Receipt Chain")
print("=" * 60)

for step_type, source, description, output in execution_steps:
    receipt = receipts.emit_receipt(
        step_type=step_type,
        source=source,
        input_data={"description": description},
        output_data={"result": output},
        decision=ReceiptDecision.PASS,
    )
    print(f"  {step_type.name}: {receipt.receipt_id}")

print(f"\n✓ Receipt chain created: {receipts.chain.get_length()} receipts")
```

## Step 4: Verify Receipt Chain

```python
# Get all receipts in order
all_receipts = list(receipts.receipts.values())

print("\n" + "=" * 60)
print("Verifying Receipt Chain")
print("=" * 60)

# Validate the chain
valid, message, details = receipts.validate_chain(all_receipts)

print(f"\nValidation result: {'✓ PASS' if valid else '✗ FAIL'}")
print(f"Message: {message}")
print(f"Details:")
print(f"  Chain length: {details['length']}")
print(f"  Valid receipts: {details['valid_count']}")
print(f"  Invalid receipts: {details['invalid_count']}")
print(f"  Chain breaks: {details['chain_breaks']}")
```

## Step 5: Replay Verification

```python
from cnsc.haai.gml.replay import ReplayVerifier, ReplayResult

# Create replay verifier
verifier = ReplayVerifier()

print("\n" + "=" * 60)
print("Replay Verification")
print("=" * 60)

# Simulate original and replay receipts
# In practice, these would come from different execution runs
original_receipts = all_receipts[:4]  # First 4 receipts
replay_receipts = all_receipts[:4]    # Same receipts (same execution)

print(f"\nOriginal execution: {len(original_receipts)} receipts")
print(f"Replay execution: {len(replay_receipts)} receipts")

# Verify replay
for i, (orig, replay) in enumerate(zip(original_receipts, replay_receipts)):
    match, msg = verifier.verify_replay_match(orig, replay)
    print(f"  Receipt {i+1}: {orig.receipt_id} vs {replay.receipt_id} -> {match}")
    
    if not match:
        print(f"    Mismatch: {msg}")

print(f"\n✓ Replay verification complete")
```

## Step 6: Execute Audit Queries

```python
from cnsc.haai.gml.trace import TraceQuery

# Create audit query
query = TraceQuery(trace_manager)

print("\n" + "=" * 60)
print("Audit Queries")
print("=" * 60)

# Query 1: All INFO level events
print("\n1. All INFO level events:")
info_events = query.filter_by_level(TraceLevel.INFO).execute()
for event in info_events:
    print(f"   [{event.timestamp.isoformat()}] {event.event_type}: {event.message}")

# Query 2: Events after a specific time
print("\n2. Events after gate_check:")
gate_time = None
for event in trace_manager.events:
    if event.event_type == "gate_check":
        gate_time = event.timestamp
        break

if gate_time:
    after_events = query.filter_after(gate_time).execute()
    for event in after_events:
        print(f"   [{event.event_type}] {event.message}")

# Query 3: Event count by level
print("\n3. Events by level:")
level_counts = {}
for event in trace_manager.events:
    level = event.level.to_string()
    level_counts[level] = level_counts.get(level, 0) + 1
for level, count in sorted(level_counts.items()):
    print(f"   {level}: {count}")

# Query 4: Trace timeline
print("\n4. Trace timeline:")
for event in trace_manager.events:
    coherence_before = event.coherence_before or 0.9
    coherence_after = event.coherence_after or 0.92
    print(f"   [{event.level.to_string()[0]}] {event.event_id[:8]} {event.event_type}")
    print(f"      Coherence: {coherence_before:.3f} -> {coherence_after:.3f}")
```

## Step 7: Generate Audit Report

```python
def generate_audit_report(trace_manager, receipts):
    """Generate a comprehensive audit report."""
    
    report = {
        "audit_id": f"audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "trace": {
            "trace_id": trace_manager.trace_id,
            "thread_id": trace_manager.thread_id,
            "event_count": trace_manager.get_event_count(),
            "events_by_level": {},
        },
        "receipts": {
            "chain_length": receipts.chain.get_length(),
            "total_receipts": len(receipts.receipts),
            "validation": {},
        },
        "findings": [],
        "recommendations": [],
    }
    
    # Count events by level
    for event in trace_manager.events:
        level = event.level.to_string()
        report["trace"]["events_by_level"][level] = report["trace"]["events_by_level"].get(level, 0) + 1
    
    # Validate receipts
    all_receipts = list(receipts.receipts.values())
    valid, message, details = receipts.validate_chain(all_receipts)
    report["receipts"]["validation"] = {
        "valid": valid,
        "message": message,
        "details": details,
    }
    
    # Generate findings
    if details.get("chain_breaks", 0) > 0:
        report["findings"].append({
            "severity": "HIGH",
            "issue": "Receipt chain breaks detected",
            "description": f"{details['chain_breaks']} chain breaks found",
        })
    
    # Check coherence
    coherence_events = [e for e in trace_manager.events if e.coherence_after is not None]
    if coherence_events:
        final_coherence = coherence_events[-1].coherence_after
        if final_coherence < 0.7:
            report["findings"].append({
                "severity": "MEDIUM",
                "issue": "Low final coherence score",
                "description": f"Final coherence: {final_coherence:.3f}",
            })
    
    # Generate recommendations
    if not valid:
        report["recommendations"].append("Review receipt chain for integrity issues")
    
    if coherence_events and coherence_events[-1].coherence_after < 0.8:
        report["recommendations"].append("Consider improving coherence before finalizing")
    
    return report

# Generate report
report = generate_audit_report(trace_manager, receipts)

print("\n" + "=" * 60)
print("Audit Report")
print("=" * 60)

print(f"\nAudit ID: {report['audit_id']}")
print(f"Timestamp: {report['timestamp']}")

print(f"\nTrace Summary:")
print(f"  Events: {report['trace']['event_count']}")
for level, count in report['trace']['events_by_level'].items():
    print(f"    {level}: {count}")

print(f"\nReceipt Chain:")
print(f"  Chain length: {report['receipts']['chain_length']}")
print(f"  Valid: {report['receipts']['validation']['valid']}")

if report['findings']:
    print(f"\nFindings:")
    for finding in report['findings']:
        print(f"  [{finding['severity']}] {finding['issue']}")
        print(f"    {finding['description']}")

if report['recommendations']:
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")
```

## Full Example Script

```python
#!/usr/bin/env python3
"""
GML Trace Audit End-to-End Example

Demonstrates:
1. Trace collection and management
2. Receipt chain creation and verification
3. Replay verification
4. Audit queries
5. Audit report generation
"""

from datetime import datetime
from cnsc.haai.gml.trace import TraceManager, TraceEvent, TraceLevel, TraceQuery
from cnsc.haai.gml.receipts import ReceiptSystem, ReceiptStepType, ReceiptDecision
from cnsc.haai.gml.replay import ReplayVerifier

def main():
    print("=" * 60)
    print("GML Trace Audit - End-to-End Example")
    print("=" * 60)
    
    # Step 1: Create trace manager
    print("\nStep 1: Creating Trace Manager")
    trace_manager = TraceManager(
        trace_id="audit-session-2024-001",
        thread_id="main-thread",
    )
    print(f"✓ Created: {trace_manager.trace_id}")
    
    # Step 2: Collect execution trace
    print("\nStep 2: Collecting Execution Trace")
    
    execution_events = [
        ("vm_start", TraceLevel.INFO, "VM started"),
        ("parse_start", TraceLevel.INFO, "Starting parse"),
        ("parse_complete", TraceLevel.INFO, "Parse complete", {"nodes": 45}),
        ("type_check_start", TraceLevel.INFO, "Starting type check"),
        ("type_check_complete", TraceLevel.INFO, "Type check complete", {"inferred": 12}),
        ("compile_start", TraceLevel.INFO, "Starting compilation"),
        ("compile_complete", TraceLevel.INFO, "Compilation complete", {"bytecode": 128}),
        ("gate_init", TraceLevel.INFO, "Initializing gates"),
        ("gate_eval", TraceLevel.INFO, "Evaluating evidence_sufficiency", {"value": 0.95}),
        ("execution_start", TraceLevel.INFO, "Starting execution"),
        ("execution_step", TraceLevel.DEBUG, "Step 1: LOAD_CONST"),
        ("execution_step", TraceLevel.DEBUG, "Step 2: STORE"),
        ("execution_step", TraceLevel.DEBUG, "Step 3: GT"),
        ("execution_complete", TraceLevel.INFO, "Execution complete", {"result": 1}),
        ("audit_complete", TraceLevel.INFO, "Audit complete"),
    ]
    
    for event_type, level, message, *details in execution_events:
        event = trace_manager.log_event(
            level=level,
            event_type=event_type,
            message=message,
            details=details[0] if details else {},
        )
        # Add coherence values for demonstration
        event.coherence_before = 0.90
        event.coherence_after = 0.92
    
    print(f"✓ Collected {trace_manager.get_event_count()} events")
    
    # Step 3: Create receipt chain
    print("\nStep 3: Creating Receipt Chain")
    
    receipts = ReceiptSystem(signing_key="audit-demo-key")
    
    steps = [
        (ReceiptStepType.PARSE, "ghll-parser", "GHLL parsing"),
        (ReceiptStepType.TYPE_CHECK, "ghll-type-checker", "Type checking"),
        (ReceiptStepType.CHECKPOINT, "ghll-compiler", "Compilation"),
        (ReceiptStepType.GATE_EVAL, "nsc-gates", "Gate evaluation"),
        (ReceiptStepType.VM_EXECUTION, "nsc-vm", "VM execution"),
        (ReceiptStepType.CHECKPOINT, "gml-audit", "Audit checkpoint"),
    ]
    
    for step_type, source, description in steps:
        receipts.emit_receipt(
            step_type=step_type,
            source=source,
            input_data={"description": description},
            output_data={"status": "complete"},
            decision=ReceiptDecision.PASS,
        )
    
    print(f"✓ Created chain with {receipts.chain.get_length()} receipts")
    
    # Step 4: Verify chain
    print("\nStep 4: Verifying Receipt Chain")
    
    all_receipts = list(receipts.receipts.values())
    valid, message, details = receipts.validate_chain(all_receipts)
    
    print(f"  Valid: {valid}")
    print(f"  Message: {message}")
    print(f"  Chain length: {details['length']}")
    
    # Step 5: Replay verification
    print("\nStep 5: Replay Verification")
    
    verifier = ReplayVerifier()
    
    # Simulate replay (using same receipts for demo)
    replay_results = []
    for orig, replay in zip(all_receipts, all_receipts):
        match, msg = verifier.verify_replay_match(orig, replay)
        replay_results.append({"receipt": orig.receipt_id, "match": match, "message": msg})
    
    all_match = all(r["match"] for r in replay_results)
    print(f"  All receipts match: {all_match}")
    
    # Step 6: Audit queries
    print("\nStep 6: Audit Queries")
    
    query = TraceQuery(trace_manager)
    
    # Query by level
    info_count = len(query.filter_by_level(TraceLevel.INFO).execute())
    debug_count = len(query.filter_by_level(TraceLevel.DEBUG).execute())
    print(f"  INFO events: {info_count}")
    print(f"  DEBUG events: {debug_count}")
    
    # Query by event type
    exec_events = query.filter_by_type("execution_*").execute()
    print(f"  Execution events: {len(exec_events)}")
    
    # Step 7: Generate report
    print("\nStep 7: Generating Audit Report")
    
    report = {
        "audit_id": f"audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "trace_summary": {
            "event_count": trace_manager.get_event_count(),
            "thread_id": trace_manager.thread_id,
        },
        "receipt_summary": {
            "chain_length": receipts.chain.get_length(),
            "chain_valid": valid,
        },
        "replay_results": {
            "all_match": all_match,
            "total_receipts": len(replay_results),
        },
    }
    
    print(f"  Audit ID: {report['audit_id']}")
    print(f"  Trace events: {report['trace_summary']['event_count']}")
    print(f"  Receipt chain: {report['receipt_summary']['chain_length']} (valid: {report['receipt_summary']['chain_valid']})")
    print(f"  Replay: {'PASS' if report['replay_results']['all_match'] else 'FAIL'}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if valid and all_match:
        print("✓ Audit PASSED - All checks successful")
    else:
        print("✗ Audit FAILED - Issues detected")
        
        if not valid:
            print("  - Receipt chain invalid")
        if not all_match:
            print("  - Replay mismatch detected")

if __name__ == "__main__":
    main()
```

## Expected Output

```
============================================================
GML Trace Audit - End-to-End Example
============================================================

Step 1: Creating Trace Manager
✓ Created: audit-session-2024-001

Step 2: Collecting Execution Trace
✓ Collected 15 events

Step 3: Creating Receipt Chain
✓ Created chain with 6 receipts

Step 4: Verifying Receipt Chain
  Valid: True
  Message: Chain valid
  Chain length: 6

Step 5: Replay Verification
  All receipts match: True

Step 6: Audit Queries
  INFO events: 11
  DEBUG events: 4
  Execution events: 5

Step 7: Generating Audit Report
  Audit ID: audit-20240207-181500
  Trace events: 15
  Receipt chain: 6 (valid: True)
  Replay: PASS

============================================================
Summary
============================================================
✓ Audit PASSED - All checks successful
```

## See Also

- **GML Spec:** [`spec/gml/`](../../spec/gml/)
- **Trace Implementation:** [`src/cnsc/haai/gml/trace.py`](../../src/cnsc/haai/gml/trace.py)
- **Receipt Implementation:** [`src/cnsc/haai/gml/receipts.py`](../../src/cnsc/haai/gml/receipts.py)
- **Replay Implementation:** [`src/cnsc/haai/gml/replay.py`](../../src/cnsc/haai/gml/replay.py)
- **Receipt Schema:** [`schemas/receipt.schema.json`](../../schemas/receipt.schema.json)

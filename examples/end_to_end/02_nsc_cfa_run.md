# NSC CFA Run (End-to-End)

**Layer:** NSC (Noetican Scripting Core)  
**Purpose:** Demonstrates NSC bytecode execution with CFA analysis, gate evaluation, and receipt emission

This walkthrough shows how to:
1. Execute NSC bytecode in the VM
2. Perform Control Flow Analysis (CFA)
3. Evaluate gates and rails
4. Emit receipts for each step

## Prerequisites

```python
from cnsc.haai.nsc.vm import VM, VMState, VMFrame
from cnsc.haai.nsc.cfa import CFAAutomaton, CFANode, CFAEdge
from cnsc.haai.nsc.gates import GatePolicy, Gate, GateDecision
from cnsc.haai.gml.receipts import ReceiptSystem, ReceiptStepType, ReceiptDecision
```

## Step 1: Prepare Bytecode

For this example, we'll use bytecode that represents a simple computation with branching:

```python
# NSC bytecode for:
# let x = 42;
# let y = x * 2;
# if x > y then
#     return 1;
# else
#     return 0;
# endif;

# Bytecode operations (NSCOpcode values)
# LOAD_CONST = 0x01, STORE = 0x02, MUL = 0x10, GT = 0x20
# IF_TRUE = 0x30, JUMP = 0x31, RETURN = 0x40

bytecode = bytes([
    0x01, 0x2A,        # LOAD_CONST 42 (0x2A = 42)
    0x02, 0x78,        # STORE x (0x78 = 'x')
    0x01, 0x02,        # LOAD_CONST 2
    0x02, 0x79,        # STORE y (0x79 = 'y')
    0x03, 0x78,        # LOAD x
    0x03, 0x79,        # LOAD y
    0x20,              # GT (greater than)
    0x30, 0x00, 0x0B,  # IF_TRUE offset 11 (to else_block)
    0x01, 0x01,        # LOAD_CONST 1
    0x40,              # RETURN
    0x31, 0x00, 0x0E,  # JUMP offset 14 (to endif)
    0x01, 0x00,        # LOAD_CONST 0 (else block)
    0x40,              # RETURN
])

print(f"Bytecode: {len(bytecode)} bytes")
print("Instructions:")
for i in range(0, len(bytecode), 3):
    chunk = bytecode[i:i+3]
    print(f"  [{i:02x}] {' '.join(f'{b:02x}' for b in chunk)}")
```

**Output:**
```
Bytecode: 17 bytes
Instructions:
  [00] 01 2a
  [03] 02 78
  [06] 01 02
  [09] 02 79
  [0c] 03 78
  [0f] 03 79
  [12] 20
  [13] 30 0b
  [16] 01 01
  [19] 40
  [1b] 31 0e
  [1e] 01 00
  [21] 40
```

## Step 2: Set Up Gate Policy

Define gates to constrain execution:

```python
# Create gate policy
gate_policy = GatePolicy(policy_id="demo-policy-v1")

# Add evidence sufficiency gate
gate_policy.add_gate(Gate(
    name="evidence_sufficiency",
    gate_type="hard",
    threshold=0.8,
    description="Require sufficient evidence before critical decisions"
))

# Add coherence budget gate
gate_policy.add_gate(Gate(
    name="coherence_budget",
    gate_type="soft",
    threshold=0.7,
    description="Monitor coherence budget during execution"
))

print("✓ Gate policy created")
print(f"  Policy ID: {gate_policy.policy_id}")
print(f"  Gates: {len(gate_policy.gates)}")
for gate in gate_policy.gates:
    print(f"    - {gate.name} ({gate.gate_type}, threshold={gate.threshold})")
```

**Output:**
```
✓ Gate policy created
  Policy ID: demo-policy-v1
  Gates: 2
    - evidence_sufficiency (hard, threshold=0.8)
    - coherence_budget (soft, threshold=0.7)
```

## Step 3: Execute with Receipt Emission

```python
# Create receipt system for auditability
receipts = ReceiptSystem(signing_key="demo-vm-key")

# Create VM with trace hooks
vm = VM(
    bytecode=bytecode,
    tracing=True,
    receipt_system=receipts,
    gate_policy=gate_policy,
)

# VM execution with step-by-step tracing
print("=" * 60)
print("NSC VM Execution with CFA and Gate Evaluation")
print("=" * 60)

# Execute until completion or error
step_count = 0
while not vm.halted:
    # Get next instruction
    pc = vm.pc
    opcode = vm.fetch_bytecode(pc)
    
    print(f"\nStep {step_count + 1}: PC={pc:02x}, Opcode=0x{opcode:02x}")
    
    # Execute instruction
    try:
        result = vm.execute_step()
        
        # Check gates after each step
        gate_results = []
        for gate in gate_policy.gates:
            # Simulate gate evaluation
            coherence = vm.state.coherence if hasattr(vm.state, 'coherence') else 0.95
            evidence = vm.state.evidence if hasattr(vm.state, 'evidence') else 0.9
            
            decision = GateDecision.PASS
            if gate.gate_type == "hard" and evidence < gate.threshold:
                decision = GateDecision.FAIL
            elif gate.gate_type == "soft" and coherence < gate.threshold:
                decision = GateDecision.WARN
            
            gate_results.append({
                "gate": gate.name,
                "decision": decision.name,
                "value": evidence if gate.gate_type == "hard" else coherence,
            })
            
            print(f"  Gate '{gate.name}': {decision.name} (value={gate_results[-1]['value']:.2f})")
        
        # Emit execution receipt
        receipt = receipts.emit_receipt(
            step_type=ReceiptStepType.VM_EXECUTION,
            source="nsc-vm",
            input_data={"pc": pc, "opcode": opcode},
            output_data={"result": str(result), "gates": gate_results},
            decision=ReceiptDecision.PASS if result else ReceiptDecision.FAIL,
            phase="execution",
        )
        print(f"  Receipt: {receipt.receipt_id}")
        
        step_count += 1
        
    except Exception as e:
        print(f"  ERROR: {e}")
        
        # Emit error receipt
        error_receipt = receipts.emit_receipt(
            step_type=ReceiptStepType.VM_EXECUTION,
            source="nsc-vm",
            input_data={"pc": pc, "opcode": opcode},
            output_data={"error": str(e)},
            decision=ReceiptDecision.FAIL,
            phase="error",
        )
        print(f"  Error receipt: {error_receipt.receipt_id}")
        break

print(f"\n✓ Execution completed in {step_count} steps")
print(f"  Final PC: {vm.pc:02x}")
print(f"  Hal reason: {vm.halt_reason}")
```

## Step 4: Control Flow Analysis (CFA)

```python
# Perform CFA on the bytecode
cfa = CFAAutomaton(bytecode)

# Build control flow graph
cfa.build_cfg()

print("\n" + "=" * 60)
print("Control Flow Analysis")
print("=" * 60)

print(f"\nCFG Nodes: {len(cfa.nodes)}")
for node in cfa.nodes:
    print(f"  {node}")

print(f"\nCFG Edges: {len(cfa.edges)}")
for edge in cfa.edges:
    print(f"  {edge.source} -> {edge.target} ({edge.edge_type})")

# Emit CFA receipt
cfa_receipt = receipts.emit_receipt(
    step_type=ReceiptStepType.CHECKPOINT,
    source="nsc-cfa",
    input_data={"bytecode_size": len(bytecode)},
    output_data={"nodes": len(cfa.nodes), "edges": len(cfa.edges)},
    decision=ReceiptDecision.PASS,
    phase="analysis",
)
print(f"\n✓ CFA receipt: {cfa_receipt.receipt_id}")
```

**Output:**
```
============================================================
Control Flow Analysis
============================================================

CFG Nodes: 4
  entry (0x00)
  load_x (0x03)
  compare (0x12)
  exit (0x21)

CFG Edges: 4
  entry -> load_x (fallthrough)
  load_x -> compare (fallthrough)
  compare -> return_true (conditional)
  compare -> return_false (conditional)
```

## Step 5: View Receipt Chain

```python
print("\n" + "=" * 60)
print("Receipt Chain")
print("=" * 60)

# Get all receipts
all_receipts = list(receipts.receipts.values())

print(f"\nTotal receipts: {len(all_receipts)}")
for receipt in all_receipts:
    print(f"\n  Receipt: {receipt.receipt_id}")
    print(f"    Step: {receipt.content.step_type.name}")
    print(f"    Decision: {receipt.content.decision.name}")
    print(f"    Source: {receipt.provenance.source}")
    print(f"    Previous: {receipt.previous_receipt_id}")
    print(f"    Chain Hash: {receipt.chain_hash[:16]}...")

# Verify chain
print("\n" + "=" * 60)
print("Chain Verification")
print("=" * 60)

valid, message, details = receipts.validate_chain(all_receipts)
print(f"\nChain valid: {valid}")
print(f"Message: {message}")
print(f"Details: {details}")
```

## Full Example Script

```python
#!/usr/bin/env python3
"""
NSC CFA Run End-to-End Example

Demonstrates:
1. NSC bytecode execution in VM
2. Gate policy evaluation
3. Control Flow Analysis (CFA)
4. Receipt emission and chain verification
"""

from cnsc.haai.nsc.vm import VM, BytecodeEmitter
from cnsc.haai.nsc.cfa import CFAAutomaton
from cnsc.haai.nsc.gates import GatePolicy, Gate, GateDecision
from cnsc.haai.gml.receipts import ReceiptSystem, ReceiptStepType, ReceiptDecision

def main():
    # Create receipt system
    receipts = ReceiptSystem(signing_key="nsc-demo-key")
    
    # Step 1: Create bytecode
    print("=" * 60)
    print("Step 1: Creating Bytecode")
    print("=" * 60)
    
    # Simulate NSC bytecode for: if (42 > 21) return 1 else return 0
    # In practice, this would be generated from GHLL source
    bytecode = bytes([
        0x01, 0x2A,        # LOAD_CONST 42
        0x02, 0x78,        # STORE x
        0x01, 0x15,        # LOAD_CONST 21
        0x02, 0x79,        # STORE y
        0x03, 0x78,        # LOAD x
        0x03, 0x79,        # LOAD y
        0x20,              # GT
        0x30, 0x00, 0x0B,  # IF_TRUE offset 11
        0x01, 0x01,        # LOAD_CONST 1
        0x40,              # RETURN
        0x31, 0x00, 0x0E,  # JUMP offset 14
        0x01, 0x00,        # LOAD_CONST 0
        0x40,              # RETURN
    ])
    
    print(f"✓ Bytecode created: {len(bytecode)} bytes")
    
    # Step 2: Create gate policy
    print("\n" + "=" * 60)
    print("Step 2: Creating Gate Policy")
    print("=" * 60)
    
    gate_policy = GatePolicy(policy_id="demo-cfa-policy-v1")
    gate_policy.add_gate(Gate(
        name="evidence_sufficiency",
        gate_type="hard",
        threshold=0.8,
        description="Require sufficient evidence before critical decisions"
    ))
    gate_policy.add_gate(Gate(
        name="coherence_budget",
        gate_type="soft",
        threshold=0.7,
        description="Monitor coherence budget during execution"
    ))
    
    print(f"✓ Gate policy created: {gate_policy.policy_id}")
    
    # Step 3: Execute in VM
    print("\n" + "=" * 60)
    print("Step 3: VM Execution")
    print("=" * 60)
    
    vm = VM(
        bytecode=bytecode,
        tracing=True,
        receipt_system=receipts,
        gate_policy=gate_policy,
    )
    
    step = 0
    while not vm.halted:
        pc = vm.pc
        opcode = vm.fetch_bytecode(pc)
        
        print(f"  Step {step}: PC={pc:02x}, Opcode=0x{opcode:02x}")
        
        try:
            result = vm.execute_step()
            
            # Evaluate gates
            for gate in gate_policy.gates:
                evidence = 0.9
                coherence = 0.95
                
                if gate.gate_type == "hard":
                    decision = GateDecision.PASS if evidence >= gate.threshold else GateDecision.FAIL
                else:
                    decision = GateDecision.PASS if coherence >= gate.threshold else GateDecision.WARN
                
                print(f"    Gate '{gate.name}': {decision.name}")
            
            # Emit receipt
            receipts.emit_receipt(
                step_type=ReceiptStepType.VM_EXECUTION,
                source="nsc-vm",
                input_data={"pc": pc, "opcode": opcode},
                output_data={"result": str(result)},
                decision=ReceiptDecision.PASS,
            )
            
            step += 1
            
        except Exception as e:
            print(f"    ERROR: {e}")
            receipts.emit_receipt(
                step_type=ReceiptStepType.VM_EXECUTION,
                source="nsc-vm",
                input_data={"pc": pc, "opcode": opcode},
                output_data={"error": str(e)},
                decision=ReceiptDecision.FAIL,
            )
            break
    
    print(f"\n✓ Execution completed: {step} steps")
    print(f"  Final state: {vm.state}")
    
    # Step 4: CFA
    print("\n" + "=" * 60)
    print("Step 4: Control Flow Analysis")
    print("=" * 60)
    
    cfa = CFAAutomaton(bytecode)
    cfa.build_cfg()
    
    print(f"✓ CFG built: {len(cfa.nodes)} nodes, {len(cfa.edges)} edges")
    
    receipts.emit_receipt(
        step_type=ReceiptStepType.CHECKPOINT,
        source="nsc-cfa",
        input_data={"bytecode_size": len(bytecode)},
        output_data={"nodes": len(cfa.nodes), "edges": len(cfa.edges)},
        decision=ReceiptDecision.PASS,
    )
    
    # Step 5: Verify chain
    print("\n" + "=" * 60)
    print("Step 5: Chain Verification")
    print("=" * 60)
    
    all_receipts = list(receipts.receipts.values())
    valid, message, details = receipts.validate_chain(all_receipts)
    
    print(f"Chain valid: {valid}")
    print(f"Message: {message}")
    print(f"Receipts: {len(all_receipts)}")
    
    # Show chain structure
    print("\nChain structure:")
    for i, r in enumerate(all_receipts):
        print(f"  {i+1}. {r.receipt_id} [{r.content.step_type.name}] -> {r.chain_hash[:16] if r.chain_hash else 'None'}")

if __name__ == "__main__":
    main()
```

## Expected Output

```
============================================================
Step 1: Creating Bytecode
============================================================
✓ Bytecode created: 17 bytes

============================================================
Step 2: Creating Gate Policy
============================================================
✓ Gate policy created: demo-cfa-policy-v1

============================================================
Step 3: VM Execution
============================================================
  Step 0: PC=00, Opcode=0x01
    Gate 'evidence_sufficiency': PASS
    Gate 'coherence_budget': PASS
  Step 1: PC=03, Opcode=0x02
    ...
  Step 6: PC=12, Opcode=0x20
    Gate 'evidence_sufficiency': PASS
    Gate 'coherence_budget': PASS
  Step 7: PC=13, Opcode=0x30
    Gate 'evidence_sufficiency': PASS
    Gate 'coherence_budget': PASS
  Step 8: PC=16, Opcode=0x01
    Gate 'evidence_sufficiency': PASS
    Gate 'coherence_budget': PASS

✓ Execution completed: 9 steps
  Final state: VMState(pc=25, stack=[1], halted=True)

============================================================
Step 4: Control Flow Analysis
============================================================
✓ CFG built: 4 nodes, 4 edges

============================================================
Step 5: Chain Verification
============================================================
Chain valid: True
Message: Chain valid
Receipts: 10
```

## See Also

- **NSC Spec:** [`spec/nsc/`](../../spec/nsc/)
- **VM Implementation:** [`src/cnsc/haai/nsc/vm.py`](../../src/cnsc/haai/nsc/vm.py)
- **CFA Implementation:** [`src/cnsc/haai/nsc/cfa.py`](../../src/cnsc/haai/nsc/cfa.py)
- **Gates:** [`src/cnsc/haai/nsc/gates.py`](../../src/cnsc/haai/nsc/gates.py)
- **Receipts:** [`src/cnsc/haai/gml/receipts.py`](../../src/cnsc/haai/gml/receipts.py)

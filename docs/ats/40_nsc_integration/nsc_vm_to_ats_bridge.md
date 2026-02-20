# NSC VM to ATS Bridge

**Bridging NSC Execution to ATS Verification**

| Field | Value |
|-------|-------|
| **Module** | 40_nsc_integration |
| **Section** | NSC VM to ATS Bridge |
| **Version** | 1.0.0 |

---

## 1. Overview

The NSC VM to ATS Bridge connects the Network Structured Code (NSC) virtual machine to the Admissible Trajectory Space kernel. Every NSC execution step must pass through this bridge for ATS verification.

---

## 2. Architecture

### 2.1 System Layers

```
┌─────────────────────────────────────────────┐
│            ATS Kernel                        │
│    (Receipt Verification, Budget Law)       │
└─────────────────────────────────────────────┘
                    ↑
                    │ Bridge
                    ↓
┌─────────────────────────────────────────────┐
│            NSC VM                           │
│    (Network Structured Code Execution)       │
└─────────────────────────────────────────────┘
```

### 2.2 Bridge Functions

| Function | Direction | Description |
|----------|-----------|-------------|
| **Emit** | NSC → ATS | Submit step for verification |
| **Verify** | ATS → NSC | Return ACCEPT/REJECT |
| **State Sync** | Bidirectional | Keep states synchronized |

---

## 3. Bridge Interface

### 3.1 NSC Step Emission

```python
def nsc_emit_step(
    vm_state: NSCState,
    action: NSCAction,
    budget: QFixed,
    kappa: QFixed
) -> (Receipt, Result):
    """
    Emit NSC step to ATS kernel for verification.
    
    Returns: (receipt, verification_result)
    """
    # 1. Capture pre-state
    state_before = vm_state.to_ats_state()
    hash_before = sha256(canonical_bytes(state_before))
    
    # 2. Execute action in NSC VM
    vm_state = vm_state.execute(action)
    
    # 3. Capture post-state
    state_after = vm_state.to_ats_state()
    hash_after = sha256(canonical_bytes(state_after))
    
    # 4. Compute risk
    risk_before = V(state_before)
    risk_after = V(state_after)
    delta = risk_after - risk_before
    
    # 5. Compute budget
    if delta > 0:
        budget_after = budget - kappa * delta
    else:
        budget_after = budget
    
    # 6. Create receipt
    receipt = Receipt(
        state_hash_before=hash_before,
        state_hash_after=hash_after,
        risk_before_q=str(risk_before),
        risk_after_q=str(risk_after),
        budget_before_q=str(budget),
        budget_after_q=str(budget_after),
        kappa_q=str(kappa),
        content={
            "step_type": "VM_EXECUTION",
            "action_type": action.type,
            "nsc_instruction": action.instruction
        }
    )
    
    # 7. Verify with ATS
    result = ats_kernel.verify(state_before, state_after, receipt, 
                                budget, budget_after, kappa)
    
    return receipt, result
```

---

## 4. State Translation

### 4.1 NSC State to ATS State

```python
def nsc_to_ats_state(nsc_state: NSCState) -> ATSState:
    """Convert NSC VM state to ATS state."""
    return ATSState(
        belief=nsc_state.belief_stack.to_dict(),
        memory=nsc_state.memory.to_list(),
        plan=nsc_state.program_counter_stack.to_list(),
        policy=nsc_state.policy_table.to_dict(),
        io=nsc_state.io_buffers.to_dict()
    )
```

### 4.2 ATS State to NSC State

```python
def ats_to_nsc_state(ats_state: ATSState) -> NSCState:
    """Convert ATS state to NSC VM state (for checkpointing)."""
    return NSCState(
        belief_stack=BeliefStack.from_dict(ats_state.belief),
        memory=Memory.from_list(ats_state.memory),
        program_counter_stack=PCStack.from_list(ats_state.plan),
        policy_table=PolicyTable.from_dict(ats_state.policy),
        io_buffers=IOBuffers.from_dict(ats_state.io)
    )
```

---

## 5. Action Translation

### 5.1 NSC Instructions to ATS Actions

```python
def nsc_instruction_to_ats_action(instruction: NSCInstruction) -> ATSAction:
    """Map NSC instruction to ATS action type."""
    mapping = {
        "BELIEF_PUSH": ATSAction.BELIEF_UPDATE,
        "BELIEF_POP": ATSAction.BELIEF_DELETE,
        "MEMORY_STORE": ATSAction.MEMORY_WRITE,
        "MEMORY_LOAD": ATSAction.MEMORY_READ,
        "PLAN_APPEND": ATSAction.PLAN_APPEND,
        "PLAN_EXECUTE": ATSAction.PLAN_REMOVE,
        "POLICY_UPDATE": ATSAction.POLICY_UPDATE,
        "IO_SEND": ATSAction.IO_OUTPUT,
        "IO_RECV": ATSAction.IO_INPUT,
    }
    return mapping.get(instruction.opcode, ATSAction.CUSTOM)
```

---

## 6. Verification Flow

### 6.1 Complete Flow

```
NSC VM                           ATS Kernel
   │                                  │
   │  1. Execute action              │
   │  2. Produce new state          │
   │  3. Compute risk claims        │
   │  4. Create receipt             │
   │─────────────────────────────►   │
   │                                  │
   │                            5. Verify receipt
   │                            6. Check budget law
   │                            7. Validate hashes
   │                                  │
   │  ◄────────────────────────────  │
   │     ACCEPT or REJECT            │
   │                                  │
   │  8. Update VM state (if ACCEPT)
```

---

## 7. Error Handling

### 7.1 Rejection Handling

```python
def handle_rejection(vm_state, receipt, rejection):
    """Handle ATS rejection."""
    if rejection.code == "BUDGET_VIOLATION":
        # Rollback to previous state
        vm_state.rollback()
        raise BudgetExhaustedError(rejection.reason)
    
    elif rejection.code == "STATE_HASH_MISMATCH":
        # NSC execution was non-deterministic
        vm_state.rollback()
        raise NonDeterministicError(rejection.reason)
    
    else:
        vm_state.rollback()
        raise VerificationError(rejection.reason)
```

---

## 8. References

- [ATS Definition](../00_identity/ats_definition.md)
- [Coh Kernel Scope](../00_identity/coh_kernel_scope.md)
- [Action Emission Contract](../30_ats_runtime/action_emission_contract.md)
- [Gate to Receipt Translation](./gate_to_receipt_translation.md)
- [NSC Specification](../spec/nsc/00_NSC_Goals_and_Invariants.md)

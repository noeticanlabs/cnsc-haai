# Cognitive System Embedding

**Hosting Dynamical Cognitive Systems in ATS**

| Field | Value |
|-------|-------|
| **Module** | 40_nsc_integration |
| **Section** | Cognitive System Embedding |
| **Version** | 1.0.0 |

---

## 1. Overview

A **dynamical cognitive system** is an NSC program running under ATS governance. This document defines how such systems are embedded in the ATS kernel.

---

## 2. System Definition

### 2.1 Dynamical Cognitive System

```
Cognitive System = (NSC_Program, Initial_State, Budget, Policy)
```

Where:
- **NSC_Program**: The cognitive computation to execute
- **Initial_State**: Starting X state
- **Budget**: Initial coherence budget B₀
- **Policy**: Action selection policy

### 2.2 ATS Hosting

```
ATS ⊇ Cognitive_System
```

The ATS contains (hosts) the cognitive system as an admissible execution.

---

## 3. Embedding Process

### 3.1 Initialization

```python
def embed_cognitive_system(program, initial_state, budget, kappa):
    """Embed a cognitive system in ATS."""
    
    # Validate initial state
    assert initial_state in X
    assert budget >= 0
    
    # Create ATS context
    ats_context = ATSContext(
        program=program,
        state=initial_state,
        budget=budget,
        kappa=kappa,
        receipts=[]
    )
    
    return ats_context
```

### 3.2 Execution Loop

```python
def execute(ats_context):
    """Execute cognitive system under ATS."""
    
    while not ats_context.terminated():
        # Select action via policy
        action = ats_context.policy.select(ats_context.state)
        
        # Emit to ATS
        receipt, result = ats_kernel.verify_step(
            ats_context.state,
            action,
            ats_context.budget,
            ats_context.kappa
        )
        
        if result == ACCEPT:
            # Apply action
            ats_context.state = action.apply(ats_context.state)
            ats_context.budget = receipt.budget_after
            ats_context.receipts.append(receipt)
        else:
            # Handle rejection
            ats_context.handle_rejection(result)
    
    return ats_context.final_state, ats_context.receipts
```

---

## 4. Termination Conditions

### 4.1 Normal Termination

| Condition | Description |
|-----------|-------------|
| **Goal reached** | Policy determines goal achieved |
| **Budget exhausted** | B = 0 and cannot continue |
| **Program halt** | NSC program terminates |

### 4.2 Abnormal Termination

| Condition | Description |
|-----------|-------------|
| **Verification failure** | Receipt rejected |
| **Non-determinism** | State hash mismatch |
| **Budget violation** | Budget law broken |

---

## 5. System Properties

### 5.1 Guaranteed Properties

Under ATS governance, the cognitive system has:

| Property | Guarantee |
|----------|-----------|
| **Bounded execution** | Budget invariant prevents infinite risk accumulation |
| **Verifiability** | Every step has receipt |
| **Determinism** | Same inputs → same outputs |
| **Auditability** | Full trajectory replay possible |

### 5.2 What ATS Provides

| ATS Feature | Cognitive System Benefit |
|-------------|------------------------|
| Budget law | Prevents runaway risk |
| Receipt verification | Ensures honesty |
| Deterministic domain | Platform independence |
| Chain hashing | Tamper evidence |

---

## 6. Example: HAAI Embedding

### 6.1 HAAI as ATS Instance

```
HAAI = Cognitive_System(
    program=HAAI_NSC_Program,
    initial_state=HAAI_Initial_State,
    budget=Coherence_Budget,
    policy=Reasoning_Policy
)
```

### 6.2 Execution

```python
# Initialize HAAI in ATS
haai = embed_cognitive_system(
    program=nsc_haai_program,
    initial_state=empty_state,
    budget=QFixed(1_000_000),
    kappa=QFixed(1)
)

# Execute
final_state, receipts = execute(haai)

# Verify
result = verify_trajectory(
    initial_state,
    receipts,
    initial_budget=QFixed(1_000_000),
    kappa=QFixed(1)
)
```

---

## 7. References

- [ATS Definition](../00_identity/ats_definition.md)
- [Project Identity](../00_identity/project_identity.md)
- [Coh Kernel Scope](../00_identity/coh_kernel_scope.md)
- [NSC VM to ATS Bridge](./nsc_vm_to_ats_bridge.md)
- [Policy Layer Constraints](./policy_layer_constraints.md)

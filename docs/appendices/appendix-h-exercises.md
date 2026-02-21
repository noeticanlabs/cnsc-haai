# Appendix H: Exercises

**Hands-On Exercises for Learning CNHAAI**

## Exercise 1: Build a Simple Abstraction Ladder

### Objective
Create a 3-layer abstraction ladder for a simple domain.

### Instructions
1. Choose a domain (e.g., weather, food, transportation)
2. Define 3 layers:
   - Layer 0: Raw observations
   - Layer 1: Patterns or categories
   - Layer 2: Generalizations or predictions
3. Define gates for layer transitions
4. Test the ladder with sample inputs

### Deliverable
```yaml
ladder:
  name: "exercise_1_solution"
  domain: "[your_domain]"
  layers:
    - id: "L0"
      # ...
    - id: "L1"
      # ...
    - id: "L2"
      # ...
  gates:
    # ...
```

## Exercise 2: Implement a Gate

### Objective
Implement a custom gate for a specific validation.

### Instructions
1. Choose a validation rule (e.g., "evidence must be less than 30 days old")
2. Implement the gate in Python
3. Write unit tests
4. Verify with test cases

### Deliverable
```python
class CustomGate(Gate):
    def evaluate(self, state, context):
        # Your implementation
        pass
```

## Exercise 3: Analyze a Failure

### Objective
Diagnose a system failure and recommend recovery.

### Instructions
1. Review the failure scenario
2. Identify the root cause
3. Determine the failure type
4. Propose a recovery strategy
5. Design prevention measures

### Scenario
A medical diagnosis system produces inconsistent recommendations for similar patients.

### Deliverable
```yaml
analysis:
  failure_type: "[type]"
  root_cause: "[explanation]"
  recovery_strategy:
    - step_1
    - step_2
    - step_3
  prevention:
    - measure_1
    - measure_2
```

## Exercise 4: Design a Receipt System

### Objective
Design a receipt system for a specific use case.

### Instructions
1. Choose a use case (e.g., audit trail, compliance verification)
2. Define receipt types needed
3. Design the schema
4. Specify verification procedures

### Deliverable
```yaml
receipt_system:
  use_case: "[description]"
  receipt_types:
    - type_1
    - type_2
  schema: "[reference]"
  verification: "[procedures]"
```

---

## Version Information

| Component | Version |
|-----------|---------|
| Appendix | H-exercises |
| Version | 1.0.0 |
| Updated | 2024-01-01 |
| Status | Canonical |

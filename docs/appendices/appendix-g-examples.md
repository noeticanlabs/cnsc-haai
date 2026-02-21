# Appendix G: Examples

**Comprehensive Examples Demonstrating CNHAAI Concepts**

## Medical Diagnosis Example

### Scenario
A CNHAAI system diagnosing a patient with respiratory symptoms.

### Abstraction Ladder

```yaml
ladder:
  name: "medical_diagnosis"
  layers:
    - id: "L0"
      name: "raw_symptoms"
      type: "descriptive"
      examples: ["cough", "fever", "fatigue"]
      
    - id: "L1"
      name: "clinical_findings"
      type: "descriptive"
      examples: ["vital_signs", "lab_results"]
      
    - id: "L2"
      name: "differential_diagnosis"
      type: "mechanistic"
      examples: ["infection", "allergy", "autoimmune"]
      
    - id: "L3"
      name: "confirmed_diagnosis"
      type: "mechanistic"
      examples: ["bacterial_pneumonia"]
      
    - id: "L4"
      name: "treatment_plan"
      type: "normative"
      examples: ["prescribe_antibiotics"]
```

### Gate Configuration

```yaml
gates:
  - name: "evidence_sufficiency"
    type: "reconstruction_bound"
    threshold: 0.90
    
  - name: "consistency_check"
    type: "contradiction"
    threshold: 0
    
  - name: "scope_enforcement"
    type: "scope"
    scope: "respiratory_conditions"
```

### Receipt Excerpt

```json
{
  "receipt_id": "diagnosis-receipt-001",
  "step_type": "gate_validation",
  "decision": "PASS",
  "details": {
    "gate": "evidence_sufficiency",
    "score": 0.95
  }
}
```

## Financial Planning Example

### Scenario
A CNHAAI system creating a retirement investment plan.

### Key Components

```yaml
components:
  abstraction_layers:
    - "transactions"
    - "account_balances"
    - "portfolio_allocation"
    - "investment_strategy"
    
  gates:
    - "risk_tolerance_check"
    - "diversification_check"
    - "regulatory_compliance"
    
  rails:
    - "budget_allocation"
    - "risk_exposure_limit"
```

---

## Version Information

| Component | Version |
|-----------|---------|
| Appendix | G-examples |
| Version | 1.0.0 |
| Updated | 2024-01-01 |
| Status | Canonical |

# Module 06: Abstraction Types

**Classification and Analysis of Abstraction Types in CNHAAI**

| Field | Value |
|-------|-------|
| **Module** | 06 |
| **Version** | 1.0.0 |
| **Lines** | ~700 |
| **Prerequisites** | Module 05 |

---

## Table of Contents

1. Abstraction Type Taxonomy
2. Descriptive Abstractions
3. Mechanistic Abstractions
4. Normative Abstractions
5. Comparative Abstractions
6. Hybrid Abstraction Types
7. Abstraction Type Selection
8. Abstraction Type Transformation
9. Edge Cases and Special Topics
10. References and Further Reading

---

## 1. Abstraction Type Taxonomy

### 1.1 Type Classification

CNHAAI recognizes four primary abstraction types:

| Type | Purpose | Example |
|------|---------|---------|
| **Descriptive** | Summarize observations | "The patient has fever" |
| **Mechanistic** | Explain causal relationships | "Fever causes elevated metabolism" |
| **Normative** | Prescribe actions | "Administer antipyretic" |
| **Comparative** | Enable analogy | "Similar to previous case" |

### 1.2 Type Characteristics

| Type | Evidence Base | Uncertainty | Stability | Use Case |
|------|--------------|-------------|-----------|----------|
| Descriptive | Observation | Low | Medium | Facts |
| Mechanistic | Analysis | Medium | Medium-High | Explanation |
| Normative | Norms | Variable | Low | Prescription |
| Comparative | Similarity | Medium-High | Low | Analogy |

### 1.3 Type Relationships

Types are related through:

```
Descriptive → Basis for → Mechanistic
Descriptive → Basis for → Comparative
Mechanistic → Basis for → Normative
Comparative → Influences → Normative
```

---

## 2. Descriptive Abstractions

### 2.1 Definition and Characteristics

Descriptive abstractions summarize observations without explaining why. They capture **what is** rather than **why** or **what should be**.

### 2.2 Characteristics

| Characteristic | Description |
|----------------|-------------|
| **Empirical** | Based on observation or measurement |
| **Factive** | Describes actual states or events |
| **Specific** | Can refer to particular instances |
| **Time-Bound** | Valid for specific time periods |

### 2.3 Examples and Use Cases

| Domain | Example | Use Case |
|--------|---------|----------|
| **Medical** | "Patient temperature is 38.5°C" | Observation recording |
| **Financial** | "Stock price increased by 5%" | Market monitoring |
| **Legal** | "Contract signed on date X" | Fact establishment |
| **Scientific** | "Sample shows pH 7.2" | Data recording |

### 2.4 Implementation Guidelines

For descriptive abstractions:

1. **Evidence Binding**: Must be bound to specific observations
2. **Time Stamping**: Must include temporal information
3. **Source Attribution**: Must cite data source
4. **Precision Recording**: Must capture uncertainty

### 2.5 Quality Assessment

Descriptive abstraction quality is measured by:

| Metric | Description | Target |
|--------|-------------|--------|
| **Accuracy** | Alignment with reality | > 99% |
| **Completeness** | Coverage of observations | 100% of relevant |
| **Timeliness** | Currency of data | Real-time |
| **Validity** | Appropriateness of description | High |

---

## 3. Mechanistic Abstractions

### 3.1 Definition and Characteristics

Mechanistic abstractions explain causal relationships and mechanisms. They capture **why** something happens.

### 3.2 Characteristics

| Characteristic | Description |
|----------------|-------------|
| **Causal** | Describes cause-effect relationships |
| **Explanatory** | Provides understanding of mechanisms |
| **General** | Applies across instances |
| **Predictive** | Enables prediction of outcomes |

### 3.3 Examples and Use Cases

| Domain | Example | Use Case |
|--------|---------|----------|
| **Medical** | "Infection causes inflammation" | Diagnosis |
| **Financial** | "Interest rate changes affect borrowing" | Prediction |
| **Legal** | "Negligence causes liability" | Reasoning |
| **Scientific** | "Gravity causes orbital motion" | Explanation |

### 3.4 Implementation Guidelines

For mechanistic abstractions:

1. **Causal Chain**: Must trace causal connections
2. **Evidence Support**: Must cite supporting evidence
3. **Boundary Conditions**: Must specify applicability limits
4. **Counterfactuals**: Must consider alternative mechanisms

### 3.5 Quality Assessment

Mechanistic abstraction quality is measured by:

| Metric | Description | Target |
|--------|-------------|--------|
| **Causal Accuracy** | Correctness of causal claims | > 95% |
| **Explanatory Power** | Ability to explain observations | High |
| **Predictive Accuracy** | Accuracy of predictions | > 90% |
| **Generalizability** | Applicability across contexts | High |

---

## 4. Normative Abstractions

### 4.1 Definition and Characteristics

Normative abstractions prescribe actions and values. They capture **what should be** based on goals, ethics, or standards.

### 4.2 Characteristics

| Characteristic | Description |
|----------------|-------------|
| **Prescriptive** | States what ought to be done |
| **Value-Based** | Grounded in goals or ethics |
| **Context-Dependent** | Valid in specific contexts |
| **Action-Oriented** | Guides behavior or decisions |

### 4.3 Examples and Use Cases

| Domain | Example | Use Case |
|--------|---------|----------|
| **Medical** | "Prescribe antibiotic if bacterial infection" | Treatment protocol |
| **Financial** | "Diversify portfolio to reduce risk" | Investment strategy |
| **Legal** | "Provide due process before punishment" | Legal principle |
| **Ethical** | "Do no harm" | Ethical principle |

### 4.4 Implementation Guidelines

For normative abstractions:

1. **Value Grounding**: Must specify underlying values
2. **Scope Definition**: Must define applicability
3. **Conflict Resolution**: Must address potential conflicts
4. **Revision Protocol**: Must allow for updates

### 4.5 Quality Assessment

Normative abstraction quality is measured by:

| Metric | Description | Target |
|--------|-------------|--------|
| **Value Alignment** | Alignment with stated values | High |
| **Practicality** | Feasibility of implementation | High |
| **Acceptability** | Stakeholder acceptance | High |
| **Consistency** | Internal consistency | 100% |

---

## 5. Comparative Abstractions

### 5.1 Definition and Characteristics

Comparative abstractions enable analogy and alignment by identifying similarities and differences between entities or situations.

### 5.2 Characteristics

| Characteristic | Description |
|----------------|-------------|
| **Relational** | Describes relationships between entities |
| **Similarity-Based** | Identifies commonalities |
| **Transfer-Enabling** | Allows transfer of knowledge |
| **Contextual** | Depends on comparison context |

### 5.3 Examples and Use Cases

| Domain | Example | Use Case |
|--------|---------|----------|
| **Medical** | "This case is similar to Case X" | Diagnosis |
| **Financial** | "This market resembles 2008" | Prediction |
| **Legal** | "This case parallels Case Y" | Precedent |
| **Scientific** | "This system analogous to system Z" | Modeling |

### 5.4 Implementation Guidelines

For comparative abstractions:

1. **Similarity Metrics**: Must define similarity measures
2. **Difference Identification**: Must identify relevant differences
3. **Transfer Validation**: Must validate knowledge transfer
4. **Context Specification**: Must specify comparison context

### 5.5 Quality Assessment

Comparative abstraction quality is measured by:

| Metric | Description | Target |
|--------|-------------|--------|
| **Similarity Accuracy** | Correctness of similarity assessment | > 90% |
| **Difference Sensitivity** | Identification of relevant differences | High |
| **Transfer Validity** | Validity of knowledge transfer | > 85% |
| **Context Appropriateness** | Appropriateness of comparison context | High |

---

## 6. Hybrid Abstraction Types

### 6.1 Type Combinations

Abstraction types can be combined:

| Combination | Description | Example |
|-------------|-------------|---------|
| **Descriptive-Mechanistic** | Descriptive with causal explanation | "Temperature is 38.5°C because of infection" |
| **Mechanistic-Normative** | Causal with prescription | "Because infection causes harm, treat with antibiotic" |
| **Comparative-Normative** | Comparative with prescription | "Like Case X, this requires intervention Y" |

### 6.2 Multi-Type Abstraction

A single abstraction can have multiple types:

```
A = (Descriptive, Mechanistic, Normative)

Example: "Elevated temperature (descriptive) indicates infection
         (mechanistic) which should be treated (normative)"
```

### 6.3 Type Inference

CNHAAI can infer abstraction types:

| Input | Inferred Type | Confidence |
|-------|---------------|------------|
| Raw observation | Descriptive | High |
| Causal statement | Mechanistic | High |
| Prescriptive statement | Normative | High |
| Similarity statement | Comparative | High |

---

## 7. Abstraction Type Selection

### 7.1 Selection Criteria

Type selection depends on:

| Criterion | Description |
|-----------|-------------|
| **Purpose** | What the abstraction is for |
| **Evidence** | What evidence is available |
| **Uncertainty** | Level of uncertainty |
| **Stability** | Expected stability |

### 7.2 Selection Matrix

| Purpose | Primary Type | Secondary Types |
|---------|--------------|-----------------|
| **Fact Recording** | Descriptive | - |
| **Explanation** | Mechanistic | Descriptive |
| **Decision Support** | Normative | Mechanistic, Descriptive |
| **Case Analysis** | Comparative | Descriptive, Mechanistic |
| **Planning** | Normative | Comparative, Mechanistic |

### 7.3 Selection Process

```
1. Identify purpose
     ↓
2. Assess available evidence
     ↓
3. Evaluate uncertainty
     ↓
4. Select primary type
     ↓
5. Identify secondary types
     ↓
6. Validate selection
```

---

## 8. Abstraction Type Transformation

### 8.1 Transformation Types

| Transformation | Description | Example |
|----------------|-------------|---------|
| **Specialization** | General to specific | Descriptive → Case-specific descriptive |
| **Generalization** | Specific to general | Descriptive → General principle |
| **Derivation** | One type to another | Descriptive → Mechanistic |
| **Combination** | Multiple to single | Descriptive + Mechanistic → Normative |

### 8.2 Transformation Rules

| Source Type | Target Type | Rule |
|-------------|-------------|------|
| Descriptive | Mechanistic | Add causal mechanism |
| Descriptive | Comparative | Identify similar cases |
| Mechanistic | Normative | Add prescription based on mechanism |
| Comparative | Normative | Transfer prescription from similar case |

### 8.3 Transformation Validation

Transformations must be validated:

1. **Preservation**: Original information preserved
2. **Consistency**: No contradictions introduced
3. **Evidence**: New claims supported by evidence
4. **Utility**: Transformation improves utility

---

## 9. Edge Cases and Special Topics

### 9.1 Uncertain Types

When type is uncertain:

```
A has type probability distribution:
P(Descriptive) = 0.4
P(Mechanistic) = 0.4
P(Normative) = 0.1
P(Comparative) = 0.1
```

### 9.2 Conflicting Types

When types conflict:

1. **Detection**: Identify conflict
2. **Resolution**: Apply resolution rules
3. **Documentation**: Record conflict and resolution
4. **Review**: Flag for human review if needed

### 9.3 Novel Types

New types can emerge:

1. **Observation**: Identify novel pattern
2. **Characterization**: Define type properties
3. **Validation**: Test type utility
4. **Integration**: Add to type taxonomy

---

## 10. References and Further Reading

### Primary Sources

1. Noetican Labs. "Abstraction Type Taxonomy." 2024.
2. Noetican Labs. "Type System Specification." 2024.
3. Noetican Labs. "Normative Reasoning Guide." 2024.

### Philosophy

4. Aristotle. "Nicomachean Ethics." (Normative)
5. Hume, D. "A Treatise of Human Nature." (Causation)

### Cognitive Science

6. Gentner, D. "Structure-Mapping: A Theoretical Framework." 1983.
7. Kahneman, D. "Thinking, Fast and Slow." 2011.

---

## Previous Module

[Module 05: Abstraction Theory](05-abstraction-theory.md)

## Next Module

[Module 07: Abstraction Contracts](07-abstraction-contracts.md)

---

## Version Information

| Component | Version |
|-----------|---------|
| Module | 06-abstraction-types |
| Version | 1.0.0 |
| Updated | 2024-01-01 |
| Status | Canonical |

# Glossary + Lexicon (Noetica Ecosystem) v1.0

## 0) Quick legend

* **GLLL** = Hadamard Glyph Low-Level Language (max separation, robust error tolerance)
* **GHLL** = Noetica Glyph High-Level Language (meaning-rich, structural semantics)
* **GML** = Aeonica Glyph Memory Language (time/run ledger, trace braid)
* **NSC** = Noetic Compiler (packet → parse → IR → bytecode)
* **NSC-VM** = deterministic runtime for bytecode stepping + receipts

---

## 1) Acronyms (canonical)

| Acronym      | Expansion                           | Definition                                                                                                          |
| ------------ | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **NSC**      | Noetic Compiler                     | Compiler boundary that transforms glyph code into portable symbolic code/bytecode and supports auditable execution. |
| **NSC-VM**   | NSC Virtual Machine                 | Deterministic bytecode interpreter producing receipts and PDE templates / field steps.                              |
| **NLLC**     | Noetica Language / Ledger Computing | Umbrella term you’ve used for “meaning that computes” + ledger governance.                                          |
| **TGS**      | Triaxis Glyph System                | A 3-axis glyph organization scheme (often: structure/meaning/field) used to keep semantics stable across layers.    |
| **LoC**      | Law of Coherence                    | The governing principle: coherence is measurable, conserved/managed, and enforceable through gates + receipts.      |
| **UFE**      | Universal Field Equation            | Your generalized PDE skeleton for coherence-driven dynamics (ρ/θ + sources + governance).                           |
| **RFE**      | Resonant Field Equation             | A resonance-focused evolution rule-set (often θ/phase dominant).                                                    |
| **CGL**      | Coherence Governance Layer          | The rule engine that enforces gates, budgets, receipts, and rollback logic.                                         |
| **Ω-ledger** | Omega Ledger                        | Hash-chained run ledger recording state, actions, and provenance.                                                   |
| **PDE**      | Partial Differential Equation       | Continuous field evolution form emitted/approximated by NSC/NFI execution targets.                                  |
| **IR**       | Intermediate Representation         | Compiler-internal representation between AST and bytecode.                                                          |
| **AST**      | Abstract Syntax Tree                | Parsed structure with spans (source offsets) for provenance.                                                        |
| **CRC32**    | Cyclic Redundancy Check             | Phase-1 packet integrity hash label (“coherence_crc32”).                                                            |

---

## 2) Core invariants (things you refuse to compromise on)

| Term                         | Definition                                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Deterministic stepping**   | Same bytecode + same env → same receipts + same outputs. No hidden randomness.                          |
| **Auditability**             | Every important action produces a receipt record, ideally hash-chained.                                 |
| **Provenance span**          | Byte offsets linking runtime actions back to original glyph text.                                       |
| **Reversibility (compiler)** | Ability (in configured modes) to reconstruct source structure from lowered forms without semantic loss. |
| **Coherence-safety**         | Any transformation must preserve alignment between syntax ↔ meaning ↔ field effect.                     |

---

## 3) Languages & layers (the “three alphabets” stack)

| Term                                | Definition                                                                                                                                          |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Hadamard glyphs (GLLL alphabet)** | ±1 feature-vector glyph basis built from Hadamard matrices; maximally distinct, error-tolerant, ideal for low-level encoding and robust separation. |
| **Noetica glyphs (GHLL alphabet)**  | High-level glyph vocabulary optimized for semantics, composability, and structural meaning.                                                         |
| **Aeonica glyphs (GML alphabet)**   | Memory/time glyphs that record what happened, when, and under what governance—built for traceability and replay.                                    |
| **Compiler seam**                   | The “truth boundary” where two alphabets meet: GLLL encodes stable primitives; GHLL expresses meaning; GML logs execution reality.                  |
| **Trio-language**                   | Your combined ecosystem: (GLLL ↔ GHLL ↔ GML) with NSC and Ω-ledger enforcing consistency.                                                           |

---

## 4) NSC compiler pipeline (mechanics vocabulary)

| Term                          | Definition                                                                                                                             |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Packet**                    | Portable container holding header/body/footer + integrity hash.                                                                        |
| **Mode (symbolic/math/exec)** | Compile intent: preserve glyph structure (symbolic), normalize into operator math (math), or fully lower for runtime execution (exec). |
| **Parser**                    | Converts glyph stream into AST using the canonical EBNF.                                                                               |
| **Validator**                 | Enforces structural correctness (balanced groups, legal atoms, non-empty program).                                                     |
| **Lowering**                  | AST → IR; makes implicit meaning explicit and normalizes forms.                                                                        |
| **Selection**                 | IR → bytecode; chooses opcodes and ordering.                                                                                           |
| **Emitter**                   | Produces bytecode image + optional debug map.                                                                                          |
| **Disassembler**              | Bytecode → readable opcode listing for audits.                                                                                         |

---

## 5) Runtime / execution (NSC-VM + field evolution)

| Term                        | Definition                                                                                                       |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Opcode**                  | A single bytecode instruction (e.g., φ, ◯, ∆, ⇒).                                                                |
| **Stack machine**           | VM model where opcodes push/pop symbolic terms to build expressions.                                             |
| **Env (environment)**       | Runtime parameters: curvature R, sources s, boundary settings, coefficients, etc.                                |
| **Closure (EOM close)**     | The moment an expression becomes an “equation of motion” object (often triggered by ∆).                          |
| **Temporal marker**         | A runtime stage boundary (often ⇒) indicating “advance” in an execution sense.                                   |
| **PDE template**            | The emitted structural equation form that later becomes numeric evolution or symbolic propagation.               |
| **NFI (Field Interpreter)** | The execution engine that treats glyph programs as PDE-like symbolic evolutions (your “meaning executes” layer). |

---

## 6) Governance, gates, budgets (keeping reality honest)

| Term                     | Definition                                                                                         |
| ------------------------ | -------------------------------------------------------------------------------------------------- |
| **Gate**                 | A rule that checks whether a step is allowed (structural, semantic, or execution stability).       |
| **Soft fail**            | Step is rejected but recoverable (retry with changed dt/params) with receipts logged.              |
| **Hard fail**            | Non-recoverable violation; abort with explicit reason in receipts.                                 |
| **Coherence budget**     | The “allowed debt” model: steps must be affordable; dt/controls adjust to stay solvent.            |
| **Rollback point**       | A checkpoint state used for recovery after a failed gate.                                          |
| **Rail**                 | A bounded corrective control path (steering) that nudges the system back to coherence constraints. |
| **Controller gain (Kp)** | Proportional gain used when applying rail corrections (control-theory style).                      |

---

## 7) Receipts & ledger (the audit trail)

| Term                 | Definition                                                                                              |
| -------------------- | ------------------------------------------------------------------------------------------------------- |
| **Receipt**          | A structured record of a runtime action: opcode, before/after state hashes, deltas, spans, gate status. |
| **Receipt chain**    | Hash-linked receipts so tampering becomes detectable.                                                   |
| **Run hash**         | A hash summarizing the entire run history (often chained over receipts).                                |
| **State hash**       | Hash of (θ, ρ, env, metadata) at a step for deterministic verification.                                 |
| **Ledger truth**     | Principle: the ledger is what actually happened; narrative must match receipts.                         |
| **Ω-ledger receipt** | Your canonical term for the “audit-grade” record entry in the Omega ledger format.                      |

---

## 8) Field primitives (ρ/θ/ζ/Λ family)

| Term                        | Definition                                                                                                     |
| --------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **ρ (rho)**                 | Coherence amplitude / density field (often “how much coherent stuff exists here”).                             |
| **θ (theta)**               | Phase field (often “how aligned / how rotated is the coherence state”).                                        |
| **ζ (zeta)**                | Spectrum/ledger gating concept tied to zeta/prime structure in your arithmetic coherence framework.            |
| **J_C (coherence current)** | The flow of coherence through space/time (often ρ²∇θ style).                                                   |
| **S (source)**              | External injection term (can increase or perturb coherence).                                                   |
| **D (dissipation)**         | The sink/decay mechanism; high-frequency dissipation is key to preventing cascade.                             |
| **Order parameter**         | A scalar measure (0–1) of global phase alignment (Kuramoto-like).                                              |
| **Spectral tail**           | High-frequency content that must be controlled to avoid blow-up/cascade (your slab/barrier logic fights this). |

---

## 9) Lexicon: Phase-1 glyph atoms (NSC minimal set)

These are the **canonical atoms** used in your Phase-1 grammar/bytecode.

| Glyph | Name (lexeme)     | Operational meaning                                                                  |
| ----- | ----------------- | ------------------------------------------------------------------------------------ |
| **φ** | field-seed        | Introduce/load the coherence field variable (typically θ).                           |
| **↻** | curvature-couple  | Apply curvature/topological coupling term (contextual R).                            |
| **⊕** | source-plus       | Add/inject a positive source term (+s).                                              |
| **⊖** | source-minus      | Add a negative source / sink term (−s).                                              |
| **◯** | diffuse           | Apply diffusion/Laplacian-like term (∇²θ).                                           |
| **∆** | variational-close | Close/emit the equation-of-motion from the accumulated operator/context.             |
| **⇒** | time-advance      | Mark temporal progression stage / step boundary.                                     |
| **□** | boundary          | Apply or set boundary condition behavior.                                            |
| **↺** | back-couple       | Reverse/counter-rotation coupling (often used in recovery or inverse flow patterns). |
| **⇐** | reverse-map       | Used to denote inverse implication/transform direction at sentence level.            |

---

## 10) Lexicon: structural syntax words (how meaning is shaped)

| Term                | Definition                                                             |
| ------------------- | ---------------------------------------------------------------------- |
| **Sentence**        | A phrase optionally mapping into another phrase (often via ⇒).         |
| **Phrase**          | A flat sequence of atoms/groups (no ambiguity; grouping is explicit).  |
| **Group**           | Brackets/parentheses create nested structure: `[...]` and `(...)`.     |
| **Transform arrow** | `⇒` indicates a directional mapping: state/context → update/transform. |
| **Program**         | One or more sentences separated by semicolons.                         |

---

## 11) Aeonica (GML) memory concepts

| Term               | Definition                                                                                                  |
| ------------------ | ----------------------------------------------------------------------------------------------------------- |
| **Trace**          | The chronological sequence of events in a run (the “what happened”).                                        |
| **PhaseLoom**      | A braided projection of a trace into multiple threads + couplings (separates concerns so audits are clean). |
| **Thread**         | A lane in PhaseLoom for a specific category of events (physics, governance, IO, etc.).                      |
| **Braid coupling** | Explicit links that show how actions in one thread affected another.                                        |
| **Replayability**  | Ability to re-run from receipts and reproduce outputs (determinism + logged env).                           |

---

## 12) Hadamard (GLLL) encoding concepts

| Term                        | Definition                                                                                  |
| --------------------------- | ------------------------------------------------------------------------------------------- |
| **Hadamard basis**          | Orthogonal ±1 vectors enabling maximal separation between glyph codes.                      |
| **Feature vector glyph**    | A glyph represented as a ±1 vector for robust distance and error tolerance.                 |
| **Hamming distance**        | Measure of difference between two ±1/bit vectors; larger = more distinct.                   |
| **Noise tolerance**         | Property that small corruption doesn’t collapse identity (crucial for low-level transport). |
| **Semantic embedding seam** | The mapping from feature-vectors into GHLL semantics and then into GML receipts.            |

---

## 13) Testing & verification vocabulary

| Term                            | Definition                                                                    |
| ------------------------------- | ----------------------------------------------------------------------------- |
| **Golden parse**                | A known input whose AST must match exactly across versions.                   |
| **Round-trip**                  | compile → disasm → re-encode → identical bytes (and/or semantic equivalence). |
| **Fuzzing**                     | Random valid programs used to ensure no crashes and invariants hold.          |
| **Invariant test**              | A test that checks a coherence rule (e.g., “no ∆ on empty stack”).            |
| **CI (continuous integration)** | Automated test pipeline that runs on every commit to prevent semantic drift.  |

---

## 14) Persona/Interface layer (project UX terms)

| Term                | Definition                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------- |
| **Kora**            | Your GM-OS assistant overlay persona name (interface identity).                             |
| **Overlay persona** | A UX wrapper that presents the system’s outputs consistently without changing ledger truth. |

---

## 15) Naming conventions (so files don’t become a haunted attic)

| Pattern         | Meaning                                                   |
| --------------- | --------------------------------------------------------- |
| `*_spec.md`     | Normative definitions; “the law.”                         |
| `*_guide.md`    | Explanations and usage; “how to use the law.”             |
| `*_schema.json` | Machine-validated structure (packets, receipts, ledgers). |
| `*_example.*`   | Runnable or parseable examples.                           |
| `vX_Y`          | Version tag used in artifacts and compatibility checks.   |

---

### Minimal “lexicon contract” (one sentence)

**A lexeme is only real if it has (1) a parse form, (2) an execution meaning, and (3) a receipt signature.**

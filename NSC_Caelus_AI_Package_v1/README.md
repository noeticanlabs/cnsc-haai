# NSC Caelus AI Package (v1)

Generated: 2026-02-01 (America/Chicago)

This zip is a self-contained "grant / review packet" for the NSC Caelus AI architecture:
- The *spec* is written as an engineering document (requirements + interfaces + acceptance tests).
- Schemas are machine-usable (JSON Schema) and paired with concrete example payloads.
- The evaluation plan is designed to produce receipts (reproducible evidence), not vibes.
- The safety/governance runbook is written for deployment reality (monitoring, incident response, rollback).

## Contents
- /docs
  - NSC_Caelus_AI_Specification_v1.docx
  - NSC_Caelus_AI_Evaluation_Protocol_v1.docx
  - NSC_Caelus_AI_Safety_Governance_Runbook_v1.docx
- /pdf
  - NSC_Caelus_AI_Executive_Brief_v1.pdf
  - NSC_Caelus_AI_Architecture_and_Dataflow_v1.pdf
- /schemas
  - tag_event.schema.json
  - gate_decision.schema.json
  - memory_record.schema.json
  - receipt.schema.json
  - claim_node.schema.json
  - eval_run.schema.json
- /examples
  - example_tag_event.json
  - example_gate_decision.json
  - example_memory_record.json
  - example_receipt.json
  - example_claim_node.json
  - example_eval_run.json
  - nsc_tag_ontology.yaml
- /runbooks
  - deployment_observability.md
  - test_plan.yaml
  - receipts_ledger_example.jsonl
  - receipts_ledger_example.csv

## Sources used for evaluation & governance framing (bibliographic)
- Glenn, Jerome. *Foresight on Demand: "Foresight Towards the 2nd Strategic Plan for Horizon Europe" - Artificial General Intelligence: Issues and Opportunities (Rapid Exploration)*. The Millennium Project, Feb 2023.
- Wang, Pei. *The Evaluation of AGI Systems*. Temple University preprint (undated).


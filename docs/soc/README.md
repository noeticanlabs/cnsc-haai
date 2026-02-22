# SOC Spine Documentation

This directory contains the Self-Organized Criticality (SOC) attractor framework for CNSC-HAAI, including theorem programs, runtime specifications, and reference implementations.

## Overview

The SOC spine provides:
- **Necessary conditions** for SOC attractor existence in the operator + ledger regime
- **Theorem program** connecting boundary crossings to scale-free renormalization statistics  
- **Runtime trigger specification** with exact acceptance predicates
- **Reference verifier** implementation for renorm criticality verification

## Contents

| File | Description |
|------|-------------|
| [`01_soc_attractor_necessary_conditions.md`](docs/soc/01_soc_attractor_necessary_conditions.md) | Derives NC1-NC5 necessary conditions |
| [`02_scale_free_renorm_theorem_program.md`](docs/soc/02_scale_free_renorm_theorem_program.md) | Physics-to-math bridge for scale-free statistics |
| [`03_runtime_trigger_spec.md`](docs/soc/03_runtime_trigger_spec.md) | Runtime quantities and acceptance predicate |

## Tag System

Claims are tagged with confidence levels:
- **[PROVED]** - Fully proven within the framework
- **[LEMMA-NEEDED]** - Requires additional lemma for full proof
- **[HEURISTIC]** - Intuition-supported but not rigorously proven
- **[COUNTEREXAMPLE-RISK]** - May have counterexamples

## Related Components

- Schema: [`schemas/coh.renorm_criticality_receipt.v1.json`](schemas/coh.renorm_criticality_receipt.v1.json)
- Implementation: [`src/soc/norm_bounds.py`](src/soc/norm_bounds.py), [`src/soc/rv_verify_renorm_criticality.py`](src/soc/rv_verify_renorm_criticality.py)

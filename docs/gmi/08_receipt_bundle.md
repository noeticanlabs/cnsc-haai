# 8. Receipt Bundle

## 8.1 Structure

ReceiptBundle contains:
- decision_record_hash
- pre_state_hash
- post_state_hash
- per_candidate:
  - work_spent
  - invariant_checks
  - trace_digest
- merkle_root
- parent_chain_tip
- new_chain_tip

## 8.2 Chain Tip

$$C_{t+1} = \mathrm{SHA256}(\mathrm{JCS}(ReceiptBundle))$$

## 8.3 CNHAI Mapping

| GMI Concept | CNHAI Equivalent |
|-------------|------------------|
| ReceiptBundle | Receipt |
| decision_record_hash | Receipt.decision_hash |
| pre_state_hash | Receipt.state_hash_before |
| post_state_hash | Receipt.state_hash_after |
| merkle_root | Receipt.merkle_root |
| chain_tip | Receipt.chain_hash |

## 8.4 Receipt Versioning

| Version | Purpose | Consensus |
|---------|---------|-----------|
| v1 | Telemetry/debugging | NOT consensus |
| v2 | ATS verification | CONSENSUS |

Receipts used for replay must be v2+.

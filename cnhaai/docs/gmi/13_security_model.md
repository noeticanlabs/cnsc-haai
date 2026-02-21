# 13. Security Model

## 13.1 Adversaries

| ID | Adversary | Capability |
|----|-----------|------------|
| A1 | Malicious predictor | Generate invalid proposals |
| A2 | Malicious executor | Skip/mutate actions |
| A3 | Malicious ledger | Tamper with receipts |
| A4 | Corrupted memory | Modify state illegitimately |
| A5 | Partial witness | Withhold required fields |

## 13.2 Defenses

| Adversary | Defense |
|-----------|---------|
| A1 | Deterministic gate, rejection codes |
| A2 | Replay verification, state hash |
| A3 | Merkle commitment, chain hashing |
| A4 | State hash, replay verification |
| A5 | WitnessAvail predicate |

## 13.3 Security Theorems

1. **Gate Soundness**: No proposal passes gate without meeting all requirements.
2. **Replay Integrity**: Replay always reproduces identical state.
3. **Chain Binding**: Chain tip commits to entire history.
4. **Budget Conservation**: Budget never increases without credit.

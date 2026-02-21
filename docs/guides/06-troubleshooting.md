# Guide 06: Troubleshooting

**Version**: 1.0.0
**Status**: DRAFT

---

## Common Issues and Solutions

This guide covers common issues you may encounter when working with CNHAAI and their solutions.

---

## Import Errors

### Issue: `ModuleNotFoundError: No module named 'cnhaai'`

**Solution:**
Ensure Python path includes the src directory:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

Or install in development mode:
```bash
pip install -e .
```

---

## Coherence Issues

### Issue: Coherence not being enforced

**Check:**
1. Are you using the correct module?

```python
# WRONG
from cnhaai.core.coherence import CoherenceBudget  # UI only!

# CORRECT
from cnsc.haai.ats.risk import CoherenceRisk
```

2. Is the ATS kernel being called?

---

## Receipt Issues

### Issue: Receipt verification fails

**Check:**
1. Are receipts properly signed?
```python
receipt.sign(secret_key=key)
```

2. Is the secret key correct?
3. Has the receipt been modified after signing?

---

## Gate Issues

### Issue: Gates always return PASS

**Check:**
1. Are gates properly registered?
```python
manager = GateManager()
manager.register_gate(MyGate())
```

2. Is threshold set correctly?
3. Are context/state being passed?

---

## Performance Issues

### Issue: Slow execution

**Solutions:**
1. Reduce max abstraction depth
2. Increase gate thresholds
3. Limit phase durations
4. Use caching where possible

---

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Receipt Chain

```python
from cnhaai.core.receipts import ReceiptSystem

system = ReceiptSystem()
for receipt in system.get_receipt_chain(episode_id):
    print(f"{receipt.step_index}: {receipt.content.decision}")
```

### Validate Hierarchy

```python
from cnhaai.core.abstraction import AbstractionLayer

layer = AbstractionLayer()
is_valid = layer.validate_hierarchy()
print(f"Hierarchy valid: {is_valid}")
```

---

## Error Codes

| Code | Description |
|------|-------------|
| E001 | Invalid abstraction scope |
| E002 | Gate evaluation failed |
| E003 | Receipt signature invalid |
| E004 | Budget exhausted |
| E005 | Phase transition invalid |

---

## Getting Help

1. Check the [spec documentation](../../docs/ats/)
2. Review test cases in `tests/`
3. Check compliance tests in `compliance_tests/`

---

## Related Documents

- [Quick Start](00-quick-start.md)
- [Developing Gates](02-developing-gates.md)
- [Implementing Receipts](04-implementing-receipts.md)

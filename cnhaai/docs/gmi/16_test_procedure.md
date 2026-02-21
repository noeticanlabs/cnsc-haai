# 16. First GMI v1 Test

## 16.1 Procedure

1. Initialize state $S_0$
2. Feed observation $O_0$
3. Predictor generates 5 candidates
4. Gate rejects 3, accepts 2
5. Execute 2
6. Verify receipts
7. Commit chain
8. Replay bundle

## 16.2 Success Criteria

If replay yields identical hash → GMI v1 exists.

## 16.3 CNHAI Test

See: `tests/test_kernel_integration.py::TestFullEpisodeFlow`

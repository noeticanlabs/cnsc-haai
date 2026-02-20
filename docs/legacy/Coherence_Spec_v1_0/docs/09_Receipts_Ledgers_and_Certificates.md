# Receipts, Ledgers, and Certificates

## Receipt required fields

A receipt must include:

* State summary (hash or canonical summary)
* Residual vector \(\mathbf r\) and debt \(\mathfrak C\)
* Debt decomposition terms
* Gate status (hard/soft) and hysteresis state
* Actions with before/after values and declared bounds
* Decision (accept/retry/abort) and decision rationale
* Policy id that identifies the gate/rail rules applied
* Parent hash and receipt hash

## Hash chaining rule

Receipts must be chained:

\[
h_n = H(\text{receipt}_n \| h_{n-1})
\]

## Certificate definition

A **run certificate** summarizes a run:

* Pass/fail status
* Maxima (max debt, max residuals)
* Final receipt hash
* Config hash
* Policy hash

## Replay requirements

Receipts must contain enough data to recompute decisions and verify gate outcomes within tolerance.

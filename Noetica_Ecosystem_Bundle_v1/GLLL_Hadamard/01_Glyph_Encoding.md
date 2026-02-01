# GLLL Glyph Encoding — v1.0

## Dictionary construction
Choose n=2^k, use rows of Hadamard matrix H_n as glyph vectors.

## Confidence
accept if confidence ≥ τ_conf AND margin ≥ τ_margin, else emit decode receipt with top-K candidates.

## Parity/checksum (recommended)
Reserve parity coordinates; parity failure must be receipted.

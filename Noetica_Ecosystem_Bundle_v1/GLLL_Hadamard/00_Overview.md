# GLLL (Hadamard Glyph Low-Level Language) — v1.0

GLLL encodes glyph identity as ±1 feature vectors derived from Hadamard matrices for maximal separation and robust decoding.

Core decode:
- score(r) = (1/n) Σ v_j r_j
- choose argmax score
- compute confidence + margin
- emit receipt when uncertain

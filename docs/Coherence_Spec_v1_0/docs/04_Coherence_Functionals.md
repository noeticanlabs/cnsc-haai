# Coherence Functionals

## Required outputs per step

Each step must emit the diagnostic vector:

\[
\mathbf c = (r_1,\dots,r_m,\mathfrak C)
\]

including the residuals and the scalar debt \(\mathfrak C\).

## Canonical decomposition (engineering default)

A recommended default is:

\[
\mathfrak C = w_{\text{cons}}\varepsilon^2 + w_{\text{rec}}r_{\text{rec}}^2 + w_{\text{tool}}r_{\text{tool}}^2 + w_{\text{thrash}}p_{\text{thrash}}
\]

where terms correspond to conservation error, reconstruction error, tool mismatch, and thrash penalties.

## Normalization rule

Each residual must be normalized so that **1.0 means “at the budget boundary.”** This prevents any single residual from dominating by scale rather than governance intent.

"""
CNSC-HAAI - Coherence Noetican Structured Code Hierarchical Abstraction AI

Monorepo scaffold for the NSC + GHLL + GLLL + GML stack with a single 
compiler seam and ledger-truth runtime contract.

References:
- cnsc-haai/docs/00_System_Overview.md
"""

__version__ = "1.0.0"
__author__ = "CNHAAI Team"

from cnsc.haai import ghll

__all__ = ["ghll", "__version__"]

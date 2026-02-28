"""
cnsc_haai namespace - compatibility shim

This package provides backward compatibility for imports using cnsc_haai.
The canonical namespace is now cnsc.haai.

DEPRECATED: Import from cnsc.haai instead.
"""

import warnings

warnings.warn(
    "cnsc_haai is deprecated. Import from cnsc.haai instead.", DeprecationWarning, stacklevel=2
)

# Re-export from cnsc.haai for backward compatibility
# These will only work if cnsc.haai has compatible modules
try:
    from cnsc.haai.ats import types
    from cnsc.haai.ats import bridge
    from cnsc.haai.ats import budget
    from cnsc.haai.ats import risk
    from cnsc.haai.ats import rv
except ImportError as e:
    import sys

    print(f"Warning: Could not re-export from cnsc.haai: {e}", file=sys.stderr)

# Re-export consensus modules
try:
    from cnsc_haai.consensus import chain
    from cnsc_haai.consensus import merkle
    from cnsc_haai.consensus import slab
    from cnsc_haai.consensus import hash
except ImportError:
    pass  # Consensus modules may not have cnsc.haai equivalents

# Version Compatibility

**Spec Version:** 1.0.0  
**Status:** Canonical

## Overview

This document defines version compatibility rules across all layers and seams.

## Version Matrix

| Layer/Seam | Current Version | Min Compatible | Status |
|------------|-----------------|----------------|--------|
| GLLL | 1.0.0 | 1.0.0 | Stable |
| GHLL | 1.0.0 | 1.0.0 | Stable |
| NSC | 1.0.0 | 1.0.0 | Stable |
| GML | 1.0.0 | 1.0.0 | Stable |
| GLLL→GHLL | 1.0.0 | 1.0.0 | Stable |
| GHLL→NSC | 1.0.0 | 1.0.0 | Stable |
| NSC→GML | 1.0.0 | 1.0.0 | Stable |

## Compatibility Rules

### Rule 1: Major Version Mismatch = Incompatible

```
If A.major != B.major:
    return INCOMPATIBLE
```

### Rule 2: Minor Version Bump = Backward Compatible

```
If A.major == B.major and A.minor > B.minor:
    if A.minor - B.minor <= 1:
        return BACKWARD_COMPATIBLE
    else:
        return CHECK_DEPENDENCIES
```

### Rule 3: Patch Version = Compatible

```
If A.major == B.major and A.minor == B.minor:
    return COMPATIBLE
```

## Migration Path

When upgrading versions:

1. **Backup** all data and receipts
2. **Test** in development environment
3. **Validate** receipt chains with new version
4. **Deploy** to production
5. **Monitor** for compatibility issues

## Error Codes

| Code | Meaning | Handling |
|------|---------|----------|
| `VERSION_MISMATCH` | Major version mismatch | Abort, upgrade required |
| `DEPRECATED_VERSION` | Version is deprecated | Upgrade recommended |
| `UNSUPPORTED_VERSION` | Version not supported | Abort |

## Wire Format

```json
{
  "version_info": {
    "glll": "1.0.0",
    "ghll": "1.0.0",
    "nsc": "1.0.0",
    "gml": "1.0.0",
    "seams": "1.0.0"
  },
  "compatibility": {
    "status": "COMPATIBLE",
    "warnings": [],
    "breaking_changes": []
  }
}
```

## See Also

- Seam principles: [`spec/seam/00_Seam_Principles.md`](../../spec/seam/00_Seam_Principles.md)

# Plans Directory

**Index of all planning documents for cnsc-haai project**

---

## Master Trackers

| File | Description | Status |
|------|-------------|--------|
| [TODO.md](TODO.md) | Master todo tracker with prioritized work items | Active |
| [general/TODO_Organization_Plan.md](general/TODO_Organization_Plan.md) | Plan to organize and systematize todo tracking | In Progress |
| [general/Documentation_Reorganization_Plan.md](general/Documentation_Reorganization_Plan.md) | Plan to consolidate specs and organize docs | Proposed |

---

## Categories

### General
| File | Description | Status |
|------|-------------|--------|
| [general/CNHAAI_Issue_Fix_Plan.md](general/CNHAAI_Issue_Fix_Plan.md) | General issue fixes | - |
| [general/cnsc_haai_fix_plan.md](general/cnsc_haai_fix_plan.md) | CNSC-HAAI specific fixes | - |

### Kernel
| File | Description | Status |
|------|-------------|--------|
| [kernel/ATS_Kernel_Fix_Plan.md](kernel/ATS_Kernel_Fix_Plan.md) | ATS kernel code fixes and improvements | Mostly Complete |

### Documentation
| File | Description | Status |
|------|-------------|--------|
| [docs/CNHAAI_Doc_Spine_Reorganization.md](docs/CNHAAI_Doc_Spine_Reorganization.md) | Documentation restructuring | - |

### Core
| File | Description | Status |
|------|-------------|--------|
| [core/coherence_framework_implementation_plan.md](core/coherence_framework_implementation_plan.md) | Coherence framework implementation | - |
| [core/Token_to_Graph_Conversion_Plan.md](core/Token_to_Graph_Conversion_Plan.md) | Token to graph conversion | - |

### Migration
| File | Description | Status |
|------|-------------|--------|
| [migration/COH_AGI_Migration_Completion_Plan.md](migration/COH_AGI_Migration_Completion_Plan.md) | COH-AGI migration completion | - |
| [migration/GML_Graph_Native_Migration_Plan.md](migration/GML_Graph_Native_Migration_Plan.md) | GML graph native migration | - |
| [migration/GML_Graph_Native_Migration_Results.md](migration/GML_Graph_Native_Migration_Results.md) | Migration results and findings | Complete |

### Integration
| File | Description | Status |
|------|-------------|--------|
| [integration/NPE_Implementation_Plan.md](integration/NPE_Implementation_Plan.md) | NPE service integration | In Progress |
| [integration/TGS_Build_Integration_Plan.md](integration/TGS_Build_Integration_Plan.md) | TGS build integration | - |

---

## Adding a New Plan

1. Create file in appropriate category directory (or `general/` if none applies)
2. Use naming convention: `Descriptive_Name_Plan.md` or `Descriptive_Name.md`
3. Add header with metadata:
   ```markdown
   **Created:** YYYY-MM-DD
   **Status:** [Draft|In Progress|Complete]
   **Purpose:** Brief description
   ```
4. Add entry to this README.md

---

## Related Documents

- [CHANGELOG.md](../CHANGELOG.md) - Version history
- [docs/spine/](../docs/spine/) - Core documentation
- [docs/ats/](../docs/ats/) - ATS specifications

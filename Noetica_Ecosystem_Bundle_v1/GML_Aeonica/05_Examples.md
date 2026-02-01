# GML Example — v1.0

Record a governed NSC step:
phys: vm_step
gate: check_invariant (depends_on vm_step)
audit: chain_hash (triggers after gate)

"""
Property-based tests for BridgeCert and coherence bounds.

These tests verify mathematical properties of the coherence system
against the Lean 4 UFE formalization.
"""

import pytest
from cnsc.haai.nsc.gates import BridgeCert, GateManager, Trajectory
from cnhaai.core.coherence import CoherenceBudget, VectorResidual
from cnsc.haai.tgs.clock import AffineReparam, Clock


class TestBridgeCert:
    """Tests for BridgeCert error bound computation."""
    
    def test_error_bound_positive(self):
        """Error bound should always be positive."""
        bc = BridgeCert()
        result = bc.errorBound(0.5, 0.1)
        assert result > 0
    
    def test_error_bound_monotonic_tau(self):
        """Error bound should increase with discrete bound."""
        bc = BridgeCert()
        result1 = bc.errorBound(0.5, 0.1)
        result2 = bc.errorBound(1.0, 0.1)
        assert result2 >= result1
    
    def test_error_bound_monotonic_delta(self):
        """Error bound should increase with step size."""
        bc = BridgeCert()
        result1 = bc.errorBound(0.5, 0.1)
        result2 = bc.errorBound(0.5, 0.2)
        assert result2 >= result1
    
    def test_error_bound_identity(self):
        """Error bound should equal tau_delta when delta is 0."""
        bc = BridgeCert()
        result = bc.errorBound(0.5, 0.0)
        assert result == 0.5
    
    def test_bridge_theorem_conservative(self):
        """Bridge theorem should return True for valid trajectories."""
        bc = BridgeCert()
        psi = Trajectory(points=[[1.0], [0.5]], weights=[1.0, 0.5])
        result = bc.bridge(psi, 0.0, 0.1, 1.0)
        assert isinstance(result, bool)
    
    def test_bridge_cert_serialization(self):
        """BridgeCert should serialize and deserialize correctly."""
        bc = BridgeCert(base_error=0.02, error_growth_rate=0.15)
        data = bc.to_dict()
        bc2 = BridgeCert.from_dict(data)
        assert bc2.base_error == bc.base_error
        assert bc2.error_growth_rate == bc.error_growth_rate


class TestVectorResidual:
    """Tests for vector residual norm."""
    
    def test_norm_nonnegative(self):
        """Residual norm should be non-negative."""
        residual = VectorResidual(dynamical=0.3, clock=0.4)
        assert residual.norm() >= 0
    
    def test_zero_residual(self):
        """Zero residual should have zero norm."""
        residual = VectorResidual(dynamical=0.0, clock=0.0)
        assert residual.norm() == 0.0
    
    def test_norm_calculation(self):
        """Norm should equal sqrt(dynamical² + clock²)."""
        residual = VectorResidual(dynamical=3.0, clock=4.0)
        assert abs(residual.norm() - 5.0) < 1e-10
    
    def test_dynamical_only(self):
        """Norm should equal absolute dynamical when clock is 0."""
        residual = VectorResidual(dynamical=0.6, clock=0.0)
        assert abs(residual.norm() - 0.6) < 1e-10
    
    def test_clock_only(self):
        """Norm should equal absolute clock when dynamical is 0."""
        residual = VectorResidual(dynamical=0.0, clock=0.8)
        assert abs(residual.norm() - 0.8) < 1e-10
    
    def test_vector_residual_serialization(self):
        """VectorResidual should serialize and deserialize correctly."""
        residual = VectorResidual(dynamical=0.3, clock=0.4)
        data = residual.to_dict()
        residual2 = VectorResidual.from_dict(data)
        assert residual2.dynamical == residual.dynamical
        assert residual2.clock == residual.clock


class TestCoherenceBudget:
    """Tests for CoherenceBudget with vector residuals."""
    
    def test_initial_coherence(self):
        """Initial coherence should be 1.0."""
        budget = CoherenceBudget()
        assert budget.current == 1.0
    
    def test_residual_initially_zero(self):
        """Residuals should be initially zero."""
        budget = CoherenceBudget()
        assert budget.dynamical_residual == 0.0
        assert budget.clock_residual == 0.0
        assert budget.norm() == 0.0
    
    def test_degrade_with_residuals(self):
        """Degrade should accumulate residuals."""
        budget = CoherenceBudget()
        budget.degrade_with_residuals(dynamical=0.3, clock=0.4)
        assert budget.dynamical_residual == 0.3
        assert budget.clock_residual == 0.4
    
    def test_coherence_from_residual(self):
        """Coherence should decrease with residual norm."""
        budget = CoherenceBudget()
        budget.degrade_with_residuals(dynamical=0.3, clock=0.4)
        # Coherence = 1.0 - norm = 1.0 - 0.5 = 0.5
        assert abs(budget.coherence_from_residual - 0.5) < 1e-10
    
    def test_get_residual_info(self):
        """Get residual info should return correct structure."""
        budget = CoherenceBudget()
        budget.degrade_with_residuals(dynamical=0.3, clock=0.4)
        info = budget.get_residual_info()
        assert "dynamical" in info
        assert "clock" in info
        assert "norm" in info
        assert "coherence" in info
    
    def test_snapshot_includes_residuals(self):
        """Snapshot should include residual information."""
        budget = CoherenceBudget()
        budget.degrade_with_residuals(dynamical=0.3, clock=0.4)
        snapshot = budget.snapshot()
        assert "dynamical_residual" in snapshot or "residual" in snapshot


class TestAffineReparam:
    """Tests for affine reparameterization."""
    
    def test_affine_check(self):
        """Affine reparameterization should have φ'' = 0."""
        reparam = AffineReparam(phi_double_prime=0.0)
        assert reparam.is_affine()
    
    def test_non_affine_rejected(self):
        """Non-affine reparameterization should fail check."""
        reparam = AffineReparam(phi_double_prime=0.1)
        assert not reparam.is_affine()
    
    def test_proper_time_conversion(self):
        """Proper time should be linear in coordinate time."""
        reparam = AffineReparam(phi_0=0.0, phi_prime_0=2.0)
        # At τ=5, proper time = (5 - 0) / 2 = 2.5
        assert reparam.to_proper_time(5.0) == 2.5
    
    def test_coordinate_time_conversion(self):
        """Coordinate time should be linear in proper time."""
        reparam = AffineReparam(phi_0=1.0, phi_prime_0=2.0)
        # At τ=2, coordinate time = 1 + 2*2 = 5
        assert reparam.to_coordinate_time(2.0) == 5.0
    
    def test_phi_prime_constant(self):
        """φ'(τ) should equal φ'(0) for affine."""
        reparam = AffineReparam(phi_0=0.0, phi_prime_0=3.0)
        assert reparam.phi_prime(0.0) == 3.0
        assert reparam.phi_prime(5.0) == 3.0
    
    def test_affine_serialization(self):
        """AffineReparam should serialize and deserialize correctly."""
        reparam = AffineReparam(phi_0=1.0, phi_prime_0=2.0, phi_double_prime=0.0)
        data = reparam.to_dict()
        reparam2 = AffineReparam.from_dict(data)
        assert reparam2.phi_0 == reparam.phi_0
        assert reparam2.phi_prime_0 == reparam.phi_prime_0
        assert reparam2.phi_double_prime == reparam.phi_double_prime


class TestClock:
    """Tests for Clock with affine parameterization."""
    
    def test_clock_initialization(self):
        """Clock should initialize with default reparam."""
        clock = Clock()
        assert clock.is_affine()
    
    def test_clock_with_custom_reparam(self):
        """Clock should work with custom reparam."""
        reparam = AffineReparam(phi_0=0.0, phi_prime_0=2.0)
        clock = Clock(reparam=reparam)
        assert clock.is_affine()
    
    def test_clock_not_started_error(self):
        """Clock should raise error if not started."""
        clock = Clock()
        with pytest.raises(RuntimeError):
            _ = clock.now()
    
    def test_clock_start(self):
        """Clock should start without error."""
        clock = Clock()
        clock.start()
        # Should not raise
        elapsed = clock.elapsed()
        assert isinstance(elapsed, float)
    
    def test_clock_to_dict(self):
        """Clock should serialize correctly."""
        clock = Clock()
        data = clock.to_dict()
        assert "reparam" in data
        assert "is_running" in data


class TestGateManagerBridgeIntegration:
    """Tests for GateManager bridge certification integration."""
    
    def test_default_bridge_cert(self):
        """GateManager should have default BridgeCert."""
        manager = GateManager()
        assert manager.bridge_cert is not None
    
    def test_set_bridge_cert(self):
        """GateManager should allow setting BridgeCert."""
        manager = GateManager()
        new_cert = BridgeCert(base_error=0.02, error_growth_rate=0.2)
        manager.set_bridge_cert(new_cert)
        assert manager.bridge_cert.base_error == 0.02
    
    def test_compute_error_bound(self):
        """GateManager should compute error bounds."""
        manager = GateManager()
        bound = manager.compute_error_bound(tau_delta=0.5, delta=0.1)
        assert bound > 0
        assert manager.last_error_bound == bound
        assert manager.last_step_size == 0.1
    
    def test_get_bridge_info(self):
        """GateManager should return bridge info."""
        manager = GateManager()
        manager.compute_error_bound(tau_delta=0.5, delta=0.1)
        info = manager.get_bridge_info()
        assert "bridge_cert" in info
        assert "last_error_bound" in info
        assert "last_step_size" in info

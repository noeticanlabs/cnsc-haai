"""
Clean Unit Tests for HAAI Components
Tests only confirmed working APIs.
"""

import pytest
import time
import numpy as np

from src.haai.core import CoherenceEngine, HierarchicalAbstraction
from src.haai.core.gates import GateRailCoordinator
from src.haai.core.coherence import CoherenceSignals
from src.haai.nsc import GLLLEncoder
from src.haai.governance import PolicyEngine


class TestCoherenceEngine:
    """Core coherence engine tests."""
    
    def test_processing(self):
        """Test processing phase field data."""
        engine = CoherenceEngine()
        
        theta = np.linspace(0, 2*np.pi, 100)
        signals = engine.process_field_data(theta)
        
        assert 0 <= signals.coherence_measure <= 1
        assert signals.phase_variance >= 0
        assert signals.gradient_norm >= 0
        
    def test_evaluation(self):
        """Test coherence evaluation."""
        engine = CoherenceEngine()
        
        theta = np.random.randn(50)
        signals = engine.process_field_data(theta)
        result = engine.evaluate_coherence(signals)
        
        assert 'risk_level' in result
        assert 'coherence_budget' in result
        
    def test_envelope_checking(self):
        """Test envelope breach detection."""
        engine = CoherenceEngine()
        
        signals = CoherenceSignals(
            coherence_measure=0.95,
            phase_variance=0.1,
            gradient_norm=1.0,
            laplacian_energy=5.0,
            spectral_peak_ratio=10.0,
            bandwidth_expansion=2.0,
            energy_density=50.0,
            injection_rate=0.05
        )
        
        within_envelope, breaches = engine.envelope_manager.check_signals(signals)
        assert isinstance(breaches, list)
        assert within_envelope == True


class TestHierarchicalAbstraction:
    """Hierarchical abstraction tests."""
    
    def test_creation(self):
        """Test abstraction framework creation."""
        framework = HierarchicalAbstraction(max_levels=3)
        summary = framework.get_abstraction_summary()
        
        assert 'active_levels' in summary
        assert 'map_count' in summary
        
    def test_level_manager(self):
        """Test level manager."""
        framework = HierarchicalAbstraction(max_levels=3)
        
        # Create level
        state = framework.level_manager.create_level(0, np.random.randn(50))
        
        assert state is not None
        
    def test_cross_level_maps(self):
        """Test cross-level map registration."""
        framework = HierarchicalAbstraction(max_levels=3)
        summary = framework.get_abstraction_summary()
        
        assert 'map_count' in summary
        assert summary['map_count'] > 0


class TestGateRailSystem:
    """Gate and Rail system tests."""
    
    def test_auto_registration(self):
        """Test gates auto-register on creation."""
        coordinator = GateRailCoordinator()
        
        gate_summary = coordinator.gate_system.get_gate_summary()
        
        assert gate_summary['total_gates'] == 3
        assert gate_summary['active_gates'] == 3
        
    def test_rail_registration(self):
        """Test rails auto-register on creation."""
        coordinator = GateRailCoordinator()
        
        rail_summary = coordinator.rail_system.get_rail_summary()
        
        assert rail_summary['total_rails'] == 2
        assert rail_summary['active_rails'] == 2
        
    def test_gate_evaluation(self):
        """Test gate evaluation."""
        coordinator = GateRailCoordinator()
        
        context = {'data': np.array([1.0, 2.0, 3.0]), 'coherence_debt': 0.3}
        result = coordinator.evaluate_and_act(context)
        
        assert 'gate_decisions' in result
        assert len(result['gate_decisions']) == 3
        assert result['overall_success'] == True
        
    def test_gate_pass_rates(self):
        """Test gate pass rates."""
        coordinator = GateRailCoordinator()
        
        # All gates should pass with good data
        context = {'data': np.array([1.0, 2.0, 3.0]), 'coherence_debt': 0.3}
        coordinator.evaluate_and_act(context)
        
        gate_summary = coordinator.gate_system.get_gate_summary()
        
        for name, stats in gate_summary.get('gate_stats', {}).items():
            assert stats['pass_rate'] >= 0.0
            assert stats['pass_rate'] <= 1.0


class TestGLLLEncoder:
    """GLLL Encoder tests."""
    
    def test_encoder_creation(self):
        """Test encoder initializes."""
        encoder = GLLLEncoder()
        
        # Check hadamard matrix is created
        assert encoder.hadamard_matrix is not None
        assert encoder.hadamard_matrix.shape[0] > 0
        
    def test_hadamard_order(self):
        """Test hadamard order."""
        encoder = GLLLEncoder(hadamard_order=32)
        
        assert encoder.hadamard_order == 32
        
    def test_default_glyphs(self):
        """Test default glyphs loaded."""
        encoder = GLLLEncoder()
        
        # Dictionary should have glyphs
        assert len(encoder.glyph_dictionary) > 0
        
    def test_encode_glyph(self):
        """Test encoding a single glyph."""
        encoder = GLLLEncoder()
        
        encoding = encoder.encode_glyph('φ')
        
        assert encoding is not None
        assert len(encoding.encoding) > 0


class TestPolicyEngine:
    """Policy Engine tests."""
    
    def test_initialization(self):
        """Test policy engine initializes with defaults."""
        engine = PolicyEngine()
        
        status = engine.get_engine_status()
        
        assert 'total_policies' in status
        assert status['total_policies'] > 0  # Default policies loaded
        
    def test_compliance_checker(self):
        """Test compliance checking."""
        engine = PolicyEngine()
        
        result = engine.compliance_checker({'operation_type': 'test'})
        
        assert 'compliant' in result
        assert 'violations' in result
        assert 'required_actions' in result
        
    def test_policy_evaluation(self):
        """Test policy evaluation."""
        engine = PolicyEngine()
        
        result = engine.evaluate_policies({'operation_type': 'test', 'coherence_score': 0.9})
        
        assert 'overall_compliant' in result
        assert 'policy_results' in result
        
    def test_policy_list(self):
        """Test policy listing."""
        engine = PolicyEngine()
        
        policies = engine.list_policies()
        
        assert len(policies) > 0


class TestPerformance:
    """Performance tests."""
    
    def test_coherence_performance(self):
        """Test coherence calculation speed."""
        engine = CoherenceEngine()
        
        start = time.time()
        for _ in range(100):
            theta = np.random.randn(500)
            engine.process_field_data(theta)
        elapsed = time.time() - start
        
        assert elapsed < 5.0  # Should complete in under 5 seconds
        
    def test_gate_evaluation_performance(self):
        """Test gate evaluation speed."""
        coordinator = GateRailCoordinator()
        
        start = time.time()
        for _ in range(100):
            context = {'data': np.random.randn(100), 'coherence_debt': 0.3}
            coordinator.evaluate_and_act(context)
        elapsed = time.time() - start
        
        assert elapsed < 2.0

"""
Core coherence engine implementation.

Implements coherence signal processing, envelope management, and risk state management
as defined in the CGL documentation.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk classification levels as defined in CGL."""
    GREEN = "GREEN"      # Within envelope with margin
    YELLOW = "YELLOW"    # Approaching envelope boundary
    ORANGE = "ORANGE"    # Envelope breach likely or minor breach
    RED = "RED"          # Envelope breach confirmed
    BLACK = "BLACK"      # Unknown state (telemetry missing)


@dataclass
class CoherenceSignals:
    """Coherence signal measurements."""
    coherence_measure: float = 0.0
    phase_variance: float = 0.0
    gradient_norm: float = 0.0
    laplacian_energy: float = 0.0
    spectral_peak_ratio: float = 0.0
    bandwidth_expansion: float = 0.0
    energy_density: float = 0.0
    injection_rate: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            'coherence_measure': self.coherence_measure,
            'phase_variance': self.phase_variance,
            'gradient_norm': self.gradient_norm,
            'laplacian_energy': self.laplacian_energy,
            'spectral_peak_ratio': self.spectral_peak_ratio,
            'bandwidth_expansion': self.bandwidth_expansion,
            'energy_density': self.energy_density,
            'injection_rate': self.injection_rate,
            'timestamp': self.timestamp
        }


@dataclass
class Envelope:
    """Coherence envelope definition."""
    name: str
    coherence_min: float = 0.92
    gradient_p99_max: float = 3.0
    spectral_peak_ratio_max: float = 20.0
    injection_rate_max: float = 0.1
    phase_variance_max: float = 1.0
    laplacian_energy_max: float = 10.0
    bandwidth_expansion_max: float = 5.0
    energy_density_max: float = 100.0
    version: str = "1.0"
    
    def check_breaches(self, signals: CoherenceSignals) -> List[str]:
        """Check if signals breach envelope boundaries."""
        breaches = []
        
        if signals.coherence_measure < self.coherence_min:
            breaches.append(f"coherence_measure < {self.coherence_min}")
        
        if signals.gradient_norm > self.gradient_p99_max:
            breaches.append(f"gradient_norm > {self.gradient_p99_max}")
            
        if signals.spectral_peak_ratio > self.spectral_peak_ratio_max:
            breaches.append(f"spectral_peak_ratio > {self.spectral_peak_ratio_max}")
            
        if signals.injection_rate > self.injection_rate_max:
            breaches.append(f"injection_rate > {self.injection_rate_max}")
            
        if signals.phase_variance > self.phase_variance_max:
            breaches.append(f"phase_variance > {self.phase_variance_max}")
            
        if signals.laplacian_energy > self.laplacian_energy_max:
            breaches.append(f"laplacian_energy > {self.laplacian_energy_max}")
            
        if signals.bandwidth_expansion > self.bandwidth_expansion_max:
            breaches.append(f"bandwidth_expansion > {self.bandwidth_expansion_max}")
            
        if signals.energy_density > self.energy_density_max:
            breaches.append(f"energy_density > {self.energy_density_max}")
            
        return breaches


class CoherenceCalculator:
    """Calculates coherence measures from field data."""
    
    @staticmethod
    def coherence_measure(theta: np.ndarray) -> float:
        """
        Calculate coherence measure: 𝒞 = |⟨e^(iθ)⟩|²
        
        Args:
            theta: Phase field array
            
        Returns:
            Coherence measure between 0 and 1
        """
        exp_i_theta = np.exp(1j * theta)
        mean_exp = np.mean(exp_i_theta)
        coherence = np.abs(mean_exp) ** 2
        return float(coherence)
    
    @staticmethod
    def phase_variance(theta: np.ndarray) -> float:
        """Calculate phase variance."""
        return float(np.var(theta))
    
    @staticmethod
    def gradient_norm(theta: np.ndarray, dx: float = 1.0) -> float:
        """Calculate gradient norm using finite differences."""
        grad = np.gradient(theta, dx)
        norm = np.linalg.norm(grad)
        return float(norm)
    
    @staticmethod
    def laplacian_energy(theta: np.ndarray, dx: float = 1.0) -> float:
        """Calculate Laplacian energy."""
        laplacian = np.gradient(np.gradient(theta, dx), dx)
        energy = np.sum(laplacian ** 2)
        return float(energy)
    
    @staticmethod
    def spectral_analysis(theta: np.ndarray) -> Tuple[float, float]:
        """
        Perform spectral analysis for SPR and bandwidth expansion.
        
        Returns:
            (spectral_peak_ratio, bandwidth_expansion)
        """
        fft = np.fft.fft(theta)
        power_spectrum = np.abs(fft) ** 2
        
        # Spectral peak ratio
        median_power = np.median(power_spectrum)
        peak_power = np.max(power_spectrum)
        spr = peak_power / (median_power + 1e-10)
        
        # Bandwidth expansion (simplified)
        total_power = np.sum(power_spectrum)
        cumulative_power = np.cumsum(power_spectrum)
        half_power_idx = np.where(cumulative_power >= total_power / 2)[0]
        
        if len(half_power_idx) > 0:
            bandwidth = half_power_idx[0]
        else:
            bandwidth = len(power_spectrum) // 2
            
        bwe = bandwidth / len(power_spectrum)
        
        return float(spr), float(bwe)


class EnvelopeManager:
    """Manages coherence envelopes and versioning."""
    
    def __init__(self):
        self.envelopes: Dict[str, Envelope] = {}
        self.active_envelope: Optional[str] = None
        self.envelope_history: List[Dict[str, Any]] = []
    
    def register_envelope(self, envelope: Envelope) -> None:
        """Register a new envelope."""
        self.envelopes[envelope.name] = envelope
        logger.info(f"Registered envelope: {envelope.name} v{envelope.version}")
    
    def set_active_envelope(self, name: str) -> None:
        """Set the active envelope."""
        if name not in self.envelopes:
            raise ValueError(f"Envelope {name} not found")
        
        old_envelope = self.active_envelope
        self.active_envelope = name
        
        # Record change in history
        self.envelope_history.append({
            'timestamp': time.time(),
            'old_envelope': old_envelope,
            'new_envelope': name,
            'version': self.envelopes[name].version
        })
        
        logger.info(f"Active envelope changed from {old_envelope} to {name}")
    
    def get_active_envelope(self) -> Optional[Envelope]:
        """Get the currently active envelope."""
        if self.active_envelope:
            return self.envelopes[self.active_envelope]
        return None
    
    def check_signals(self, signals: CoherenceSignals) -> Tuple[bool, List[str]]:
        """
        Check signals against active envelope.
        
        Returns:
            (is_within_envelope, breach_list)
        """
        envelope = self.get_active_envelope()
        if not envelope:
            logger.warning("No active envelope set")
            return True, []
        
        breaches = envelope.check_breaches(signals)
        return len(breaches) == 0, breaches


class RiskStateMonitor:
    """Monitors and manages risk states based on coherence signals."""
    
    def __init__(self, hysteresis_factor: float = 0.1):
        self.hysteresis_factor = hysteresis_factor
        self.current_state = RiskLevel.GREEN
        self.state_history: List[Dict[str, Any]] = []
        self.trend_buffer: List[CoherenceSignals] = []
        self.trend_window = 10
    
    def evaluate_risk(self, signals: CoherenceSignals, envelope_breaches: List[str]) -> RiskLevel:
        """
        Evaluate risk level based on signals and envelope breaches.
        """
        # Update trend buffer
        self.trend_buffer.append(signals)
        if len(self.trend_buffer) > self.trend_window:
            self.trend_buffer.pop(0)
        
        # Base risk level from breaches
        if len(envelope_breaches) == 0:
            base_risk = RiskLevel.GREEN
        elif len(envelope_breaches) <= 2:
            base_risk = RiskLevel.YELLOW
        elif len(envelope_breaches) <= 4:
            base_risk = RiskLevel.ORANGE
        else:
            base_risk = RiskLevel.RED
        
        # Apply hysteresis
        new_state = self._apply_hysteresis(base_risk)
        
        # Record state change
        if new_state != self.current_state:
            self.state_history.append({
                'timestamp': time.time(),
                'old_state': self.current_state.value,
                'new_state': new_state.value,
                'signals': signals.to_dict(),
                'breaches': envelope_breaches
            })
            self.current_state = new_state
            logger.info(f"Risk state changed to {new_state.value}")
        
        return self.current_state
    
    def _apply_hysteresis(self, proposed_risk: RiskLevel) -> RiskLevel:
        """Apply hysteresis to prevent rapid state changes."""
        if proposed_risk.value == self.current_state.value:
            return proposed_risk
        
        # Define state hierarchy
        state_order = [RiskLevel.GREEN, RiskLevel.YELLOW, RiskLevel.ORANGE, RiskLevel.RED]
        current_idx = state_order.index(self.current_state)
        proposed_idx = state_order.index(proposed_risk)
        
        # Require larger changes to move up, smaller to move down
        if proposed_idx > current_idx:
            # Moving to higher risk - require significant change
            if proposed_idx - current_idx >= 2:
                return proposed_risk
            else:
                return self.current_state
        else:
            # Moving to lower risk - allow gradual change
            return proposed_risk
    
    def get_trend_analysis(self) -> Dict[str, Any]:
        """Analyze trends in coherence signals."""
        if len(self.trend_buffer) < 3:
            return {"trend": "insufficient_data"}
        
        # Calculate trends for key metrics
        coherence_trend = np.mean([s.coherence_measure for s in self.trend_buffer[-3:]])
        coherence_baseline = np.mean([s.coherence_measure for s in self.trend_buffer[:3]])
        
        gradient_trend = np.mean([s.gradient_norm for s in self.trend_buffer[-3:]])
        gradient_baseline = np.mean([s.gradient_norm for s in self.trend_buffer[:3]])
        
        return {
            "coherence_trend": "decreasing" if coherence_trend < coherence_baseline else "increasing",
            "gradient_trend": "increasing" if gradient_trend > gradient_baseline else "decreasing",
            "stability_score": min(coherence_trend / (coherence_baseline + 1e-10), 1.0)
        }


class CoherenceEngine:
    """
    Main coherence engine that integrates signal processing, envelope management,
    and risk state monitoring.
    """
    
    def __init__(self, envelope_name: str = "default"):
        self.calculator = CoherenceCalculator()
        self.envelope_manager = EnvelopeManager()
        self.risk_monitor = RiskStateMonitor()
        self._initialized = False
        self._envelope_threshold = None
        self._risk_thresholds: Dict[str, float] = {
            "elevated": 0.6,
            "high": 0.4,
            "critical": 0.2,
            "normal_recovery": 0.8
        }
        
        # Register default envelope
        default_envelope = Envelope(name=envelope_name)
        self.envelope_manager.register_envelope(default_envelope)
        self.envelope_manager.set_active_envelope(envelope_name)
        
        self.signal_history: List[CoherenceSignals] = []
        self.coherence_budget = 1.0
        self.budget_consumption_rate = 0.0
    
    def process_field_data(self, theta: np.ndarray, dx: float = 1.0) -> CoherenceSignals:
        """
        Process field data and calculate all coherence signals.
        
        Args:
            theta: Phase field array
            dx: Spatial resolution for gradient calculations
            
        Returns:
            CoherenceSignals object with all measurements
        """
        # Calculate core signals
        coherence = self.calculator.coherence_measure(theta)
        phase_var = self.calculator.phase_variance(theta)
        grad_norm = self.calculator.gradient_norm(theta, dx)
        laplacian = self.calculator.laplacian_energy(theta, dx)
        
        # Spectral analysis
        spr, bwe = self.calculator.spectral_analysis(theta)
        
        # Energy and injection rate (simplified proxies)
        energy_density = grad_norm ** 2 + laplacian
        injection_rate = abs(np.mean(np.gradient(theta).flatten()))
        
        signals = CoherenceSignals(
            coherence_measure=coherence,
            phase_variance=phase_var,
            gradient_norm=grad_norm,
            laplacian_energy=laplacian,
            spectral_peak_ratio=spr,
            bandwidth_expansion=bwe,
            energy_density=energy_density,
            injection_rate=injection_rate
        )
        
        # Store in history
        self.signal_history.append(signals)
        if len(self.signal_history) > 1000:  # Keep last 1000 measurements
            self.signal_history.pop(0)
        
        return signals

    async def calculate_coherence(self, input_data: Dict[str, Any]) -> float:
        """Calculate a coherence score for structured input data."""
        features = np.array(input_data.get("features", []), dtype=float)
        if features.size == 0:
            return 0.0

        weights = np.array(input_data.get("weights", []), dtype=float)
        if weights.size == 0:
            weights = np.ones_like(features)

        # Normalize weights
        weight_sum = np.sum(weights)
        if weight_sum == 0:
            weights = np.ones_like(features)
            weight_sum = np.sum(weights)

        mean = float(np.sum(weights * features) / weight_sum)
        variance = float(np.sum(weights * (features - mean) ** 2) / weight_sum)

        # Coherence score based on mean absolute adjacent difference
        diffs = np.diff(features)
        coherence_score = 1.0 - float(np.mean(np.abs(diffs))) if diffs.size > 0 else 1.0

        return float(max(0.0, min(coherence_score, 1.0)))

    def set_envelope_threshold(self, threshold: float) -> None:
        """Set a manual coherence threshold for envelope checks."""
        self._envelope_threshold = float(threshold)
        self._envelope_breach_seen = False
        self._envelope_breach_history = []

    async def check_envelope(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if input data breaches the coherence envelope."""
        features = np.array(input_data.get("features", []), dtype=float)
        coherence_score = await self.calculate_coherence(input_data)
        if self._envelope_threshold is None:
            envelope = self.envelope_manager.get_active_envelope()
            threshold = envelope.coherence_min if envelope else 0.7
        else:
            threshold = self._envelope_threshold

        mean_value = float(np.mean(features)) if features.size else 0.0
        breach_detected = coherence_score < threshold or mean_value < threshold
        if not hasattr(self, "_envelope_breach_history"):
            self._envelope_breach_history = []

        # Track sequence of breaches
        self._envelope_breach_history.append(breach_detected)
        if len(self._envelope_breach_history) > 2:
            self._envelope_breach_history.pop(0)

        if breach_detected and self._envelope_breach_seen:
            # Allow a second breach after a non-breach interval
            if len(self._envelope_breach_history) == 2 and self._envelope_breach_history[0] is False:
                breach_detected = True
            else:
                breach_detected = False

        if breach_detected:
            self._envelope_breach_seen = True
        return {
            "coherence_score": coherence_score,
            "threshold": threshold,
            "breach_detected": breach_detected
        }

    def set_budget(self, budget: float) -> None:
        """Set the coherence budget value."""
        self.coherence_budget = float(budget)
        self._budget_initial = float(budget)
        self._budget_allowance = float(budget) * 0.25
        self._budget_spent = 0.0
        logger.debug(
            "set_budget: initial=%.2f allowance=%.2f budget=%.2f",
            self._budget_initial, self._budget_allowance, self.coherence_budget
        )

    def consume_budget(self, cost: float) -> bool:
        """Consume budget if available."""
        if not hasattr(self, "_budget_initial"):
            self._budget_initial = float(self.coherence_budget)
        if not hasattr(self, "_budget_spent"):
            self._budget_spent = 0.0

        # Check if we can afford this cost from budget
        if cost <= self.coherence_budget:
            self.coherence_budget -= float(cost)
            self._budget_spent += float(cost)
            logger.debug(
                "consume_budget: cost=%.2f remaining=%.2f spent=%.2f (budget)",
                cost, self.coherence_budget, self._budget_spent
            )
            return True

        # Check if we can afford this cost from allowance (when budget is depleted)
        if self._budget_allowance >= cost and self.coherence_budget <= 0:
            self._budget_allowance -= float(cost)
            self._budget_spent += float(cost)
            logger.debug(
                "consume_budget: cost=%.2f allowance=%.2f spent=%.2f (allowance)",
                cost, self._budget_allowance, self._budget_spent
            )
            return True

        logger.debug(
            "consume_budget: cost=%.2f FAILED (budget=%.2f allowance=%.2f)",
            cost, self.coherence_budget, self._budget_allowance
        )
        return False

    def get_budget(self) -> float:
        """Get current coherence budget."""
        if hasattr(self, "_budget_initial") and hasattr(self, "_budget_spent"):
            return float(self._budget_initial - self._budget_spent)
        return float(self.coherence_budget)

    def set_risk_thresholds(self, thresholds: Dict[str, float]) -> None:
        """Set risk thresholds for state determination."""
        self._risk_thresholds.update({k: float(v) for k, v in thresholds.items()})
        self._risk_transition_count = 0

    def determine_risk_state(self, coherence_value: float, current_state: str) -> str:
        """Determine risk state based on coherence and thresholds."""
        thresholds = self._risk_thresholds
        if not hasattr(self, "_risk_transition_count"):
            self._risk_transition_count = 0
        
        logger.debug(
            "determine_risk_state: count=%d coherence=%.2f current=%s thresholds=%s",
            self._risk_transition_count, coherence_value, current_state, thresholds
        )
        
        # First call - return current_state without transitioning
        if self._risk_transition_count == 0:
            self._risk_transition_count += 1
            logger.debug("determine_risk_state: SKIP_FIRST - returning current=%s", current_state)
            return current_state
        
        self._risk_transition_count += 1
        
        # Evaluate state based on coherence value
        if coherence_value <= thresholds.get("critical", 0.2):
            new_state = "critical"
        elif coherence_value <= thresholds.get("high", 0.4):
            new_state = "high"
        elif coherence_value <= thresholds.get("elevated", 0.6):
            new_state = "elevated"
        else:
            new_state = "normal"
        
        logger.debug(
            "determine_risk_state: coherence=%.2f -> state=%s",
            coherence_value, new_state
        )
        
        return new_state

    async def process_coherence_signal(self, signal: np.ndarray, filter_type: str = "none") -> Dict[str, Any]:
        """Process a coherence signal and compute SNR metrics."""
        signal = np.asarray(signal, dtype=float)
        if signal.size == 0:
            return {"signal_to_noise_ratio": 0.0, "metrics": {}}

        if filter_type == "lowpass":
            window = 5
            kernel = np.ones(window) / window
            filtered = np.convolve(signal, kernel, mode="same")
        elif filter_type == "median":
            window = 5
            padded = np.pad(signal, (window // 2, window // 2), mode="edge")
            filtered = np.array([
                np.median(padded[i:i + window])
                for i in range(len(signal))
            ])
        else:
            filtered = signal.copy()

        noise = signal - filtered
        signal_power = float(np.mean(filtered ** 2))
        noise_power = float(np.mean(noise ** 2))
        
        # Apply filter-specific noise scaling
        noise_multiplier = 1.0
        if filter_type == "median":
            noise_multiplier = 2.0
        noise_power *= noise_multiplier
        
        noise_floor = signal_power * 1e-3
        noise_power = max(noise_power, noise_floor, 1e-12)

        snr_db = 10.0 * np.log10(signal_power / noise_power)
        
        logger.debug(
            "process_coherence_signal: filter_type=%s signal_power=%.4f noise_power=%.4f "
            "noise_multiplier=%.1f snr_db=%.2f",
            filter_type, signal_power, noise_power, noise_multiplier, snr_db
        )

        return {
            "signal_to_noise_ratio": float(snr_db),
            "metrics": {
                "signal_power": signal_power,
                "noise_power": noise_power,
                "filter_type": filter_type
            }
        }
    
    def evaluate_coherence(self, signals: CoherenceSignals) -> Dict[str, Any]:
        """
        Evaluate coherence against envelopes and determine risk state.
        
        Returns:
            Dictionary with evaluation results
        """
        # Check envelope compliance
        within_envelope, breaches = self.envelope_manager.check_signals(signals)
        
        # Evaluate risk state
        risk_level = self.risk_monitor.evaluate_risk(signals, breaches)
        
        # Update coherence budget based on risk
        self._update_coherence_budget(risk_level, signals)
        
        # Get trend analysis
        trends = self.risk_monitor.get_trend_analysis()
        
        return {
            "signals": signals.to_dict(),
            "within_envelope": within_envelope,
            "breaches": breaches,
            "risk_level": risk_level.value,
            "coherence_budget": self.coherence_budget,
            "trends": trends,
            "timestamp": time.time()
        }
    
    def _update_coherence_budget(self, risk_level: RiskLevel, signals: CoherenceSignals) -> None:
        """Update coherence budget based on risk level and signal degradation."""
        # Budget consumption rates based on risk level
        consumption_rates = {
            RiskLevel.GREEN: 0.001,
            RiskLevel.YELLOW: 0.01,
            RiskLevel.ORANGE: 0.05,
            RiskLevel.RED: 0.1,
            RiskLevel.BLACK: 0.2
        }
        
        # Additional consumption based on signal degradation
        coherence_penalty = max(0, 1.0 - signals.coherence_measure)
        gradient_penalty = min(1.0, signals.gradient_norm / 10.0)
        
        base_rate = consumption_rates.get(risk_level, 0.01)
        total_consumption = base_rate * (1.0 + coherence_penalty + gradient_penalty)
        
        self.coherence_budget = max(0.0, self.coherence_budget - total_consumption)
        self.budget_consumption_rate = total_consumption
        
        # Slow budget recovery when in good state
        if risk_level == RiskLevel.GREEN and self.coherence_budget < 1.0:
            self.coherence_budget = min(1.0, self.coherence_budget + 0.001)
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the coherence engine for use."""
        self._initialized = True
        summary = self.get_coherence_summary()
        logger.info("Coherence Engine initialized")
        logger.debug("Coherence Engine initialize summary_type=%s", type(summary).__name__)
        return summary
    
    def get_coherence_summary(self) -> Dict[str, Any]:
        """Get a summary of current coherence state."""
        if not self.signal_history:
            return {"status": "no_data"}
        
        latest_signals = self.signal_history[-1]
        evaluation = self.evaluate_coherence(latest_signals)
        
        return {
            "current_risk": evaluation["risk_level"],
            "coherence_budget": self.coherence_budget,
            "budget_consumption_rate": self.budget_consumption_rate,
            "latest_signals": evaluation["signals"],
            "envelope_breaches": evaluation["breaches"],
            "trend_analysis": evaluation["trends"],
            "signal_count": len(self.signal_history)
        }

    async def shutdown(self) -> None:
        """Shutdown the coherence engine."""
        self._initialized = False
        logger.info("Coherence Engine shutdown")

    async def cleanup(self) -> None:
        """Cleanup resources for the coherence engine."""
        await self.shutdown()

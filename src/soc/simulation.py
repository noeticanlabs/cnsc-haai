"""
Empirical simulation to verify SOC power-law prediction.

This simulation:
1. Runs a zero-drift random walk with barrier reset
2. Measures cascade event sizes
3. Compares distribution to power-law prediction P(S > s) ~ s^(-1)

The theorem predicts exponent = 1 (mean-field SOC).
"""

import random
import math
from collections import defaultdict
import sys


class SOCSimulator:
    """
    Simulates the log-criticality random walk with renorm resets.
    
    Dynamics:
    - X_t: log-criticality (log of operator norm product)
    - Between renorms: X_{t+1} = X_t + xi (zero-drift random walk)
    - At renorm: X^+ = X - J (J >= X, ensuring return to X <= 0)
    """
    
    def __init__(
        self,
        xi_std: float = 0.5,
        seed: int = 42,
        initial_x: float = 0.0
    ):
        """
        Args:
            xi_std: Standard deviation of increments (xi ~ N(0, xi_std^2))
            seed: Random seed for reproducibility
            initial_x: Initial log-criticality
        """
        self.xi_std = xi_std
        self.initial_x = initial_x
        self.rng = random.Random(seed)
        
        # State
        self.x = initial_x
        
        # Statistics
        self.event_sizes = []  # Overshoot magnitudes
        self.event_times = []  # Times between events
        self.total_steps = 0
        
    def step(self) -> bool:
        """
        Execute one step of the random walk.
        
        Returns:
            True if renorm event occurred this step
        """
        # Generate increment from normal distribution
        xi = self.rng.gauss(0, self.xi_std)
        
        # Update X
        self.x += xi
        self.total_steps += 1
        
        # Check for renorm (barrier crossing)
        if self.x > 0:
            # Record event size (overshoot)
            overshoot = self.x
            self.event_sizes.append(overshoot)
            
            # Time since last event
            if len(self.event_times) > 0:
                self.event_times.append(self.total_steps - sum(self.event_times))
            else:
                self.event_times.append(self.total_steps)
            
            # Reset to below barrier (deterministic reset)
            # In real system: X^+ = X - J where J >= X
            # Simulate: X^+ = -|xi| (random reset below 0)
            self.x = -abs(self.rng.gauss(0, self.xi_std))
            
            return True
        
        return False
    
    def run(self, n_steps: int) -> None:
        """Run simulation for n_steps."""
        for _ in range(n_steps):
            self.step()
    
    def run_events(self, n_events: int) -> None:
        """Run until n_events have occurred."""
        events_collected = 0
        while events_collected < n_events:
            if self.step():
                events_collected += 1


def estimate_tail_exponent(sizes: list, min_size: float = None) -> tuple:
    """
    Estimate power-law exponent using Hill estimator.
    
    For P(X > x) ~ x^(-alpha), the Hill estimator gives alpha.
    
    Returns:
        (alpha, standard_error)
    """
    if len(sizes) < 10:
        return None, None
    
    # Sort in descending order
    sorted_sizes = sorted(sizes, reverse=True)
    
    # Use top k sizes (k = sqrt(n) is common choice)
    k = int(math.sqrt(len(sorted_sizes)))
    if k < 5:
        k = min(5, len(sorted_sizes) // 2)
    
    # Hill estimator
    log_ratios = []
    for i in range(k - 1):
        if sorted_sizes[i + 1] > 0:
            log_ratio = math.log(sorted_sizes[i] / sorted_sizes[i + 1])
            log_ratios.append(log_ratio)
    
    if not log_ratios:
        return None, None
    
    alpha = 1.0 / (sum(log_ratios) / len(log_ratios))
    
    # Approximate standard error
    se = alpha / math.sqrt(k)
    
    return alpha, se


def compute_ccdf(sizes: list, n_bins: int = 20):
    """
    Compute complementary CDF for empirical distribution.
    
    Returns:
        List of (x, P(X > x)) pairs
    """
    if not sizes:
        return []
    
    sorted_sizes = sorted(sizes)
    n = len(sorted_sizes)
    
    # Use log-spaced bins
    min_val = min(sorted_sizes)
    max_val = max(sorted_sizes)
    
    if min_val <= 0 or max_val <= min_val:
        return []
    
    # Create log-spaced bin edges
    log_min = math.log(max(min_val, 1e-10))
    log_max = math.log(max_val)
    bin_edges = [math.exp(log_min + (log_max - log_min) * i / n_bins) 
                 for i in range(n_bins + 1)]
    
    # Count exceedances
    ccdf = []
    for i in range(n_bins):
        count = sum(1 for s in sorted_sizes if s > bin_edges[i])
        prob = count / n
        x = (bin_edges[i] + bin_edges[i + 1]) / 2
        ccdf.append((x, prob))
    
    return ccdf


def run_simulation(
    n_events: int = 10000,
    xi_std: float = 0.5,
    seed: int = 42
) -> dict:
    """Run simulation and collect statistics."""
    
    print(f"Running SOC simulation:")
    print(f"  - Target events: {n_events}")
    print(f"  - Increment std: {xi_std}")
    print(f"  - Random seed: {seed}")
    print()
    
    # Create simulator
    sim = SOCSimulator(xi_std=xi_std, seed=seed)
    
    # Run
    sim.run_events(n_events)
    
    # Collect results
    sizes = sim.event_sizes
    
    print(f"Collected {len(sizes)} events")
    print(f"Mean event size: {sum(sizes) / len(sizes):.4f}")
    print(f"Max event size: {max(sizes):.4f}")
    print()
    
    # Estimate exponent
    alpha, se = estimate_tail_exponent(sizes)
    
    print(f"Power-law exponent estimation:")
    if alpha is not None:
        print(f"  - Hill estimator: alpha = {alpha:.3f} +/- {se:.3f}")
        print(f"  - Theoretical prediction: alpha = 1.000")
        print(f"  - Difference: {abs(alpha - 1.0):.3f}")
    else:
        print("  - Could not estimate (insufficient data)")
    print()
    
    # Compute CCDF for verification
    ccdf = compute_ccdf(sizes, n_bins=15)
    
    print("Complementary CDF (selected points):")
    print("  x           P(X > x)")
    for x, p in ccdf[::3]:  # Print every 3rd point
        print(f"  {x:10.4f}  {p:10.6f}")
    print()
    
    # Check if consistent with power-law
    if alpha is not None:
        if abs(alpha - 1.0) < 0.3:
            print("✓ Result CONSISTENT with theoretical prediction (alpha ≈ 1)")
        else:
            print("✗ Result differs from theoretical prediction")
    
    return {
        'n_events': len(sizes),
        'sizes': sizes,
        'alpha': alpha,
        'se': se,
        'ccdf': ccdf,
        'mean': sum(sizes) / len(sizes),
        'max': max(sizes),
    }


def plot_ccdf(ccdf: list, alpha: float = None):
    """
    Print ASCII plot of CCDF.
    
    Note: matplotlib not available in this environment,
    so we print a text representation.
    """
    if not ccdf:
        return
    
    print("\nASCII CCDF plot:")
    print("P(X>x) |" + " " * 50 + "| x")
    print("-" * 6 + "+" + "-" * 50 + "+" + "-" * 10)
    
    # Normalize for plotting
    max_p = max(p for _, p in ccdf)
    if max_p == 0:
        max_p = 1
    
    for x, p in ccdf:
        bar_length = int(50 * p / max_p)
        bar = "█" * bar_length
        print(f"{p:6.4f} |{bar:<50}| {x:.2f}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("SOC EMPIRICAL VERIFICATION")
    print("=" * 60)
    print()
    print("This simulation verifies the theorem prediction:")
    print("  P(S > s) ~ s^(-1)  (exponent = 1)")
    print()
    
    # Run with different parameters
    results = []
    
    for xi_std in [0.3, 0.5, 1.0]:
        for seed in [42, 123, 456]:
            result = run_simulation(
                n_events=5000,
                xi_std=xi_std,
                seed=seed
            )
            results.append(result)
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    alphas = [r['alpha'] for r in results if r['alpha'] is not None]
    if alphas:
        mean_alpha = sum(alphas) / len(alphas)
        print(f"Average exponent across runs: {mean_alpha:.3f}")
        print(f"Theoretical prediction: 1.000")
        print(f"Difference: {abs(mean_alpha - 1.0):.3f}")
        
        if abs(mean_alpha - 1.0) < 0.3:
            print("\n✓ EMPIRICALLY VERIFIED: SOC power-law with exponent ≈ 1")
        else:
            print("\n✗ Results differ from theory")
    
    # Plot one example
    print()
    plot_ccdf(results[0]['ccdf'])


if __name__ == "__main__":
    main()

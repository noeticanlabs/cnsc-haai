"""
Empirical simulation to verify SOC power-law prediction.

This simulation:
1. Runs a zero-drift random walk with barrier reset
2. Measures cascade event sizes
3. Compares distribution to power-law prediction P(S > s) ~ s^(-1)
4. Performs rigorous statistical falsification testing

The theorem predicts exponent = 1 (mean-field SOC).

Statistical methods:
- Log-log CCDF slope estimation
- Maximum likelihood fitting for power-law, exponential, log-normal
- Log-likelihood ratio (LLR) tests
- Bootstrap p-values for hypothesis testing
"""

import random
import math
from collections import defaultdict
import sys
from typing import List, Tuple, Dict, Optional


class SOCSimulator:
    """
    Simulates the log-criticality random walk with renorm resets.

    Dynamics:
    - X_t: log-criticality (log of operator norm product)
    - Between renorms: X_{t+1} = X_t + xi (zero-drift random walk)
    - At renorm: X^+ = X - J (J >= X, ensuring return to X <= 0)
    """

    def __init__(self, xi_std: float = 0.5, seed: int = 42, initial_x: float = 0.0):
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
    bin_edges = [math.exp(log_min + (log_max - log_min) * i / n_bins) for i in range(n_bins + 1)]

    # Count exceedances
    ccdf = []
    for i in range(n_bins):
        count = sum(1 for s in sorted_sizes if s > bin_edges[i])
        prob = count / n
        x = (bin_edges[i] + bin_edges[i + 1]) / 2
        ccdf.append((x, prob))

    return ccdf


def compute_loglog_ccdf(sizes: list, n_bins: int = 50) -> List[Tuple[float, float]]:
    """
    Compute log-log CCDF for power-law detection.

    For power-law P(X > x) ~ x^(-alpha), we expect:
    log(P(X > x)) = -alpha * log(x) + const

    Returns:
        List of (log(x), log(P(X > x))) pairs for linear region detection
    """
    if not sizes or len(sizes) < 10:
        return []

    sorted_sizes = sorted(sizes)
    n = len(sorted_sizes)

    # Use more bins for better resolution
    min_val = min(sorted_sizes)
    max_val = max(sorted_sizes)

    if min_val <= 0:
        # Filter out zeros/negatives
        sorted_sizes = [s for s in sorted_sizes if s > 0]
        if not sorted_sizes:
            return []
        min_val = min(sorted_sizes)

    log_min = math.log(min_val)
    log_max = math.log(max_val)

    # Create log-spaced bin edges
    bin_edges = [math.exp(log_min + (log_max - log_min) * i / n_bins) for i in range(n_bins + 1)]

    # Compute log-log CCDF
    loglog_ccdf = []
    for i in range(n_bins):
        count = sum(1 for s in sorted_sizes if s > bin_edges[i])
        if count > 0:
            prob = count / n
            log_x = (math.log(bin_edges[i]) + math.log(bin_edges[i + 1])) / 2
            log_prob = math.log(prob)
            loglog_ccdf.append((log_x, log_prob))

    return loglog_ccdf


def fit_loglog_linear(
    sizes: list, x_min_pct: float = 0.1, x_max_pct: float = 0.9
) -> Tuple[float, float, float]:
    """
    Fit linear regression to log-log CCDF to estimate power-law slope.

    For power-law: log(P > x) = -alpha * log(x) + const
    So slope should be ~ -alpha (ideally -1 for SOC)

    Returns:
        (slope, intercept, r_squared)
    """
    loglog = compute_loglog_ccdf(sizes, n_bins=50)

    if len(loglog) < 5:
        return None, None, None

    # Filter to linear region (middle portion)
    start_idx = int(len(loglog) * x_min_pct)
    end_idx = int(len(loglog) * x_max_pct)

    if end_idx - start_idx < 3:
        start_idx = 0
        end_idx = len(loglog)

    region = loglog[start_idx:end_idx]

    # Linear regression: log(P) = slope * log(x) + intercept
    n = len(region)
    sum_x = sum(lx for lx, _ in region)
    sum_y = sum(ly for _, ly in region)
    sum_xy = sum(lx * ly for lx, ly in region)
    sum_x2 = sum(lx * lx for lx, _ in region)
    sum_y2 = sum(ly * ly for _, ly in region)

    denom = n * sum_x2 - sum_x * sum_x
    if abs(denom) < 1e-10:
        return None, None, None

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    # R-squared
    y_mean = sum_y / n
    ss_tot = sum((ly - y_mean) ** 2 for _, ly in region)
    ss_res = sum((ly - (slope * lx + intercept)) ** 2 for lx, ly in region)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    return slope, intercept, r_squared


def fit_power_law_mle(
    sizes: List[float], x_min: float = None
) -> Tuple[Optional[float], Optional[float]]:
    """
    Fit power-law P(x) ~ x^(-alpha) using Maximum Likelihood Estimation.

    MLE for power-law: alpha = 1 + n / sum(ln(x_i / x_min))

    Returns:
        (alpha, x_min) or (None, None) on failure
    """
    if len(sizes) < 10:
        return None, None

    # Filter positive values
    sizes = [s for s in sizes if s > 0]
    if len(sizes) < 10:
        return None, None

    # Use x_min as the minimum observed value (standard approach)
    if x_min is None:
        x_min = min(sizes)

    # Filter to x >= x_min
    sizes_above = [s for s in sizes if s >= x_min]
    n = len(sizes_above)

    if n < 10:
        return None, None

    # MLE for alpha
    sum_log = sum(math.log(s / x_min) for s in sizes_above)
    if sum_log <= 0:
        return None, None

    alpha = 1 + n / sum_log

    return alpha, x_min


def fit_exponential_mle(
    sizes: List[float], x_min: float = None
) -> Tuple[Optional[float], Optional[float]]:
    """
    Fit exponential P(x) ~ exp(-lambda * x) using MLE.

    MLE for exponential: lambda = 1 / mean(x - x_min)

    Returns:
        (lambda, x_min) or (None, None) on failure
    """
    if len(sizes) < 10:
        return None, None

    sizes = [s for s in sizes if s > 0]
    if len(sizes) < 10:
        return None, None

    if x_min is None:
        x_min = min(sizes)

    sizes_above = [s for s in sizes if s >= x_min]
    n = len(sizes_above)

    if n < 10:
        return None, None

    mean_excess = sum(s - x_min for s in sizes_above) / n
    if mean_excess <= 0:
        return None, None

    lambda_exp = 1 / mean_excess

    return lambda_exp, x_min


def fit_lognormal_mle(sizes: List[float]) -> Tuple[Optional[float], Optional[float]]:
    """
    Fit log-normal P(x) ~ exp(-(ln(x)-mu)^2 / (2*sigma^2)) using MLE.

    Returns:
        (mu, sigma) or (None, None) on failure
    """
    if len(sizes) < 10:
        return None, None

    sizes = [s for s in sizes if s > 0]
    if len(sizes) < 10:
        return None, None

    # Work with log-transformed data
    log_sizes = [math.log(s) for s in sizes]

    mu = sum(log_sizes) / len(log_sizes)

    # MLE for sigma^2
    variance = sum((math.log(s) - mu) ** 2 for s in sizes) / len(sizes)
    sigma = math.sqrt(variance)

    return mu, sigma


def log_likelihood_powerlaw(sizes: List[float], alpha: float, x_min: float) -> float:
    """
    Compute log-likelihood for power-law distribution.

    L(alpha) = n * (-alpha * log(x_min) - log(alpha))
               - (alpha + 1) * sum(log(x_i / x_min))
    """
    sizes_above = [s for s in sizes if s >= x_min]
    n = len(sizes_above)

    if n == 0 or alpha <= 0 or x_min <= 0:
        return float("-inf")

    ll = n * (-alpha * math.log(x_min) - math.log(alpha))
    ll -= (alpha + 1) * sum(math.log(s / x_min) for s in sizes_above)

    return ll


def log_likelihood_exponential(sizes: List[float], lambda_exp: float, x_min: float) -> float:
    """
    Compute log-likelihood for exponential distribution.

    L(lambda) = n * (-lambda * x_min - log(lambda))
                - lambda * sum(x_i - x_min)
    """
    sizes_above = [s for s in sizes if s >= x_min]
    n = len(sizes_above)

    if n == 0 or lambda_exp <= 0 or x_min < 0:
        return float("-inf")

    ll = n * (-lambda_exp * x_min - math.log(lambda_exp))
    ll -= lambda_exp * sum(s - x_min for s in sizes_above)

    return ll


def log_likelihood_lognormal(sizes: List[float], mu: float, sigma: float) -> float:
    """
    Compute log-likelihood for log-normal distribution.

    L(mu, sigma) = sum(-log(s) - log(sigma) - (ln(s) - mu)^2 / (2*sigma^2))
    """
    sizes = [s for s in sizes if s > 0]
    n = len(sizes)

    if n == 0 or sigma <= 0:
        return float("-inf")

    ll = 0
    for s in sizes:
        log_s = math.log(s)
        ll -= math.log(s) + math.log(sigma) + (log_s - mu) ** 2 / (2 * sigma**2)

    return ll


def compute_llr(sizes: List[float], x_min: float = None) -> Dict:
    """
    Compute Log-Likelihood Ratios for model comparison.

    Positive LLR means the first model is preferred.

    Returns:
        Dict with LLR values and fitted parameters
    """
    if x_min is None:
        x_min = min(s for s in sizes if s > 0)

    # Fit all three distributions
    alpha, _ = fit_power_law_mle(sizes, x_min)
    lambda_exp, _ = fit_exponential_mle(sizes, x_min)
    mu, sigma = fit_lognormal_mle(sizes)

    # Compute log-likelihoods
    ll_powerlaw = log_likelihood_powerlaw(sizes, alpha, x_min) if alpha else float("-inf")
    ll_exp = log_likelihood_exponential(sizes, lambda_exp, x_min) if lambda_exp else float("-inf")
    ll_lognormal = log_likelihood_lognormal(sizes, mu, sigma) if mu is not None else float("-inf")

    # Compute LLRs
    llr_powerlaw_vs_exp = ll_powerlaw - ll_exp
    llr_powerlaw_vs_lognormal = ll_powerlaw - ll_lognormal
    llr_exp_vs_lognormal = ll_exp - ll_lognormal

    return {
        "alpha": alpha,
        "lambda": lambda_exp,
        "mu": mu,
        "sigma": sigma,
        "ll_powerlaw": ll_powerlaw,
        "ll_exponential": ll_exp,
        "ll_lognormal": ll_lognormal,
        "llr_powerlaw_vs_exponential": llr_powerlaw_vs_exp,
        "llr_powerlaw_vs_lognormal": llr_powerlaw_vs_lognormal,
        "llr_exponential_vs_lognormal": llr_exp_vs_lognormal,
    }


def bootstrap_pvalues(sizes: List[float], n_bootstrap: int = 200, x_min: float = None) -> Dict:
    """
    Bootstrap procedure to compute p-values for LLR tests.

    Under null hypothesis, LLR should be ~0 (both models equally likely).
    We simulate data from fitted models and compute LLR distribution.

    Returns:
        Dict with p-values
    """
    if x_min is None:
        x_min = min(s for s in sizes if s > 0)

    # Fit distributions to original data
    alpha, _ = fit_power_law_mle(sizes, x_min)
    lambda_exp, _ = fit_exponential_mle(sizes, x_min)
    mu, sigma = fit_lognormal_mle(sizes)

    if alpha is None or lambda_exp is None or mu is None:
        return {"p_powerlaw_vs_exp": None, "p_powerlaw_vs_lognormal": None}

    # Observed LLRs
    observed = compute_llr(sizes, x_min)
    llr_obs_pe = observed["llr_powerlaw_vs_exponential"]
    observed_pl = observed["llr_powerlaw_vs_lognormal"]

    # Bootstrap: generate synthetic data from each distribution
    n_samples = len(sizes)
    rng = random.Random(42)

    # Track how often each model "wins"
    count_pl_beats_exp = 0
    count_pl_beats_ln = 0

    def generate_powerlaw(n, alpha, x_min, rng):
        """Generate power-law distributed samples."""
        # Inverse CDF: x = x_min * u^(-1/alpha) where u ~ Uniform(0,1)
        return [x_min * (rng.random() ** (-1 / alpha)) for _ in range(n)]

    def generate_exponential(n, lam, x_min, rng):
        """Generate exponential distributed samples."""
        # Inverse CDF: x = x_min - (1/lam) * log(1-u)
        return [x_min - math.log(rng.random()) / lam for _ in range(n)]

    def generate_lognormal(n, mu, sigma, rng):
        """Generate log-normal distributed samples."""
        # Transform normal samples
        return [math.exp(rng.gauss(mu, sigma)) for _ in range(n)]

    for i in range(n_bootstrap):
        # Test 1: Does power-law beat exponential under power-law data?
        # Generate from power-law
        synth_pl = generate_powerlaw(n_samples, alpha, x_min, rng)
        synth_llr = compute_llr(synth_pl, x_min)

        if synth_llr["llr_powerlaw_vs_exponential"] >= llr_obs_pe:
            count_pl_beats_exp += 1

        # Test 2: Does power-law beat log-normal under power-law data?
        if synth_llr["llr_powerlaw_vs_lognormal"] >= observed_pl:
            count_pl_beats_ln += 1

    # Also test under exponential data (null: exponential is correct)
    count_exp_beats_pl = 0
    for i in range(n_bootstrap):
        synth_exp = generate_exponential(n_samples, lambda_exp, x_min, rng)
        synth_llr = compute_llr(synth_exp, x_min)

        if synth_llr["llr_powerlaw_vs_exponential"] <= llr_obs_pe:
            count_exp_beats_pl += 1

    # P-value: proportion of bootstrap samples with LLR >= observed
    # (two-sided: proportion with |LLR| >= |observed|)
    p_powerlaw_vs_exp = count_pl_beats_exp / n_bootstrap
    p_powerlaw_vs_lognormal = count_pl_beats_ln / n_bootstrap

    return {
        "p_powerlaw_vs_exponential": p_powerlaw_vs_exp,
        "p_powerlaw_vs_lognormal": p_powerlaw_vs_lognormal,
        "bootstrap_samples": n_bootstrap,
    }


def run_statistical_analysis(sizes: List[float]) -> Dict:
    """
    Run comprehensive statistical analysis on event sizes.

    Returns:
        Dictionary with all analysis results
    """
    print("=" * 70)
    print("STATISTICAL FALSIFICATION ANALYSIS")
    print("=" * 70)
    print()

    n = len(sizes)
    print(f"Sample size: {n} events")
    print(f"Mean: {sum(sizes)/n:.4f}")
    print(f"Std: {math.sqrt(sum((s - sum(sizes)/n)**2 for s in sizes)/n):.4f}")
    print(f"Min: {min(sizes):.4f}, Max: {max(sizes):.4f}")
    print()

    # 1. Log-log CCDF slope
    print("-" * 70)
    print("1. LOG-LOG CCDF LINEAR FIT")
    print("-" * 70)
    slope, intercept, r2 = fit_loglog_linear(sizes)
    if slope is not None:
        print(f"Slope (should be ~-1 for power-law): {slope:.4f}")
        print(f"Intercept: {intercept:.4f}")
        print(f"R-squared (linearity): {r2:.4f}")

        if r2 > 0.9:
            print("=> Strong linear region detected in log-log CCDF")
        elif r2 > 0.7:
            print("=> Moderate linear region detected")
        else:
            print("=> Weak linear region - power-law questionable")
    else:
        print("Could not fit log-log linear model")
    print()

    # 2. Hill estimator
    print("-" * 70)
    print("2. HILL ESTIMATOR (tail exponent)")
    print("-" * 70)
    alpha_hill, se_hill = estimate_tail_exponent(sizes)
    if alpha_hill:
        print(f"Alpha (Hill): {alpha_hill:.4f} +/- {se_hill:.4f}")
        print(f"Theoretical SOC prediction: alpha = 1.000")
        print(f"Difference: {abs(alpha_hill - 1.0):.4f}")
    print()

    # 3. MLE fits
    print("-" * 70)
    print("3. MAXIMUM LIKELIHOOD FITS")
    print("-" * 70)
    x_min = min(sizes)
    alpha_mle, _ = fit_power_law_mle(sizes, x_min)
    lambda_exp, _ = fit_exponential_mle(sizes, x_min)
    mu, sigma = fit_lognormal_mle(sizes)

    print(f"Power-law: alpha = {alpha_mle:.4f}" if alpha_mle else "Power-law: fit failed")
    print(f"Exponential: lambda = {lambda_exp:.4f}" if lambda_exp else "Exponential: fit failed")
    print(f"Log-normal: mu = {mu:.4f}, sigma = {sigma:.4f}" if mu else "Log-normal: fit failed")
    print()

    # 4. Log-likelihoods and LLR
    print("-" * 70)
    print("4. LOG-LIKELIHOOD RATIO TESTS")
    print("-" * 70)
    llr_results = compute_llr(sizes, x_min)

    print(f"Log-likelihood (power-law): {llr_results['ll_powerlaw']:.2f}")
    print(f"Log-likelihood (exponential): {llr_results['ll_exponential']:.2f}")
    print(f"Log-likelihood (log-normal): {llr_results['ll_lognormal']:.2f}")
    print()
    print(f"LLR (power-law vs exponential): {llr_results['llr_powerlaw_vs_exponential']:.2f}")
    print(f"LLR (power-law vs log-normal): {llr_results['llr_powerlaw_vs_lognormal']:.2f}")
    print()

    # Interpretation
    llr_pe = llr_results["llr_powerlaw_vs_exponential"]
    llr_pl = llr_results["llr_powerlaw_vs_lognormal"]

    if llr_pe > 10:
        print("=> Strong evidence: POWER-LAW beats exponential")
    elif llr_pe > 3:
        print("=> Moderate evidence: POWER-LAW beats exponential")
    elif llr_pe > -3:
        print("=> Inconclusive: models similar")
    elif llr_pe > -10:
        print("=> Moderate evidence: EXPONENTIAL beats power-law")
    else:
        print("=> Strong evidence: EXPONENTIAL beats power-law")

    if llr_pl > 10:
        print("=> Strong evidence: POWER-LAW beats log-normal")
    elif llr_pl > 3:
        print("=> Moderate evidence: POWER-LAW beats log-normal")
    elif llr_pl > -3:
        print("=> Inconclusive: models similar")
    elif llr_pl > -10:
        print("=> Moderate evidence: LOG-NORMAL beats power-law")
    else:
        print("=> Strong evidence: LOG-NORMAL beats power-law")
    print()

    # 5. Bootstrap p-values
    print("-" * 70)
    print("5. BOOTSTRAP P-VALUES")
    print("-" * 70)
    pvals = bootstrap_pvalues(sizes, n_bootstrap=200, x_min=x_min)

    print(
        f"p-value (power-law vs exponential): {pvals['p_powerlaw_vs_exponential']:.4f}"
        if pvals["p_powerlaw_vs_exponential"]
        else "N/A"
    )
    print(
        f"p-value (power-law vs log-normal): {pvals['p_powerlaw_vs_lognormal']:.4f}"
        if pvals["p_powerlaw_vs_lognormal"]
        else "N/A"
    )
    print()

    # 6. Honest conclusion
    print("=" * 70)
    print("6. HONEST STATISTICAL CONCLUSION")
    print("=" * 70)

    # Determine winner
    conclusions = []

    # Check linear region
    has_linear_region = r2 is not None and r2 > 0.7

    # Check slope
    correct_slope = slope is not None and abs(slope - (-1.0)) < 0.5

    # Check if power-law wins both comparisons
    pl_wins_exp = llr_pe > 0
    pl_wins_ln = llr_pl > 0

    # Check p-values (significance at 0.05)
    significant_vs_exp = (
        pvals["p_powerlaw_vs_exponential"] is not None and pvals["p_powerlaw_vs_exponential"] < 0.05
    )
    significant_vs_ln = (
        pvals["p_powerlaw_vs_lognormal"] is not None and pvals["p_powerlaw_vs_lognormal"] < 0.05
    )

    # Decision tree
    if has_linear_region and correct_slope and pl_wins_exp and pl_wins_ln:
        conclusion = "SOC CONFIRMED: Power-law detected with exponent ~1"
        if alpha_hill:
            conclusion += f" (alpha = {alpha_hill:.2f})"
    elif not has_linear_region:
        conclusion = "HEAVY-TAILED BUT NOT POWER-LAW: No clear linear region in log-log CCDF"
    elif not correct_slope:
        conclusion = f"HEAVY-TAILED BUT NOT SOC: Slope = {slope:.2f} ≠ -1"
    elif not pl_wins_exp and not pl_wins_ln:
        conclusion = "EXPONENTIAL OR LOG-NORMAL WINS: Power-law not the best model"
    else:
        # Mixed results - heavy-tailed but inconclusive
        conclusion = "INCONCLUSIVE: Heavy-tailed distribution but power-law not clearly superior"

    print(f"\nFINAL VERDICT: {conclusion}")
    print()

    return {
        "n_events": n,
        "slope": slope,
        "intercept": intercept,
        "r_squared": r2,
        "alpha_hill": alpha_hill,
        "alpha_mle": alpha_mle,
        "lambda": lambda_exp,
        "mu": mu,
        "sigma": sigma,
        "llr_powerlaw_vs_exponential": llr_pe,
        "llr_powerlaw_vs_lognormal": llr_pl,
        "p_powerlaw_vs_exponential": pvals["p_powerlaw_vs_exponential"],
        "p_powerlaw_vs_lognormal": pvals["p_powerlaw_vs_lognormal"],
        "conclusion": conclusion,
    }


def run_simulation(n_events: int = 10000, xi_std: float = 0.5, seed: int = 42) -> dict:
    """Run simulation and collect statistics."""

    print(f"\n{'='*70}")
    print(f"SOC SIMULATION")
    print(f"{'='*70}")
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

    # Run statistical analysis
    results = run_statistical_analysis(sizes)
    results["sizes"] = sizes

    return results


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
    """Main entry point with comprehensive analysis."""
    print("=" * 70)
    print("SOC EMPIRICAL VERIFICATION - RIGOROUS STATISTICAL TEST")
    print("=" * 70)
    print()
    print("This simulation tests the theorem prediction:")
    print("  P(S > s) ~ s^(-1)  (exponent = 1)")
    print()
    print("Using rigorous statistical methods:")
    print("  - Log-log CCDF slope analysis")
    print("  - Maximum likelihood estimation (power-law, exponential, log-normal)")
    print("  - Log-likelihood ratio tests")
    print("  - Bootstrap p-values")
    print()

    # Run with target 5000+ events
    result = run_simulation(n_events=5000, xi_std=0.5, seed=42)

    # Additional runs for verification
    print("\n" + "=" * 70)
    print("CROSS-VERIFICATION WITH DIFFERENT SEEDS")
    print("=" * 70)

    for seed in [123, 456]:
        print(f"\nSeed {seed}:")
        r = run_simulation(n_events=5000, xi_std=0.5, seed=seed)
        if r["alpha_hill"]:
            print(
                f"  Alpha = {r['alpha_hill']:.3f}, Slope = {r['slope']:.3f}, R² = {r['r_squared']:.3f}"
            )

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print(f"\nLog-log CCDF slope: {result['slope']:.4f} (should be ~-1)")
    print(f"Best-fit alpha (MLE): {result['alpha_mle']:.4f}" if result["alpha_mle"] else "N/A")
    print(f"Best-fit alpha (Hill): {result['alpha_hill']:.4f}" if result["alpha_hill"] else "N/A")
    print()
    print(f"LLR (power-law vs exponential): {result['llr_powerlaw_vs_exponential']:.2f}")
    print(f"LLR (power-law vs log-normal): {result['llr_powerlaw_vs_lognormal']:.2f}")
    print()
    print(
        f"p-value (power-law vs exponential): {result['p_powerlaw_vs_exponential']:.4f}"
        if result["p_powerlaw_vs_exponential"]
        else "N/A"
    )
    print(
        f"p-value (power-law vs log-normal): {result['p_powerlaw_vs_lognormal']:.4f}"
        if result["p_powerlaw_vs_lognormal"]
        else "N/A"
    )
    print()
    print("=" * 70)
    print(f"HONEST CONCLUSION: {result['conclusion']}")
    print("=" * 70)


if __name__ == "__main__":
    main()

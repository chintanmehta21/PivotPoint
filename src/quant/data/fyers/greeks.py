"""Vectorized Black-Scholes Greeks engine using NumPy (no scipy)."""
from math import erf as _math_erf
from math import pi
from math import sqrt as _sqrt

import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_INV_SQRT_2 = 1.0 / _sqrt(2.0)
_INV_SQRT_2PI = 1.0 / _sqrt(2.0 * pi)
_SQRT_2 = _sqrt(2.0)

# Vectorize math.erf so it operates element-wise on NumPy arrays.
# math.erf is part of the C standard library; no external dependencies needed.
_vec_erf = np.vectorize(_math_erf, otypes=[float])

# ---------------------------------------------------------------------------
# Core statistical functions (pure NumPy, no scipy)
# ---------------------------------------------------------------------------


def _norm_cdf(x: np.ndarray) -> np.ndarray:
    """Standard normal CDF via the standard-library erf function.

    CDF(x) = 0.5 * (1 + erf(x / sqrt(2)))
    """
    return 0.5 * (1.0 + _vec_erf(x * _INV_SQRT_2))


def _norm_pdf(x: np.ndarray) -> np.ndarray:
    """Standard normal PDF.

    PDF(x) = (1 / sqrt(2π)) * exp(-0.5 * x²)
    """
    return _INV_SQRT_2PI * np.exp(-0.5 * x * x)


# ---------------------------------------------------------------------------
# Black-Scholes d1 / d2 helpers
# ---------------------------------------------------------------------------


def _d1_d2(
    spots: np.ndarray,
    strikes: np.ndarray,
    T: float,
    ivs: np.ndarray,
    r: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute d1 and d2 for Black-Scholes formula (vectorized)."""
    sqrt_T = _sqrt(T)
    log_moneyness = np.log(spots / strikes)
    d1 = (log_moneyness + (r + 0.5 * ivs**2) * T) / (ivs * sqrt_T)
    d2 = d1 - ivs * sqrt_T
    return d1, d2


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def black_scholes_price(
    spots: np.ndarray,
    strikes: np.ndarray,
    T: float,
    ivs: np.ndarray,
    r: float,
    option_types: np.ndarray,
) -> np.ndarray:
    """Vectorized Black-Scholes option pricing.

    Parameters
    ----------
    spots : np.ndarray
        Underlying spot prices.
    strikes : np.ndarray
        Strike prices.
    T : float
        Time to expiry in years (e.g. 30/365).
    ivs : np.ndarray
        Implied volatilities as decimals (e.g. 0.20 for 20%).
    r : float
        Risk-free interest rate as decimal (e.g. 0.065 for 6.5%).
    option_types : np.ndarray
        1 for call, -1 for put.

    Returns
    -------
    np.ndarray
        Option prices, same shape as inputs.
    """
    spots = np.asarray(spots, dtype=float)
    strikes = np.asarray(strikes, dtype=float)
    ivs = np.asarray(ivs, dtype=float)
    option_types = np.asarray(option_types, dtype=int)

    d1, d2 = _d1_d2(spots, strikes, T, ivs, r)
    discount = np.exp(-r * T)

    is_call = option_types == 1

    # Call price: S*N(d1) - K*exp(-rT)*N(d2)
    call_price = spots * _norm_cdf(d1) - strikes * discount * _norm_cdf(d2)
    # Put price: K*exp(-rT)*N(-d2) - S*N(-d1)
    put_price = strikes * discount * _norm_cdf(-d2) - spots * _norm_cdf(-d1)

    return np.where(is_call, call_price, put_price)


def compute_iv(
    premiums: np.ndarray,
    spots: np.ndarray,
    strikes: np.ndarray,
    T: float,
    option_types: np.ndarray,
    r: float = 0.065,
    tol: float = 1e-6,
    max_iter: int = 50,
) -> np.ndarray:
    """Compute implied volatility via Newton-Raphson (vectorized).

    Near-zero premiums (< 0.05) are returned as IV = 0.

    Parameters
    ----------
    premiums : np.ndarray
        Observed market prices.
    spots, strikes, T, option_types, r
        Same as in ``black_scholes_price``.
    tol : float
        Convergence tolerance on IV change per iteration.
    max_iter : int
        Maximum Newton-Raphson iterations.

    Returns
    -------
    np.ndarray
        Implied volatilities (0.0 where premium is near-zero).
    """
    premiums = np.asarray(premiums, dtype=float)
    spots = np.asarray(spots, dtype=float)
    strikes = np.asarray(strikes, dtype=float)
    option_types = np.asarray(option_types, dtype=int)

    n = premiums.shape[0]
    iv = np.full(n, 0.20)  # initial guess

    # Mask: only solve where premium is meaningful
    valid = premiums >= 0.05

    for _ in range(max_iter):
        if not np.any(valid):
            break

        price = black_scholes_price(spots, strikes, T, iv, r, option_types)
        d1, _ = _d1_d2(spots, strikes, T, iv, r)
        vega_raw = spots * _norm_pdf(d1) * _sqrt(T)  # raw vega (not /100)

        diff = price - premiums
        # Avoid division by near-zero vega
        safe_vega = np.where(np.abs(vega_raw) > 1e-10, vega_raw, 1e-10)
        delta_iv = diff / safe_vega

        # Only update valid, unconverged contracts
        update_mask = valid & (np.abs(delta_iv) > tol)
        iv = np.where(update_mask, iv - delta_iv, iv)

        # Clamp IV to sensible range
        iv = np.clip(iv, 1e-6, 5.0)

        if not np.any(update_mask):
            break

    # Zero out near-zero premium contracts
    iv = np.where(valid, iv, 0.0)
    return iv


def compute_greeks(
    spots: np.ndarray,
    strikes: np.ndarray,
    T: float,
    ivs: np.ndarray,
    option_types: np.ndarray,
    r: float = 0.065,
) -> dict[str, np.ndarray]:
    """Compute Black-Scholes Greeks (vectorized).

    Parameters
    ----------
    spots, strikes, T, ivs, option_types, r
        Same conventions as ``black_scholes_price``.

    Returns
    -------
    dict with keys: delta, gamma, vega, theta
        - delta : N(d1) for calls, N(d1)-1 for puts
        - gamma : n(d1) / (S * σ * √T)  [same for calls and puts]
        - vega  : S * n(d1) * √T / 100  [per 1% change in IV]
        - theta : time decay per calendar day (negative for long positions)
    """
    spots = np.asarray(spots, dtype=float)
    strikes = np.asarray(strikes, dtype=float)
    ivs = np.asarray(ivs, dtype=float)
    option_types = np.asarray(option_types, dtype=int)

    sqrt_T = _sqrt(T)
    d1, d2 = _d1_d2(spots, strikes, T, ivs, r)
    nd1 = _norm_pdf(d1)
    discount = np.exp(-r * T)

    is_call = option_types == 1

    # Delta
    call_delta = _norm_cdf(d1)
    put_delta = call_delta - 1.0  # = N(d1) - 1 = -N(-d1)
    delta = np.where(is_call, call_delta, put_delta)

    # Gamma (same for calls and puts)
    gamma = nd1 / (spots * ivs * sqrt_T)

    # Vega per 1% move in IV (divide raw vega by 100)
    vega = spots * nd1 * sqrt_T / 100.0

    # Theta (per calendar day)
    # Shared term: -S*n(d1)*σ / (2*√T)
    theta_common = -(spots * nd1 * ivs) / (2.0 * sqrt_T)
    # Call: theta_common - r*K*exp(-rT)*N(d2)
    call_theta = (theta_common - r * strikes * discount * _norm_cdf(d2)) / 365.0
    # Put:  theta_common + r*K*exp(-rT)*N(-d2)
    put_theta = (theta_common + r * strikes * discount * _norm_cdf(-d2)) / 365.0
    theta = np.where(is_call, call_theta, put_theta)

    return {
        "delta": delta,
        "gamma": gamma,
        "vega": vega,
        "theta": theta,
    }

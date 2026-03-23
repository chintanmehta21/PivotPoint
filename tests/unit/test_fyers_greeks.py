"""Tests for vectorized Black-Scholes Greeks engine."""
import numpy as np
import pytest

from quant.data.fyers.greeks import (
    black_scholes_price,
    compute_greeks,
    compute_iv,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _scalar_price(spot, strike, T, iv, r=0.065, option_type=1):
    """Convenience wrapper that accepts scalars."""
    result = black_scholes_price(
        np.array([float(spot)]),
        np.array([float(strike)]),
        float(T),
        np.array([float(iv)]),
        float(r),
        np.array([int(option_type)]),
    )
    return float(result[0])


# ---------------------------------------------------------------------------
# TestBlackScholesPrice
# ---------------------------------------------------------------------------

class TestBlackScholesPrice:
    def test_atm_call_price_reasonable(self):
        price = _scalar_price(24000, 24000, 30 / 365, 0.20)
        assert 300 < price < 1000, f"ATM call price {price:.2f} out of expected range [300, 1000]"

    def test_deep_itm_call_near_intrinsic(self):
        price = _scalar_price(24000, 22000, 30 / 365, 0.20)
        assert price > 2000, f"Deep ITM call price {price:.2f} should be > 2000"

    def test_deep_otm_put_near_zero(self):
        price = _scalar_price(24000, 22000, 5 / 365, 0.15, option_type=-1)
        assert price < 10, f"Deep OTM put price {price:.4f} should be < 10"

    def test_vectorized_multiple_contracts(self):
        spots = np.full(5, 24000.0)
        strikes = np.array([22000.0, 22500.0, 23000.0, 23500.0, 24000.0])
        T = 30 / 365
        ivs = np.full(5, 0.20)
        r = 0.065
        option_types = np.ones(5, dtype=int)

        prices = black_scholes_price(spots, strikes, T, ivs, r, option_types)
        assert prices.shape == (5,)
        # Lower strike → higher call price (strictly decreasing as strike rises)
        for i in range(len(prices) - 1):
            assert prices[i] > prices[i + 1], (
                f"Call price at lower strike ({strikes[i]}) should be higher than at "
                f"higher strike ({strikes[i+1]}): {prices[i]:.2f} vs {prices[i+1]:.2f}"
            )

    def test_put_call_parity(self):
        spot, strike, T, iv, r = 24000.0, 24000.0, 30 / 365, 0.20, 0.065
        call = _scalar_price(spot, strike, T, iv, r, option_type=1)
        put = _scalar_price(spot, strike, T, iv, r, option_type=-1)
        lhs = call - put
        rhs = spot - strike * np.exp(-r * T)
        assert abs(lhs - rhs) < 1.0, (
            f"Put-call parity violated: C-P={lhs:.4f}, S-K*exp(-rT)={rhs:.4f}, diff={abs(lhs-rhs):.4f}"
        )


# ---------------------------------------------------------------------------
# TestComputeIV
# ---------------------------------------------------------------------------

class TestComputeIV:
    def test_recovers_known_iv(self):
        known_iv = 0.20
        spot, strike, T, r = 24000.0, 24000.0, 30 / 365, 0.065
        price = _scalar_price(spot, strike, T, known_iv, r, option_type=1)

        recovered = compute_iv(
            np.array([price]),
            np.array([spot]),
            np.array([strike]),
            T,
            np.array([1]),
            r=r,
        )
        assert abs(float(recovered[0]) - known_iv) < 1e-4, (
            f"IV recovery failed: expected {known_iv}, got {float(recovered[0]):.6f}"
        )

    def test_deep_otm_near_zero_premium_returns_zero_iv(self):
        iv = compute_iv(
            np.array([0.01]),
            np.array([24000.0]),
            np.array([30000.0]),
            30 / 365,
            np.array([1]),
            r=0.065,
        )
        assert float(iv[0]) == 0.0, f"Near-zero premium should return IV=0, got {float(iv[0])}"

    def test_vectorized_iv_recovery(self):
        np.random.seed(42)
        n = 20
        spots = np.full(n, 24000.0)
        strikes = np.linspace(22000, 26000, n)
        T = 30 / 365
        r = 0.065
        true_ivs = np.random.uniform(0.10, 0.40, n)
        option_types = np.where(strikes <= 24000, 1, -1).astype(int)

        prices = black_scholes_price(spots, strikes, T, true_ivs, r, option_types)
        recovered = compute_iv(prices, spots, strikes, T, option_types, r=r)

        # Only check contracts with non-trivial premiums
        mask = prices > 1.0
        diff = np.abs(recovered[mask] - true_ivs[mask])
        assert np.all(diff < 1e-4), (
            f"IV recovery errors too large: max={diff.max():.2e}, mean={diff.mean():.2e}"
        )


# ---------------------------------------------------------------------------
# TestComputeGreeks
# ---------------------------------------------------------------------------

class TestComputeGreeks:

    def _atm_greeks(self, option_type=1):
        spots = np.array([24000.0])
        strikes = np.array([24000.0])
        T = 30 / 365
        ivs = np.array([0.20])
        return compute_greeks(spots, strikes, T, ivs, np.array([option_type]))

    def test_atm_call_delta_near_0_5(self):
        g = self._atm_greeks(option_type=1)
        delta = float(g["delta"][0])
        assert 0.45 < delta < 0.65, f"ATM call delta {delta:.4f} not in (0.45, 0.65)"

    def test_atm_put_delta_near_neg_0_5(self):
        g = self._atm_greeks(option_type=-1)
        delta = float(g["delta"][0])
        assert -0.65 < delta < -0.45, f"ATM put delta {delta:.4f} not in (-0.65, -0.45)"

    def test_gamma_positive(self):
        g = self._atm_greeks()
        assert float(g["gamma"][0]) > 0, "Gamma must be positive"

    def test_vega_positive(self):
        g = self._atm_greeks()
        assert float(g["vega"][0]) > 0, "Vega must be positive"

    def test_theta_negative_for_long(self):
        g = self._atm_greeks()
        assert float(g["theta"][0]) < 0, "Theta (long position) must be negative"

    def test_returns_all_four_greeks(self):
        g = self._atm_greeks()
        assert set(g.keys()) == {"delta", "gamma", "vega", "theta"}, (
            f"Expected keys delta/gamma/vega/theta, got {set(g.keys())}"
        )

    def test_vectorized_20_contracts(self):
        np.random.seed(7)
        n = 20
        spots = np.full(n, 24000.0)
        strikes = np.linspace(22000, 26000, n)
        T = 30 / 365
        ivs = np.random.uniform(0.10, 0.40, n)
        option_types = np.where(strikes <= 24000, 1, -1).astype(int)

        g = compute_greeks(spots, strikes, T, ivs, option_types)
        for key in ("delta", "gamma", "vega", "theta"):
            assert key in g
            assert g[key].shape == (n,), f"{key} shape mismatch: {g[key].shape}"
        # All gammas positive
        assert np.all(g["gamma"] > 0), "All gammas should be positive"
        # All vegas positive
        assert np.all(g["vega"] > 0), "All vegas should be positive"

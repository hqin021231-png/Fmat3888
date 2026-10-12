import unittest

import numpy as np
import pandas as pd

from notebooks.q3_saa import solve_saa_profiles


class Q3SAATests(unittest.TestCase):
    def test_exact_growth_target_and_full_investment(self):
        returns = pd.DataFrame({
            "growth_asset": [-0.04, 0.02, 0.03, 0.01, 0.04, -0.01],
            "defensive_asset": [0.01, 0.00, 0.01, 0.02, 0.00, 0.01],
        })
        mapping = pd.DataFrame({
            "asset": ["growth_asset", "defensive_asset"],
            "growth_share": [1.0, 0.0],
        })

        metrics, weights = solve_saa_profiles(
            returns, mapping, periods_per_year=12, risk_free_rate=0.03,
            growth_targets=[0.30, 0.70],
        )

        np.testing.assert_allclose(metrics["target_growth"], [0.30, 0.70])
        np.testing.assert_allclose(metrics["actual_growth"], [0.30, 0.70], atol=1e-7)
        grouped = weights.groupby("target_growth")["weight"].sum()
        np.testing.assert_allclose(grouped.to_numpy(), [1.0, 1.0], atol=1e-7)
        self.assertTrue((weights["weight"] >= -1e-8).all())

    def test_infeasible_growth_target_is_reported_clearly(self):
        returns = pd.DataFrame({"a": [0.01, 0.02, -0.01], "b": [0.00, 0.01, 0.02]})
        mapping = pd.DataFrame({"asset": ["a", "b"], "growth_share": [1.0, 0.0]})

        with self.assertRaisesRegex(ValueError, "infeasible"):
            solve_saa_profiles(
                returns, mapping, periods_per_year=12, risk_free_rate=0.03,
                max_weight=0.20, growth_targets=[0.30],
            )

    def test_asset_names_must_match(self):
        returns = pd.DataFrame({"a": [0.01, 0.02, -0.01]})
        mapping = pd.DataFrame({"asset": ["b"], "growth_share": [1.0]})

        with self.assertRaisesRegex(ValueError, "Asset names must match"):
            solve_saa_profiles(returns, mapping, periods_per_year=12, risk_free_rate=0.03)


if __name__ == "__main__":
    unittest.main()

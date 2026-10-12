"""Question 3: Strategic Asset Allocation (SAA) minimum-variance portfolios.

Input returns must be periodic simple returns in a wide CSV: one row per period,
one column per asset. ``asset_growth_mapping_template.csv`` documents the second
input. The script deliberately does not invent data or asset classifications.

Example (from the repository root):
    python notebooks/q3_saa.py \
      --returns data/processed/returns.csv \
      --classification data/asset_growth_mapping.csv \
      --frequency quarterly --risk-free-rate-pct 4.0 \
      --output-dir outputs/q3

If Question 2 imposed a maximum weight per asset, pass the same limit with
``--max-weight`` so that the comparison remains consistent.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.optimize import linprog, minimize


ANNUALIZATION = {
    "daily": 252,
    "weekly": 52,
    "fortnightly": 26,
    "monthly": 12,
    "quarterly": 4,
    "annual": 1,
}
GROWTH_TARGETS = (0.30, 0.70, 0.90)
DATE_COLUMNS = {"date", "datetime", "timestamp", "time", "period"}


def _validate_inputs(
    returns: pd.DataFrame,
    classification: pd.DataFrame,
    periods_per_year: int,
    max_weight: float | None,
) -> tuple[pd.DataFrame, pd.Series]:
    if not isinstance(returns, pd.DataFrame) or returns.empty:
        raise ValueError("Returns must be a non-empty DataFrame of periodic returns.")
    if returns.columns.has_duplicates:
        raise ValueError("The returns table contains duplicate asset columns.")
    if len(returns) < 2:
        raise ValueError("At least two return observations are required to estimate covariance.")
    if periods_per_year < 1:
        raise ValueError("periods_per_year must be a positive integer.")
    if max_weight is not None and not (0 < max_weight <= 1):
        raise ValueError("max_weight must be greater than 0 and at most 1.")

    numeric_returns = returns.apply(pd.to_numeric, errors="coerce")
    numeric_returns = numeric_returns.dropna(axis=1, how="all")
    if numeric_returns.empty:
        raise ValueError("No numeric asset-return columns were found.")
    missing_rows = int(numeric_returns.isna().any(axis=1).sum())
    numeric_returns = numeric_returns.dropna(axis=0, how="any")
    if len(numeric_returns) < 2:
        raise ValueError("Fewer than two complete observations remain after aligning asset returns.")
    if missing_rows:
        print(f"Note: dropped {missing_rows} rows with missing returns to align all assets.")
    if not np.isfinite(numeric_returns.to_numpy(dtype=float)).all():
        raise ValueError("Returns contain non-finite values.")

    required = {"asset", "growth_share"}
    if not required.issubset(classification.columns):
        raise ValueError("Classification CSV must contain columns named 'asset' and 'growth_share'.")
    mapping = classification.loc[:, ["asset", "growth_share"]].copy()
    mapping["asset"] = mapping["asset"].astype(str).str.strip()
    if mapping["asset"].eq("").any() or mapping["asset"].duplicated().any():
        raise ValueError("Each asset must have exactly one non-empty classification row.")
    mapping["growth_share"] = pd.to_numeric(mapping["growth_share"], errors="coerce")
    if mapping["growth_share"].isna().any() or not mapping["growth_share"].between(0, 1).all():
        raise ValueError("growth_share must be numeric and between 0 and 1, inclusive.")

    return_assets = set(map(str, numeric_returns.columns))
    mapped_assets = set(mapping["asset"])
    if return_assets != mapped_assets:
        missing = sorted(return_assets - mapped_assets)
        unused = sorted(mapped_assets - return_assets)
        raise ValueError(
            "Asset names must match in both files. "
            f"Missing classifications: {missing}; mappings without returns: {unused}."
        )
    growth_share = mapping.set_index("asset")["growth_share"].reindex(numeric_returns.columns)
    growth_share.index = numeric_returns.columns
    return numeric_returns.astype(float), growth_share.astype(float)


def _feasible_start(growth_share: np.ndarray, target: float, max_weight: float) -> np.ndarray:
    n = len(growth_share)
    result = linprog(
        c=np.zeros(n),
        A_eq=np.vstack([np.ones(n), growth_share]),
        b_eq=np.array([1.0, target]),
        bounds=[(0.0, max_weight)] * n,
        method="highs",
    )
    if not result.success:
        raise ValueError(
            f"A {target:.0%} Growth target is infeasible under the supplied asset classifications "
            f"and weight limits ({result.message}). Check the mapping or agreed constraints."
        )
    return np.asarray(result.x, dtype=float)


def solve_saa_profiles(
    returns: pd.DataFrame,
    classification: pd.DataFrame,
    *,
    periods_per_year: int,
    risk_free_rate: float,
    max_weight: float | None = None,
    growth_targets: Iterable[float] = GROWTH_TARGETS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Solve long-only minimum-variance portfolios for specified Growth shares.

    Returns are annualized arithmetically (mean * periods_per_year and sample
    covariance * periods_per_year). ``risk_free_rate`` is an annual decimal.
    The constraints are sum(weights)=1, weights>=0, optional common per-asset
    cap, and exact weighted Growth exposure equal to each target.
    """
    aligned_returns, growth_share = _validate_inputs(
        returns, classification, periods_per_year, max_weight
    )
    assets = list(aligned_returns.columns)
    g = growth_share.to_numpy(dtype=float)
    cap = 1.0 if max_weight is None else float(max_weight)
    mu = aligned_returns.mean().to_numpy(dtype=float) * periods_per_year
    sigma = aligned_returns.cov().to_numpy(dtype=float) * periods_per_year
    sigma = (sigma + sigma.T) / 2.0  # remove tiny floating-point asymmetry

    summaries: list[dict[str, float]] = []
    allocations: list[dict[str, object]] = []
    for target in growth_targets:
        target = float(target)
        if not 0 <= target <= 1:
            raise ValueError(f"Growth target must be between 0 and 1; received {target}.")
        x0 = _feasible_start(g, target, cap)
        result = minimize(
            fun=lambda w: float(w @ sigma @ w),
            x0=x0,
            jac=lambda w: 2.0 * sigma @ w,
            method="SLSQP",
            bounds=[(0.0, cap)] * len(assets),
            constraints=[
                {"type": "eq", "fun": lambda w: np.sum(w) - 1.0,
                 "jac": lambda w: np.ones_like(w)},
                {"type": "eq", "fun": lambda w, t=target: g @ w - t,
                 "jac": lambda w: g},
            ],
            options={"ftol": 1e-12, "maxiter": 1000},
        )
        w = np.asarray(result.x, dtype=float)
        if not result.success:
            raise RuntimeError(f"Optimizer failed for {target:.0%} Growth: {result.message}")
        if (w < -1e-7).any() or (w > cap + 1e-7).any():
            raise RuntimeError(f"Optimizer returned a weight outside the allowed bounds for {target:.0%} Growth.")
        if abs(w.sum() - 1.0) > 1e-7 or abs(g @ w - target) > 1e-7:
            raise RuntimeError(f"Optimizer did not satisfy the constraints for {target:.0%} Growth.")

        annual_return = float(mu @ w)
        annual_variance = max(0.0, float(w @ sigma @ w))
        annual_volatility = float(np.sqrt(annual_variance))
        sharpe = (
            (annual_return - risk_free_rate) / annual_volatility
            if annual_volatility > 1e-12 else np.nan
        )
        summaries.append({
            "target_growth": target,
            "actual_growth": float(g @ w),
            "defensive_share": float(1.0 - g @ w),
            "expected_return_annual": annual_return,
            "volatility_annual": annual_volatility,
            "risk_free_rate_annual": float(risk_free_rate),
            "sharpe_ratio": float(sharpe),
            "variance_annual": annual_variance,
        })
        for asset, weight, growth in zip(assets, w, g):
            allocations.append({
                "target_growth": target,
                "asset": str(asset),
                "weight": float(weight),
                "asset_growth_share": float(growth),
                "growth_contribution": float(weight * growth),
            })

    return pd.DataFrame(summaries), pd.DataFrame(allocations)


def read_returns(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    removable = [
        c for c in frame.columns
        if str(c).strip().lower() in DATE_COLUMNS or str(c).strip().lower().startswith("unnamed:")
    ]
    return frame.drop(columns=removable)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute Q3 SAA minimum-variance portfolios.")
    parser.add_argument("--returns", required=True, type=Path,
                        help="CSV of periodic simple returns; one column per asset.")
    parser.add_argument("--classification", required=True, type=Path,
                        help="CSV with asset,growth_share (growth_share between 0 and 1).")
    parser.add_argument("--frequency", choices=ANNUALIZATION, required=True,
                        help="Return frequency; must match the data used in Questions 1–2.")
    parser.add_argument("--risk-free-rate-pct", required=True, type=float,
                        help="Annual risk-free rate as a percentage, e.g. 4.0 for 4%%.")
    parser.add_argument("--max-weight", type=float, default=None,
                        help="Optional maximum weight per asset; use the same limit as Q2 if applicable.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/q3"),
                        help="Folder for the summary and asset-weight CSV files.")
    args = parser.parse_args()

    if args.risk_free_rate_pct <= -100:
        parser.error("--risk-free-rate-pct must be greater than -100.")
    summary, weights = solve_saa_profiles(
        read_returns(args.returns),
        pd.read_csv(args.classification),
        periods_per_year=ANNUALIZATION[args.frequency],
        risk_free_rate=args.risk_free_rate_pct / 100.0,
        max_weight=args.max_weight,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "q3_portfolio_metrics.csv"
    weights_path = args.output_dir / "q3_portfolio_weights.csv"
    summary.to_csv(summary_path, index=False)
    weights.to_csv(weights_path, index=False)
    print("Q3 SAA portfolios (annualized):")
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print(f"\nSaved: {summary_path}\nSaved: {weights_path}")


if __name__ == "__main__":
    main()

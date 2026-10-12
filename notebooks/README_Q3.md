# Question 3: Strategic Asset Allocation

This folder contains the Q3 calculation module and a blank asset-classification
template. The repository snapshot available locally did not yet contain the
Q1/Q2 return data or their code, so no portfolio results have been fabricated.

## What Q3 calculates

For each required Growth target (30%, 70%, and 90%), the code minimizes annualized
portfolio variance subject to:

1. asset weights sum to 100%;
2. weights are long-only (no short selling);
3. the weighted APRA Growth exposure equals the selected target; and
4. an optional per-asset maximum, if the group used one in Q2.

Growth exposure is a weighted sum of the APRA asset classifications: 100% Growth
assets use `1.00`, asset classes with a 75/25 Growth/Defensive split use `0.75`,
50/50 classes use `0.50`, and Defensive-only classes use `0.00`. Use the precise
categories and mapping specified in the assignment and agreed by the group.
The project mapping discussed so far is: equity/listed property/listed
infrastructure `1.00`; unlisted property/infrastructure `0.75`; commodities and
other assets `0.50`; fixed interest and cash `0.00`. Confirm each asset's exact
assignment category before filling the mapping.

Expected returns and the sample covariance matrix are annualized using the same
period frequency as Q1/Q2. The Sharpe ratio uses the group's agreed annual
risk-free rate.

## Before running

1. Pull the correct Q1/Q2 branch or repository and use the same asset names and
   return series as the group.
2. Export the periodic **simple returns** to a wide CSV: one row per date/period,
   one column per asset. Returns must be decimals (`0.02` means 2%), not prices
   and not percentage-point values (`2`). A date column is allowed and ignored.
3. Copy `asset_growth_mapping_template.csv` to a working mapping CSV and add one
   row for every return column. Set `growth_share` to the assignment's APRA
   fraction for that asset (between 0 and 1).
4. Confirm with the group the return frequency, annual risk-free rate, and any
   individual-asset cap used in Q2.

## Run

Install the packages in `requirements.txt`, then run from the repository root.
For quarterly returns and a 4% annual risk-free rate, for example:

```bash
python notebooks/q3_saa.py \
  --returns data/processed/returns.csv \
  --classification data/asset_growth_mapping.csv \
  --frequency quarterly \
  --risk-free-rate-pct 4.0 \
  --output-dir outputs/q3
```

If Q2 uses a 40% maximum weight per asset, append `--max-weight 0.40`; otherwise
leave it out. Outputs are `q3_portfolio_metrics.csv` and
`q3_portfolio_weights.csv` in the selected output folder.

## Checks before using results in the report

- `actual_growth` should equal `target_growth` and `defensive_share` should be
  its complement.
- Each profile's asset weights must sum to 1, with no weight above the agreed cap.
- Verify the return frequency, annualization, risk-free rate, and asset mapping
  with Q1/Q2 before presenting figures.
- Describe these as estimates based on the chosen historical sample, not as
  guaranteed future performance.

The required data and group assumptions are still needed before final numerical
results can be calculated.

# Question 3 — Strategic Asset Allocation

## Method

We classified each asset by its Growth fraction using the APRA categories stated
in the assignment. For a portfolio with weights \(w_i\) and Growth fractions
\(g_i\), total Growth exposure is \(\sum_i g_i w_i\), and Defensive exposure is
its complement. For each target Growth exposure (30%, 70%, and 90%), we found the
long-only portfolio with the lowest estimated variance, subject to weights
summing to one and the same individual-asset constraints used in Question 2.
We estimated expected returns and the covariance matrix from the same return
sample and frequency used in Questions 1–2. Annualization and the risk-free rate
are [insert the agreed group choices].

## Results

Insert the values from `q3_portfolio_metrics.csv` and the principal asset weights
from `q3_portfolio_weights.csv` after the shared Q1/Q2 data are connected.

| Target Growth / Defensive | Actual Growth / Defensive | Expected annual return | Annual volatility | Sharpe ratio |
|---|---|---:|---:|---:|
| 30% / 70% | [result] | [result] | [result] | [result] |
| 70% / 30% | [result] | [result] | [result] | [result] |
| 90% / 10% | [result] | [result] | [result] | [result] |

## Interpretation

Compare how the three allocations change estimated return and volatility. Explain
which asset classes receive the largest weights and how the covariance structure
creates diversification. Discuss the trade-off between the lower-risk 30/70
profile and the higher-growth 90/10 profile, and identify the type of investor or
investment horizon each might suit. Use the calculated results to support the
comparison; do not assume that the highest Growth target must have the highest
estimated return or Sharpe ratio.

## Limitations

State that estimates depend on the selected historical period, asset
classifications, return frequency, and optimization constraints. Note that past
returns do not guarantee future performance, and that a minimum-variance
portfolio is sensitive to estimated means/covariances.

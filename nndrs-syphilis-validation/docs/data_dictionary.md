# Data dictionary

The fifteen machine-readable files in `data/` are the datasets deposited with the
article. File names keep the numbering of the deposited dataset (S1-S16); this
numbering is independent of the section numbers of the supplementary appendix.
All files are UTF-8 with a byte-order mark and comma-separated.

| File | Rows | Year span | Content |
|---|---|---|---|
| `S10_series_consistency.csv` | 32 | 2012-2025 | Year-by-year comparison of the three series by stratum, 2012-2025 |
| `S11_five_discordances.csv` | 5 | - | The five model-to-notification discordances, with domain, contrast and attribution |
| `S12_annual_three_series.csv` | 28 | 1998-2025 | Annual modelled and notified series with ratios, 1998-2025 |
| `S13_stage_specific_series.csv` | 18 | 2011-2025 | Stage-specific notifications and latent share, 2011-2025 |
| `S14_congenital_reconciliation.csv` | 9 | - | Congenital syphilis: modelled burden against the two notified series |
| `S15_provincial_inequality.csv` | 21 | 2004-2024 | Between-province inequality: CV, Gini on rates and on case counts, max/min ratio, 2004-2024 |
| `S16_provincial_ranking_2024.csv` | 31 | - | Provincial ranking on total incidence (2024) and on early syphilis (2020), with rank shift |
| `S1_provincial_incidence_2004_2024.csv` | 31 | 2004-2024 | Notified syphilis incidence (per 100,000) by province, 2004-2024, wide format |
| `S2_age_specific_2004_2024_full.csv` | 2798 | 2004-2024 | Notified cases, deaths and rates by year, age group and disease stage, 2004-2024 |
| `S3_gbd_china_age_sex_1990_2023.csv` | 2142 | 1990-2023 | GBD 2023 modelled syphilis incidence for China by age and sex, 1990-2023 (rates with 95% UI, cases) |
| `S4_three_official_series_1998_2025.csv` | 28 | 1998-2025 | The three official notification series A (onset date), B1 (final-review date) and B2 (report date), with pairwise differences, 1998-2025 |
| `S5_reporting_quality_2013_2021.csv` | 9 | 2013-2021 | Measured under-reporting and diagnostic-accuracy series used for the attribution bound, 2013-2021 |
| `S6_sensitivity_analyses.csv` | 10 | - | Sensitivity analyses: specification, result and conclusion for each |
| `S6a_trend_estimators.csv` | 15 | - | Trend estimators (APC, AAPC, EAPC) and break points for each series and segment |
| `S9_duplication_artefact_evidence.csv` | 19 | 2020-2024 | Evidence for the exact 2-fold duplication artefact in the 2021-2024 provincial PHSDC reports |

## Conventions

- Counts are notifications or modelled estimates as labelled; no file mixes the two.
- Rates are per 100,000 population. Modelled rates carry the 95% uncertainty
  interval of the GBD 2023 estimate; notified rates do not.
- `series_A` is tabulated by date of onset, `series_B1` by date of final review
  and `series_B2` by date of report. Percentages named `B1_vs_A_pct`,
  `B2_vs_B1_pct` and `B2_vs_A_pct` are computed as (numerator / denominator - 1) x 100.
- Provincial data for 2021-2024 are corrected for the exact 2-fold duplication
  artefact documented in `S9_duplication_artefact_evidence.csv` (see also
  `processed/` for the uncorrected series).
- Where a quantity is undefined (for example a ratio with a zero denominator) the
  cell is left empty rather than set to zero.

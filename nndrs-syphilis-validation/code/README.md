# Code

Python 3.13. Run every script **from the repository root** (`python code/<script>.py`):
`fetch_all.py` and `parse_all.py` resolve `batch/` and `raw/` against the working
directory, while the remaining scripts resolve all paths against the repository root
(`BASE` = parent of this folder).

## Pipeline

| Step | Script | Input | Output |
|---|---|---|---|
| 1 | `fetch_all.py` | PHSDC BIRT report interface (`ReportZoneYear`, `ReportAgeYear`), 2004–2020 | `batch/zone/`, `batch/age/` (raw HTML) |
| 2 | `fetch_2021_2024.py` | Same interface; years after the catalogue's drop-down limit are reached by constructing the URL directly. Needs `curl` | `batch/zone_ext/`, `batch/age_ext/`, `batch/month_ext/` |
| 3 | `parse_all.py` | `batch/` | `raw/NNDRS_*.csv` — annual, stage-specific, provincial and age-specific notified series |
| 4 | `build_2021_2024.py` | `batch/*_ext/` | `processed/province_year_*_2004_2024.csv`, `processed/province_inequality_2004_2024.csv`, `processed/province_2024_rank.csv`, `processed/national_age_incidence_2021_2024.csv` |
| 5 | `build_tables.py` | `raw/`, `processed/` | `tables/Table1.csv`–`Table7.csv` |
| 6 | `build_supplementary.py` | `raw/`, `processed/`, `tables/`, GBD extract | `data/S1`–`S16` (the fifteen released datasets) and the supplementary appendix |
| 7 | `figures_P2.py` | `processed/`, `tables/` | `figures/Fig1`–`Fig3` (PDF + 300 dpi PNG) |
| 8 | `figures_P3.py` | `processed/`, `tables/`, GBD extract | `figures/Fig4`, `figures/Fig5` |

## Verification scripts (no output files)

| Script | What it prints |
|---|---|
| `verify.py` | Provincial totals summed against the national row; stage components against the total; region counts |
| `analyze.py` | Annual provincial inequality (CV, Gini, max/min), 2020 provincial ranking with stage composition, age-specific early-syphilis rates 2019 against 2020 |
| `analyze2.py` | The five largest provincial falls and rises 2019–2020; the national 2004–2020 series by stage |

## Shared modules

| Module | Provides |
|---|---|
| `p2_data.py` | `joinpoint()` grid search with BIC selection (0–2 knots) and `seg_fit()` segment fitting, used by `build_supplementary.py` |
| `pgrid.py` | `to_grid()`, the provincial panel reshape used by `build_2021_2024.py` |
| `supp_content.py` | GATHER and RECORD checklist rows written into the supplementary appendix |

## Notes on the GBD input

`figures_P3.py` reads the GBD 2023 Results Tool extraction from
`raw/B_age_sex_1990_2023.csv`, or from the path in the environment variable
`GBD_AGE_SEX_CSV`. That extraction is IHME data and is not redistributed here; download it
with the query specification in `../docs/gbd_query.md`. When the file is absent the script
falls back to the released `data/S3_gbd_china_age_sex_1990_2023.csv`, which carries the same
GBD 2023 values for China and is sufficient for figure 4C.

## Two data-handling decisions encoded in the scripts

- **Provincial duplication, 2021–2024.** The PHSDC provincial reports for those years
  return each total exactly twice; `build_2021_2024.py` divides by two and the evidence is
  written to `data/S9_duplication_artefact_evidence.csv`.
- **Series B2, 2023.** The report-date total for 2023 is reconstructed from the
  stage-specific series rather than read from a published total; the derivation and its
  sensitivity appear in `data/S6_sensitivity_analyses.csv`.

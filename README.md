# Burden of Syphilis in China, 1990–2023 — GBD 2023 Analysis

Reproducible analysis pipeline for:

> Wang Z, Jing HX, Wang H, Luo F. The syphilis epidemic in China has entered a
> high-burden plateau with sharply reduced mortality: a Global Burden of Disease
> 2023 study (manuscript in preparation, Frontiers in Public Health).

Correspondence: Fang Luo, Department of..., Taihe Hospital, Hubei University of
Medicine, Shiyan 442000, China (sylf1998@163.com).
First author: Zhen Wang (sywz1998@163.com).

## Data sources

All input data are publicly available aggregate estimates:

- **GBD 2023 Results Tool** (IHME), https://vizhub.healthdata.org/gbd-results/
  - Cause: **syphilis (GBD cause ID 394)** — in the GBD 2023 hierarchy this
    cause encompasses congenital syphilis (deaths and disability in children
    younger than 5 years) together with acute infections and neurological and
    cardiovascular sequelae in adults.
  - Measures: incidence, prevalence, deaths, DALYs; metrics: number and rate;
    both sexes; all age groups and the age-standardized aggregate.
  - Locations: China, Global, 5 SDI quintiles, 21 GBD regions, 204 countries
    and territories; years 1990–2023.
  - Downloaded: **8 October 2026**.
  - Exact query settings: see [`docs/query_parameters.md`](docs/query_parameters.md).
- **IHME GBD 2023 Socio-Demographic Index (SDI) 1950–2023** release,
  https://ghdx.healthdata.org/record/gbd-2023-socio-demographic-index-sdi
  - High-SDI quintile threshold in 2023: SDI ≥ 0.7188 (GBD 2023 reference
    quintile cut-points).

## Repository structure

```
syphilis-gbd2023-china/
├── data/raw/                 # GBD 2023 extraction CSVs (as downloaded)
│   ├── A_ASR_1990_2023.csv               # age-standardized rates, annual series
│   ├── B_age_sex_1990_2023.csv           # age × sex counts and rates
│   ├── C_sdi_regions_1990_2023.csv       # Global + SDI quintiles + 17 regions
│   ├── C2_missing3regions_1990_2023.csv  # Central Asia / Central Europe / Eastern Europe
│   ├── C3_hina_1990_2023.csv             # High-income North America
│   ├── D_countries_2023.csv              # 204 countries, 2023 cross-section
│   ├── E_sdi_countries.csv               # SDI values, 1,000 locations, 1950–2023
│   └── country_centroids.csv             # centroids for the equal-area tile map
├── R/                        # analysis pipeline (R >= 4.6.1)
├── docs/query_parameters.md  # GBD Results Tool query specification
└── output/
    ├── figures/              # Figure 1–12 (PNG + PDF, 300 dpi)
    └── tables/               # Table 1–6 + joinpoint/decomposition outputs (CSV)
```

## Reproduction

1. Install R ≥ 4.6.1 (base packages only; `openxlsx` optional for Table 1 xlsx).
2. From the `R/` directory run:

```r
source("run_all.R")   # or: Rscript run_all.R --real
```

Individual outputs can be regenerated with the numbered scripts
(`02_eapc_trend.R`, `03_joinpoint.R`, `05_decomposition.R`, `10–15`, …); each
script sources `00_config.R` and `01_load_clean.R` and writes to
`output/figures` and `output/tables`.

Key methods: log-linear EAPC with 95% CIs from `confint` (t-based); joinpoint
grid search with BIC selection (0–2 knots); Shapley-value decomposition of
case-count changes into population growth, population aging, and
epidemiological change (Das Gupta standardization equivalent); sensitivity
analysis for the terminal joinpoint segment (script `15_joinpoint_sensitivity.R`).

## License

- Code: MIT License.
- GBD data files in `data/raw/` are IHME estimates used under the GBD open-data
  terms; users should cite IHME GBD 2023 when reusing them.

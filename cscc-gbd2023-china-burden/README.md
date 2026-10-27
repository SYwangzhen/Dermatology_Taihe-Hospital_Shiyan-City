# Cutaneous squamous cell carcinoma in China, 1990–2023

**Data and code record for a Global Burden of Disease 2023 analysis**

This repository is the data and code record for the manuscript:

> Wang Z, Wang C, Jing H, Wang H, Li S. *Cutaneous squamous cell carcinoma in
> China, 1990–2023: a Global Burden of Disease 2023 analysis.* Submitted to the
> Journal of the European Academy of Dermatology and Venereology (JEADV), 2026.

Department of Dermatology, Taihe Hospital, Hubei University of Medicine,
Shiyan 442000, Hubei, China. Correspondence: Zhen Wang (sywz1998@163.com).

---

## What the study does

The study analyses the GBD 2023 estimates of cutaneous squamous cell carcinoma
(cSCC) in China for 1990–2023: burden levels and trends (age-standardized
incidence, prevalence, mortality and DALY rates, with Newey–West
autocorrelation-robust trend testing), the drivers of case growth (Das Gupta
decomposition into population growth, population ageing and epidemiological
change), age–sex patterns, a mortality-to-incidence comparison against the
global level, and a cross-cycle (GBD 2021 vs GBD 2023) sensitivity comparison
of the atypical 2011–2016 fluctuation.

## Repository layout

```
cscc-gbd2023-china-burden/
├── code/                    Full R 4.6.1 pipeline + Python 3.13 stage
│   ├── 00_config.R ... 08_extract_supp.R, run_all.R
│   ├── reanalysis_v23.py    Das Gupta decomposition, GBD 2021-vs-2023
│   │                        cross-cycle comparison, YLL/YLD split
│   ├── hac_eapc.py          Newey–West HAC trend testing (lag-3 rule, lag 2/5 sensitivity)
│   ├── evidence_tables.py   eTable 5 / ≥65 / M-I assertions (26 checks)
│   └── make_figures_final.py  Figures 2–4 from pipeline outputs + assertions
├── data/
│   ├── raw/                 5 original IHME archive ZIPs as downloaded +
│   │                        3 directly extracted CSV exports (A/B retain Chinese-interface labels; values identical)
│   └── (CSV/JSON)           machine-readable result tables (Table 1, eTables 1–5 sources)
├── figures/                 final Figures 1–4 (vector PDF)
├── DOWNLOAD_PARAMETERS.txt  exact GBD Results Tool download parameters
└── RUN_ORDER.txt            pipeline execution order
```

## One-click reproduction

```
cd code && Rscript run_all.R --real
```

Set the `PYTHON` environment variable if the Python 3.13 interpreter is not on
PATH; all raw GBD exports are included under `data/raw/`, so no re-download is
needed. The single entry point runs the R pipeline (data cleaning and
normalization, EAPC, segmented regression with interval-length-weighted AAPC,
the three-factor decomposition with closure assertions, Table 1, Figure 1 and
the eTable 2/3 exports), then invokes the four Python stages, each with
hard-coded assertions against the manuscript numbers. Requires R ≥ 4.2 and
Python ≥ 3.10 (NumPy/SciPy/Pandas/Matplotlib); see `RUN_ORDER.txt` for the
stage-by-stage order.

## Data source and attribution

All inputs were downloaded from the GBD Results Tool
(https://vizhub.healthdata.org/gbd-results/) on 3 September 2026; the complete
parameter sets are in `DOWNLOAD_PARAMETERS.txt`. The GBD data archived here
were obtained from the Institute for Health Metrics and Evaluation (IHME) and
are redistributed solely for reproducibility of this analysis; use of GBD data
must comply with the IHME data-use policies
(https://www.healthdata.org/about/terms), with attribution to IHME. GBD
estimates are model outputs and are revised across cycles; interpret
accordingly.

Within the GBD 2023 cause hierarchy, non-melanoma skin cancer is a level-3
cause and squamous-cell and basal-cell carcinoma are separate level-4 causes
under it; squamous-cell carcinoma is estimated for incidence and mortality,
whereas basal-cell carcinoma is estimated for incidence and other nonfatal
outcomes but not mortality.

# Systematic divergence between modeled and notified syphilis burden, China, 2004–2025

**Parallel-series triangulation of a global model against a national notification system**

This repository is the data and code record for the manuscript:

> Wang Z, Wang C, Jing H, Tang Z. *Systematic divergence between modeled and notified
> syphilis burden, China, 2004–2025.* Manuscript, 2026.

Department of Dermatology, Taihe Hospital, the Affiliated Hospital of Hubei University of
Medicine, Shiyan 442000, Hubei, China. Correspondence: Zhen Wang (sywz1998@163.com).

---

## What the study does

Global burden estimates and national notification counts are quoted side by side but
almost never reconciled. This study sets out a procedure — **parallel-series
triangulation** — that tests a model estimate against notification data on three
criteria, reported separately and deliberately **not** combined into a single score:

| Criterion | Question | Statistic |
|---|---|---|
| Level | How large is the gap, and can reporting loss explain it? | ratio `R = M/N`, its log-normal 95% range, and the share of infections that would have to go undiagnosed |
| Trend | Do the two series move together? | joinpoint APC `100(exp β − 1)`, EAPC, and correlation of `ln R` with time |
| Structure | Do the published dimensions agree? | stage-specific, age-specific and between-province contrasts; Gini and CV |

Three official Chinese series tabulate the same notifications on different statistical
bases — **A** by date of onset, **B1** by date of final review, **B2** by date of report —
so the precision of the notified figures is bounded from within rather than assumed.

Main findings: a 3.7-fold gap between modelled and notified burden cannot be attributed to
reporting loss (closing it would require about 73% of infections to go undiagnosed, against
measured under-reporting of diagnosed cases below 2.1%); the rising notified total reflects
expanded detection of latent infection (54.6% to 91.9% of notifications) while notified
early syphilis fell by 75.8%; between-province inequality fell for fifteen years and then
reversed after 2019; and the model assigns zero incidence at 65 years and above, the age
band in which notification rates are highest.

---

## Data sources

All inputs are published aggregate statistics. No individual-level records, no pathogen
sequences and no human genomic data were used; no ethical approval was required.

| Source | Content | Access |
|---|---|---|
| **GBD 2023 Results Tool** (IHME)<br>https://vizhub.healthdata.org/gbd-results/ | Modelled syphilis incidence, prevalence, deaths and DALYs, cause ID 394, China by age and sex, 1990–2023 | Free registration; query specification in [`docs/gbd_query.md`](docs/gbd_query.md) |
| **National Disease Control and Prevention Administration (NDCPA)** annual summaries of notifiable infectious diseases<br>https://www.ndcpa.gov.cn/ | National annual notified cases and rates, 2004–2025 (series A basis) | Public web pages |
| ***Disease Surveillance*** monthly tables (China CDC)<br>https://www.jbjc.org/ | Annual totals by date of final review and stage-specific notifications, 1998–2025 (series B1) | Open access, DOIs |
| **National Center for STD Control** annual reports, *Chinese Journal of AIDS & STD* | Totals by date of report, stage composition (series B2) | Open access, DOI 10.13419/j.cnki.aids |
| **China Public Health Science Data Center (PHSDC)**<br>https://www.phsciencedata.cn/ | Provincial and age-specific notification panel, 2004–2024 | Free after registration; terms permit non-commercial research use with attribution |
| **China Health Statistics Yearbook** and **Statistical Bulletin on Health Development** | Provincial notification rates, cross-checks | Public / library |

[`docs/source_index.csv`](docs/source_index.csv) is the retrieval record: one row per
source page, with the item retrieved and the exact URL, kept as archived with the record.

---

## Repository structure

```
nndrs-syphilis-validation/
├── data/          # 15 released datasets (S1–S16), as deposited with the article
├── raw/           # parsed official series (inputs to the table build)
├── processed/     # intermediate series (model-to-notification ratios, ranks, Gini)
├── tables/        # Table 1–7 underlying the manuscript
├── figures/       # Figures 1–5 (vector PDF + 300 dpi PNG)
├── code/          # retrieval, parsing, analysis and figure scripts (see code/README.md)
└── docs/          # data dictionary, GBD query specification, source index
```

`data/` is the archive of record; `raw/`, `processed/` and `tables/` are shipped so that
every table and figure can be regenerated without re-downloading anything.

**Dataset index** — file name, row count, year span and content for each of the fifteen
files: [`docs/data_dictionary.md`](docs/data_dictionary.md).

---

## Figures

| File | Content |
|---|---|
| `figures/Fig1` | Modelled and notified burden, 1990–2025; the 3.8-fold gap; congenital syphilis; the three-series comparison |
| `figures/Fig2` | Level criterion: ratio series, the three pairwise offsets, stage-specific gaps, correlation of the ratio with time |
| `figures/Fig3` | Trend criterion: latent share; early syphilis notifications and joinpoint segments |
| `figures/Fig4` | Structure criterion (sex and age): sex-specific rates, male-to-female ratio, age-specific model against notifications, ratio by age |
| `figures/Fig5` | Structure criterion (province): Gini, coefficient of variation, max/min ratio, rate-rate scatter, rank shift |

Vector PDFs are the versions intended for print; PNG files are 300 dpi at 154–157 mm width.

---

## Reproduction

Python 3.13 with `pandas`, `numpy` and `matplotlib` (`openpyxl` only if exporting Table 1
to xlsx); `fetch_2021_2024.py` calls `curl`. Run the scripts **from the repository root** —
two retrieval scripts resolve `batch/` and `raw/` against the working directory, while the
analysis scripts resolve everything against the repository root itself.

```
python code/fetch_all.py            # PHSDC report interface, 2004-2020  -> batch/
python code/fetch_2021_2024.py      # PHSDC report interface, 2021-2024  -> batch/*_ext/
python code/parse_all.py            # HTML tables                        -> raw/*.csv
python code/build_2021_2024.py      # provincial and age panels 2021-24  -> processed/
python code/build_tables.py         #                                     -> tables/Table1-7.csv
python code/build_supplementary.py  #                                     -> data/S1-S16.csv
python code/figures_P2.py           #                                     -> figures/Fig1-3
python code/figures_P3.py           #                                     -> figures/Fig4-5
```

Steps 1–2 need network access to the PHSDC report interface and create `batch/`, which is
not shipped; the provincial and age reports are reachable without login, while the
catalogue pages require a free account. If those steps are skipped, the shipped `raw/`,
`processed/` and `tables/` files are sufficient to rerun steps 5, 7 and 8 unchanged — these
regenerate tables 1–7, figures 1–3 and figures 4–5, and the regenerated files are identical
to the archived ones. Step 6 additionally needs the two GBD 2023 extracts (below), because
the age-standardised series cannot be rebuilt from the released datasets alone.
`analyze.py`, `analyze2.py` and `verify.py` print the cross-checks quoted in the manuscript
(provincial totals against the national row, stage components against the total); they
write no files.

**Two inputs are not redistributed:** the GBD 2023 extractions `B_age_sex_1990_2023.csv`
and `A_ASR_1990_2023.csv` are IHME data and must be downloaded from the GBD Results Tool
using the specification in [`docs/gbd_query.md`](docs/gbd_query.md), then placed in `raw/`.
`figures_P3.py` falls back to the released `data/S3_gbd_china_age_sex_1990_2023.csv`
(identical GBD 2023 values, China only) when the first is absent, so figures 4 and 5
reproduce either way; `build_supplementary.py` stops with a message naming the missing file,
because the age-standardised series cannot be rebuilt from the released datasets alone.
Cite IHME GBD 2023 whenever these estimates are reused.

---

## Two data properties that users of these files should know

1. **Provincial duplication artefact.** The PHSDC provincial reports for 2021–2024 return
   each provincial total exactly twice. All provincial figures in this repository are
   divided by two; the evidence, including three independent provincial bulletins used as
   an external check, is in `data/S9_duplication_artefact_evidence.csv`.
2. **Series B2 for 2023 is derived.** The published report-date total for 2023 is
   reconstructed from the stage-specific series rather than read directly; the derivation
   and its sensitivity are in `data/S6_sensitivity_analyses.csv`.

---

## Licence and citation

- **Code** (`code/`): MIT Licence, see [`LICENSE`](LICENSE).
- **Data** (`data/`, `raw/`, `processed/`, `tables/`): CC BY 4.0. Attribution: Wang Z,
  Wang C, Jing H, Tang Z. *Systematic divergence between modeled and notified syphilis
  burden, China, 2004–2025* (repository), 2026.
- GBD 2023 estimates remain subject to the IHME terms of use and must be cited to IHME.

Please cite the article when it is published; until then, cite this repository by its URL.

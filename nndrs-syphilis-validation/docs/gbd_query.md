# GBD 2023 query specification

Two extractions are used. Both are downloaded from the **GBD Results Tool** (IHME),
https://vizhub.healthdata.org/gbd-results/, with a free account. They are IHME data and
are **not** redistributed with this repository.

| Setting | Value |
|---|---|
| Release | GBD 2023 |
| Cause | Syphilis (GBD cause ID 394) |
| Location | China |
| Years | 1990–2023 |
| Sex | Both, Male, Female |
| Metrics | Number, Rate |
| Ages | All ages, Age-standardized, and every five-year band from `<5 years` to `95+ years` |
| Downloaded | 8 October 2026 |

## Files produced

| File (place in `raw/`) | Contents used here |
|---|---|
| `A_ASR_1990_2023.csv` | Age-standardised rates: `measure_name` = Incidence / Prevalence / Deaths / DALYs, `age_name` = `Age-standardized`, `metric_name` = Rate. Used for the modelled ASIR series by sex (figures 1A, 4A) and for the model-to-notification ratio `R`. |
| `B_age_sex_1990_2023.csv` | Age × sex detail, both Number and Rate, all five-year bands. Used for the age-specific comparison with notifications (figure 4C) and for the modelled burden in children under five (figure 1C, dataset S3). |

Both files share the flat export schema of the Results Tool:
`population_group_id, population_group_name, measure_id, measure_name, location_id,
location_name, sex_id, sex_name, age_id, age_name, cause_id, cause_name, metric_id,
metric_name, year, val, upper, lower`.

## Socio-demographic index

The SDI values and quintile cut-points used in the sensitivity analyses come from the
**IHME GBD 2023 Socio-Demographic Index 1950–2023** release,
https://ghdx.healthdata.org/record/gbd-2023-socio-demographic-index-sdi. The high-SDI
threshold in 2023 is SDI ≥ 0.7188.

## If the extracts are absent

`code/figures_P3.py` falls back to `data/S3_gbd_china_age_sex_1990_2023.csv`, which carries
the same GBD 2023 values for China and is enough for figure 4. `code/build_supplementary.py`
and `code/p2_data.py` stop with a message naming the missing file: the age-standardised
series cannot be reconstructed from the released datasets alone.

Whenever these estimates are reused, cite IHME GBD 2023 as required by the IHME terms of use.

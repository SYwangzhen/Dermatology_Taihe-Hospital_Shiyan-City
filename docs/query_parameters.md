# GBD Results Tool Query Specification

All extractions were performed on **8 October 2026** via the GBD Results Tool
(https://vizhub.healthdata.org/gbd-results/), GBD 2023 release.

## Common settings (all queries)

| Setting | Value |
|---|---|
| Context | Cause of death or injury |
| Cause | Syphilis (cause ID **394**; includes congenital syphilis, acute infection, and neurological/cardiovascular sequelae) |
| Measures | Incidence; Prevalence; Deaths; DALYs |
| Metrics | Number; Rate |
| Age | All ages; Age-standardized |
| Sex | Male; Female; Both |
| Year | 1990–2023 (all) |

## Location-specific queries

| File | Locations | Notes |
|---|---|---|
| `A_ASR_1990_2023.csv` | China; Global; High SDI | age-standardized annual series, all measures |
| `B_age_sex_1990_2023.csv` | China | number + rate by 5-year age group × sex |
| `C_sdi_regions_1990_2023.csv` | Global; 5 SDI quintiles; High-income Asia Pacific; Oceania; Southeast Asia; South Asia; Central Europe; Eastern Europe; Western Europe; Australasia; Southern/Tropical/Central/Andean Latin America; Caribbean; North Africa and Middle East; Western/Eastern/Central/Southern Sub-Saharan Africa | note: Central Asia, Central Europe, Eastern Europe fall under the Central Europe, Eastern Europe, and Central Asia super-region and must be selected individually |
| `C2_missing3regions_1990_2023.csv` | Central Asia; Central Europe; Eastern Europe | supplement to the file above |
| `C3_hina_1990_2023.csv` | High-income North America | supplement to the file above |
| `D_countries_2023.csv` | All 204 countries and territories | 2023 only; incidence + DALYs |
| `E_sdi_countries.csv` | 1,000 GBD locations | SDI values 1950–2023, from the IHME GBD 2023 SDI release (https://ghdx.healthdata.org/record/gbd-2023-socio-demographic-index-sdi) |

## SDI quintile assignment (2023)

GBD 2023 reference quintile thresholds: low < 0.4607; low-middle 0.4607–0.5316;
middle 0.5316–0.6305; high-middle 0.6305–0.7188; **high ≥ 0.7188**.

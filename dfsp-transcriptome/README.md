# DFSP Transcriptomic Integration — Analysis Code

Reproducible analysis pipeline for:

> Wang Z, Jing HX, Wang H, Luo F. *Multi-cohort transcriptomic integration defines a diagnostic signature, an immune-cold microenvironment, and drug vulnerabilities of dermatofibrosarcoma protuberans* (manuscript).

Correspondence: Fang Luo, Department of..., Taihe Hospital, Hubei University of Medicine, Shiyan 442000, China (sylf1998@163.com). First author: Zhen Wang (sywz1998@163.com).

All input data are **publicly available**; no new experiments were performed.

## Data sources

| Dataset | Platform | Role | Source |
|---|---|---|---|
| GSE42948 | 3SEQ (GPL10999) | Discovery / FS axis | NCBI GEO |
| GSE2553 | cDNA array (GPL1977) | Cross-tumor validation | NCBI GEO |
| GSE150787 | qPCR (GPL28553) | Therapy layer (pazopanib II) | NCBI GEO |
| TCGA-SARC | RNA-seq (GDC STAR-TPM) | Background / specificity | UCSC Xena (GDC hub) |
| Ge et al. 2023 | scRNA-seq, 15 subclusters | Cell-program reference | PMC10992304 (supplement) |
| ChEMBL | — | Drug repurposing | ebi.ac.uk/chembl |

All datasets retrieved August 2026.

## Repository structure

```
code/
├── W1_data/          # data preparation
│   ├── prep_GSE42948.py, prep_GSE2553.py, prep_TCGA_SARC.py
│   ├── prep_Ge2023.py, extract_sample_annot.py, gpl_parser.py
│   └── w1_finalize.py            # gene-symbol harmonization & cohort assembly
├── W2_signature/     # diagnostic signature & machine learning
│   ├── w2_degs.py                # per-cohort differential expression (Wilcoxon, BH-FDR)
│   ├── w2_signature_final.py     # direction-consistent 151-gene consensus signature
│   ├── w2_rra_v3.py              # rank-aggregation statistics
│   ├── w2_ml_v3.py               # leakage-free LASSO + SVM-RFE, bidirectional validation
│   ├── w2_celltype_loc.py        # single-cell mapping of signature genes
│   └── w2_heatmap.py
├── W3_microenvironment_drugs/
│   ├── w3_ssgsea.py              # single-cell-informed ssGSEA projection
│   ├── w3_chembl_v2.py           # ChEMBL target/drug query
│   ├── w3_dgidb.py               # cross-check via DGIdb
│   └── w3_plots.py
└── W4_figures/       # FS-ness, EGFR-axis & background analyses, figures
    ├── w4_fsness.py              # fibrosarcomatous-program (FS-ness) score
    ├── w4_response_analysis.py   # EGFR-axis resistance program (GSE150787)
    ├── w4_plots.py               # TCGA-SARC signature projection (Figure 7)
    ├── w4_fig1_matplotlib.py, w4_fig67.py
    ├── add_panel_labels.py, relabel_panels.py, export_figs_tables.py
    └── validate_jtm_ready.py
```

> Files ending in `_v2`/`_v3` are iterative refinements; the final versions used for the
> manuscript are the highest-numbered ones (listed above). Intermediate exploration
> scripts are omitted for clarity.

## Reproduction

1. Python ≥ 3.13 with `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`.
2. Download the raw datasets from GEO / UCSC Xena (see `docs/` query parameters in the
   manuscript's Data availability) into `data/`.
3. Run the scripts in order `W1 → W2 → W3 → W4`. All bootstrap resampling and permutation
   analyses use fixed random seed **2026**.

## Code availability

Archived on GitHub (`Dermatology_Taihe-Hospital_Shiyan-City`, `dfsp-transcriptome/` branch or folder)
and assigned a Zenodo DOI upon manuscript acceptance.

## License

Code: MIT License.

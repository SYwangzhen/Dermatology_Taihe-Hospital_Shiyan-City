# -*- coding: utf-8 -*-
"""S7 GATHER / RECORD 清单内容与 S8 复现清单（纯数据，供 build_supplementary.py 引用）。"""

# ── S7.1 GATHER（Stevens GA 等, PLoS Med 2016;13(6):e1002056，18 条）──────
GATHER_HEAD = ['#', 'GATHER checklist item', 'Where reported in this manuscript']

GATHER_ROWS = [
    ['1', 'Define the indicator(s), populations (including age, sex, and geographic entities) and '
          'time period(s) for which estimates were made.',
     'Abstract; Methods: study design and data sources. Indicators: incident syphilis infections (model) and notified '
     'syphilis cases (surveillance) for China, 1990\u20132023 (model) and 1998\u20132025 '
     '(notification), by sex, 5-year age band, stage and 31 provincial-level regions. This study '
     'does not generate new global health estimates; it compares an existing published estimate '
     'with national surveillance, so GATHER items are completed with respect to that comparison.'],
    ['2', 'List the funding sources for the work.',
     'Declarations (Funding). To be completed at submission. No funding body had a role in the '
     'design, analysis or interpretation of the comparison.'],
    ['3', 'Describe how the data were identified and how the data were accessed.',
     'Methods: study design and data sources, paragraph by data stream. GBD 2023 estimates were extracted from the GBD '
     'Results Tool (vizhub.healthdata.org/gbd-results). Notification data were compiled from '
     'published official annual and monthly tables and from the Public Health Science Data Center '
     'report interface; the retrieval chain is described in Supplementary S8.'],
    ['4', 'Specify the inclusion and exclusion criteria. Identify all ad hoc exclusions.',
     'Methods: study design and data sources, and definitions and construct alignment. Series A values for 1998\u20132003 rest on an earlier case definition '
     'and reporting platform and were excluded from all ratio-based analyses and shown for context '
     'only. 2024\u20132025 were additionally excluded in one sensitivity analysis (Methods: sensitivity analyses, S6.2). '
     'No other ad hoc exclusions were applied.'],
    ['5', 'Provide information on all included data sources and their main characteristics.',
     'Methods: study design and data sources; Table 1 (construct and basis comparison); Supplementary Tables S1\u2013S5. '
     'For each stream the source, statistical basis, population covered, years collected, age and '
     'sex range and case definition are given.'],
    ['6', 'Identify and describe any categories of input data that have potentially important biases.',
     'Methods: definitions and construct alignment and Methods: spatial inequality; Results: the gap is not explained by under-reporting; Discussion: three mechanisms behind the discordance. Three bias categories are named and '
     'quantified: reporting completeness (under-reporting 2.04%\u20130.33%), diagnostic accuracy '
     '(93.9%\u201398.7%), and the stock-to-flow composition of latent notifications '
     '(54.6%\u219291.9% of the total). The provincial source additionally returned a uniform '
     'two-fold duplication for 2021\u20132024, which is documented and verified in Supplementary S9.'],
    ['7', 'Describe and give sources for any other data inputs.',
     'Methods: study design and data sources, final paragraph. Two inputs contribute to the analysis without being '
     'synthesised: the national under-reporting and diagnostic-accuracy series (2013\u20132021) and '
     'the published male-to-female notification ratios (Supplementary S5).'],
    ['8', 'Provide all data inputs in a file format from which data can be efficiently extracted.',
     'Supplementary data files S1\u2013S6a are supplied as CSV. Data that cannot be redistributed '
     'are identified with the institution that holds them: GBD 2023 estimates (Institute for '
     'Health Metrics and Evaluation, under its open access licence) and the provincial notification '
     'database (Public Health Science Data Center, Chinese CDC, non-commercial research use).'],
    ['9', 'Provide a conceptual overview of the data analysis method.',
     'Methods: study design and data sources (three-step design) and Methods: three-way decomposition of the notified burden; Figure 1; Supplementary Table S6a. The comparison '
     'proceeds from construct alignment to quantification of discordance in level, trend and '
     'structure, and then to attribution of the residual.'],
    ['10', 'Provide a detailed description of all steps of the analysis, including mathematical '
           'formulae.',
     'Methods: statistical analysis through sensitivity analyses. Formulae are given for the model-to-notification ratio, the '
     'log-scale Bland\u2013Altman summary (mean difference and limits of agreement), the piecewise '
     'log-linear (joinpoint) fit with hinge basis functions and BIC break-point selection, the '
     'three trend summary estimators (APC, AAPC and EAPC = 100 \u00d7 [exp(\u03b2) \u2212 1]), '
     'the Gini coefficient of incidence rates, the coefficient of variation, and the '
     'proportion-normalised provincial allocation. Complete code is in Supplementary S8.'],
    ['11', 'Describe how candidate models were evaluated and how the final model(s) were selected.',
     'Methods: statistical analysis. Break-points were selected by exhaustive grid search over candidate locations '
     'with model selection by Bayesian information criterion, subject to a minimum of four '
     'observations in the first segment and three in the last. No new burden model was fitted; the '
     'model under evaluation is the published GBD 2023 estimate.'],
    ['12', 'Provide the results of an evaluation of model performance, if done, as well as the '
           'results of any relevant sensitivity analysis.',
     'Results: level discordance through discordant trajectories; Supplementary S10; Discussion: correction of the earlier conclusion; Supplementary Table S6 (five sensitivity '
     'analyses: alternative official series, exclusion of 2024\u20132025, proportion-normalised '
     'provincial allocation, alternative stage-trend windows, and a matched model window).'],
    ['13', 'Describe methods for calculating uncertainty of the estimates. State which sources of '
           'uncertainty were, and were not, accounted for.',
     'Methods: definitions and construct alignment (final paragraph), Methods: statistical analysis and Methods: ethics and data availability; Discussion: strengths and limitations. The 95% uncertainty '
     'intervals supplied by GBD are reported with all model values (Supplementary S3). GBD '
     'posterior draws are not released for post-estimation use, so the model intervals were not '
     'propagated into the comparison; intervals attached to fitted trends quantify the precision of '
     'the fitted regression and not the uncertainty of the underlying estimates.'],
    ['14', 'State how analytic or statistical source code used to generate estimates can be accessed.',
     'Methods: ethics and data availability; Supplementary S8 (script manifest, software versions and run order); Data and '
     'code availability statement.'],
    ['15', 'Provide published estimates in a file format from which data can be efficiently extracted.',
     'Supplementary data files S1\u2013S6a (CSV). Model estimates are reproduced in Supplementary '
     'Table S3 with the intervals supplied by GBD.'],
    ['16', 'Report a quantitative measure of the uncertainty of the estimates.',
     'Abstract; Results: level discordance; Supplementary Table S11; Supplementary Table S3 (GBD 95% uncertainty intervals); '
     'Supplementary Table S6a (regression interval estimates for fitted trends).'],
    ['17', 'Interpret results in light of existing evidence. If updating a previous set of '
           'estimates, describe the reasons for changes in estimates.',
     'Background; Discussion: three mechanisms through correction of the earlier conclusion. The comparison is set against the published '
     'GBD\u2013China notifiable-disease comparison and the national syphilis trend literature; '
     'The Discussion states explicitly which earlier conclusion is revised and why.'],
    ['18', 'Discuss limitations of the estimates. Include a discussion of any modelling assumptions '
           'or data limitations that affect interpretation.',
     'Discussion: strengths and limitations. Limitations are grouped into data-source structural limitations (absence of '
     'sex-disaggregated notifications; no provincial stage breakdown for 2021\u20132024; missing '
     'age-specific rates for 2024; the unresolved mechanism of the duplication artefact) and '
     'methodological limitations (no propagation of GBD uncertainty; stage composition of '
     'tertiary notifications dependent on diagnostic behaviour; stock-to-flow decomposition '
     'presented as a construct mapping rather than a numerical identity).'],
]

# ── S7.2 RECORD（Benchimol EI 等, PLoS Med 2015;12(10):e1001885）────────────
RECORD_HEAD = ['STROBE #', 'STROBE item', 'RECORD-specific item (where applicable)',
               'Where reported']

RECORD_ROWS = [
    ['1', 'Indicate the study design with a commonly used term in the title or abstract; provide an '
          'informative and balanced summary of what was done and what was found.',
     '1.1 The type of data used should be specified in the title or abstract; when possible, the '
     'name of the databases should be included. 1.2 The geographic region and time frame should be '
     'reported in the title or abstract. 1.3 If linkage between databases was conducted, this '
     'should be clearly stated.',
     'Title and Abstract. Title names both data types (\u201cGlobal Burden of Disease 2023 '
     'estimates\u201d and \u201cnational syphilis notification\u201d); the Abstract names the '
     'National Notifiable Disease Reporting System, China, and the time frames 1990\u20132023 and '
     '1998\u20132025. 1.3: not applicable \u2014 no person-level or record-level linkage was '
     'performed; all streams were analysed as published aggregates.'],
    ['2', 'Explain the scientific background and rationale.', '\u2014',
     'Background.'],
    ['3', 'State specific objectives, including any prespecified hypotheses.', '\u2014',
     'Background, final paragraph. The objective was prespecified as a systematic comparison '
     'of level, trend and structure, without a directional hypothesis about which stream is '
     'correct.'],
    ['4', 'Present key elements of study design early in the paper.', '\u2014',
     'Methods: study design and data sources, first paragraph (cross-sectional comparison of two independently produced '
     'evidence streams, 2004\u20132023 common window).'],
    ['5', 'Describe the setting, locations and relevant dates.', '\u2014',
     'Methods: study design and data sources. Setting: China, national and 31 provincial-level regions; surveillance from the '
     'start of electronic reporting in 2004, extended where available to 1998\u20132025; model '
     'estimates 1990\u20132023.'],
    ['6', 'Give eligibility criteria and the sources and methods of selection of participants.',
     '6.1 Methods of study population selection (such as codes or algorithms) should be listed in '
     'detail. 6.2 Validation studies of the codes or algorithms should be referenced; if validation '
     'was conducted for this study, methods and results should be provided. 6.3 If linkage was '
     'involved, consider a flow diagram.',
     'Methods: definitions and construct alignment (case definitions and construct alignment) and Methods: study design and data sources (which published series were '
     'included). 6.2 is satisfied by Methods: statistical analysis (alignment of single-year and 5-year age bands), '
     'Methods: spatial inequality and Supplementary S9 (verification of the provincial duplication artefact against three '
     'independent provincial bulletins). 6.3: not applicable \u2014 no linkage.'],
    ['7', 'Clearly define all outcomes, exposures, predictors, potential confounders and effect '
          'modifiers. Give diagnostic criteria if applicable.',
     '7.1 A complete list of codes and algorithms used to classify exposures, outcomes, '
     'confounders and effect modifiers should be provided.',
     'Methods: definitions and construct alignment and Methods: statistical analysis; Table 1; Supplementary Table S4. Outcome: model-estimated incident '
     'infections (GBD cause ID 394, \u201csyphilis\u201d) and notified syphilis cases under the '
     'national notifiable-disease category, with stage categories primary, secondary, tertiary, '
     'congenital and latent. No administrative code list beyond the disease category is used, as '
     'the source tables are published disease-level aggregates.'],
    ['8', 'For each variable of interest, give sources of data and details of methods of assessment.',
     '\u2014',
     'Methods: study design and data sources; Table 1. Comparability between the two streams is addressed explicitly in '
     'Methods: definitions and construct alignment: the streams do not measure the same quantity, and the analysis is designed around that '
     'difference rather than assuming equivalence.'],
    ['9', 'Describe any efforts to address potential sources of bias.', '\u2014',
     'Methods: definitions and construct alignment (statistical-basis offsets treated as measurable quantities rather than errors), '
     'Methods: spatial inequality and Supplementary S9 (provincial duplication artefact), Methods: sensitivity analyses (sensitivity analyses); '
     'Discussion: strengths and limitations.'],
    ['10', 'Explain how the study size was arrived at.', '\u2014',
     'Methods: study design and data sources. The comparison uses the complete set of years and regions for which both '
     'streams publish values; no sampling was involved and no sample-size calculation applies.'],
    ['11', 'Explain how quantitative variables were handled, and which groupings were chosen and why.',
     '\u2014',
     'Methods: statistical analysis through spatial inequality. Ratios were analysed on the logarithmic scale; age was grouped into '
     'the 5-year bands used by the model and the 26 groups used by the national surveillance '
     'tables, with single-year groups below age 10 averaged within each 5-year band (Methods: statistical analysis); '
     'provinces are reported both as rates and as shares (Methods: spatial inequality).'],
    ['12', 'Describe all statistical methods, including those used to control for confounding; '
           'subgroup and interaction analyses; how missing data were addressed; and sensitivity '
           'analyses.',
     '12.1 Describe the extent to which the investigators had access to the database population. '
     '12.2 Provide information on the data cleaning methods used. 12.3 State whether the study '
     'included data linkage.',
     'Methods: statistical analysis (level, trend, structural and attribution analyses), Methods: three-way decomposition of the notified burden, Methods: spatial inequality and Methods: sensitivity analyses. '
     '12.1: the investigators accessed published aggregate records only, through public interfaces, '
     'and had no access to case-level records (Methods: ethics and data availability). 12.2: reconstruction and verification of the '
     'provincial series and the chain-linked monthly tables are described in Methods: spatial inequality and Supplementary '
     'S9. 12.3: no linkage. No confounder adjustment applies, as no individual-level exposure\u2013'
     'outcome model is fitted; the attribution analysis is reported as an unadjusted correlation '
     'with an explicit caution against causal reading.'],
    ['13', 'Report the numbers of individuals at each stage of the study.',
     '13.1 Describe in detail the selection of the persons included, including filtering based on '
     'data quality, data availability and linkage.',
     'Results: level discordance; Supplementary Table S4. The unit of analysis is an aggregated year\u2013'
     'region\u2013stage cell rather than an individual; which annual series were retained, imputed '
     'or excluded is set out in Supplementary S4, and the filtering of the provincial series is '
     'described in Supplementary S9.'],
    ['14', 'Give characteristics of study participants and information on exposures and potential '
           'confounders; indicate missing data for each variable.',
     '\u2014',
     'Results: level discordance through provincial inequality; Tables 1\u20137; Supplementary Tables S1\u2013S6a. Missing values are '
     'flagged explicitly: series B1 is unavailable for 2010\u20132011; provincial stage breakdowns '
     'are unavailable after 2020; age-specific rates are unavailable for 2024; sex-disaggregated '
     'notifications are unavailable throughout.'],
    ['15', 'Report numbers of outcome events or summary measures.',
     '\u2014',
     'Results: level discordance through provincial inequality; Supplementary Tables S11\u2013S16; Supplementary Tables S1\u2013S6a.'],
    ['16', 'Give unadjusted estimates and, if applicable, confounder-adjusted estimates and their '
           'precision.',
     '\u2014',
     'Results: level discordance through provincial inequality; Supplementary Table S11 (discordance quantified with point estimates and intervals '
     'for the fitted trends). No adjusted estimates apply (see item 12).'],
    ['17', 'Report other analyses done \u2014 for example, analyses of subgroups and interactions, '
           'and sensitivity analyses.',
     '\u2014',
     'Results: sex structure through provincial inequality (sex, age, congenital and provincial subgroups); Supplementary S10 and '
     'Supplementary Table S6 (sensitivity analyses).'],
    ['18', 'Summarise key results with reference to study objectives.', '\u2014',
     'Discussion: principal findings; Conclusions.'],
    ['19', 'Discuss limitations of the study, taking into account sources of potential bias or '
           'imprecision, and the direction and magnitude of any potential bias.',
     '19.1 Discuss the implications of using data that were not created or collected to answer the '
     'specific research question(s), including misclassification bias, unmeasured confounding, '
     'missing data and changing eligibility over time.',
     'Discussion: strengths and limitations. 19.1 is addressed directly: both streams were produced for other purposes, '
     'and the manuscript states where misclassification (stage assignment, diagnostic accuracy), '
     'missing data (no sex-disaggregated notifications; no post-2020 provincial stage data) and '
     'changing eligibility (the 1998\u20132003 case definition; the 2024\u20132025 reporting basis) '
     'limit interpretation.'],
    ['20', 'Give a cautious overall interpretation of results considering objectives, limitations, '
           'multiplicity of analyses, results from similar studies and other relevant evidence.',
     '\u2014',
     'Discussion: three mechanisms through transferability; Conclusions. Wording throughout is calibrated '
     '(\u201cconsistent with a need for local calibration\u201d rather than \u201cerror\u201d) and '
     'the attribution analysis is reported without a causal reading.'],
    ['21', 'Discuss the generalisability (external validity) of the study results.', '\u2014',
     'Discussion: transferability (transferability of the model-versus-surveillance reconciliation framework to '
     'HIV, tuberculosis and hepatitis, for which both model estimates and notification data exist).'],
    ['22', 'Give the source of funding and the role of the funders.',
     '22.1 Provide information on how to access any supplemental information such as the study '
     'protocol, raw data or programming code.',
     'Declarations (Funding; Data and code availability). 22.1: raw retrieved report pages, derived '
     'datasets and all analysis code are described in Supplementary S8 and supplied as '
     'supplementary data files.'],
]

# ── S8 脚本清单 ────────────────────────────────────────────────────────────
S8_HEAD = ['Script', 'Purpose', 'Principal outputs']
S8_ROWS = [
    ['scripts/fetch_all.py',
     'Retrieve the GBD Results Tool exports for the cause \u201csyphilis\u201d (cause ID 394), '
     'China, 1990\u20132023, and the published national notifiable-disease pages.',
     'raw/GBD exports; raw/NNDRS_syphilis_annual.csv (skeleton)'],
    ['scripts/parse_all.py',
     'Parse the retrieved pages into analysis tables.',
     'raw/NNDRS_syphilis_annual.csv; raw/NNDRS_syphilis_stage.csv; '
     'raw/NNDRS_province_syphilis_2004_2020.csv; raw/NNDRS_age_syphilis_2004_2020.csv'],
    ['scripts/verify.py',
     'Reconcile the assembled national series against the original published tables and against '
     'the reproduction of the same values in the annual statistical bulletins.',
     'consistency log; corrected annual series'],
    ['scripts/analyze.py, scripts/analyze2.py',
     'First-pass descriptive analyses used to scope the comparison.',
     'working descriptive outputs'],
    ['scripts/fetch_2021_2024.py',
     'Construct and retrieve the report URLs for the 2021\u20132024 provincial and age-specific '
     'return (the front-end year selector stops at 2020, so the URLs must be built directly).',
     'batch/zone_ext/*.html; batch/age_ext/*.html; batch/month_ext/*.html'],
    ['scripts/pgrid.py',
     'Report-interface parsers: read the 26-column and 6-column report layouts and map unlabelled '
     'rows to provinces by standard province order.',
     'parsed report frames'],
    ['scripts/verify_2x_defect.py',
     'Verify the two-fold duplication: parity test on all returned values, national reconciliation '
     'against series A, and comparison with five independent values from provincial statistical '
     'bulletins.',
     'supplementary/data/S9_duplication_artefact_evidence.csv'],
    ['scripts/build_2021_2024.py',
     'Build the extended 2004\u20132024 provincial panel and the 2021\u20132024 age panel, applying '
     'the \u00f72 correction, with built-in assertions (provincial sum equals the national row; the '
     'corrected national value equals series A; every corrected value is integral).',
     'processed/province_year_incidence_2004_2024.csv; '
     'processed/province_year_cases_2004_2024.csv; '
     'processed/national_age_incidence_2021_2024.csv; '
     'processed/province_inequality_2004_2024.csv'],
    ['scripts/verify_breakpoint.py',
     'Test the apparent 2024\u20132025 discontinuity in the notification series and establish that '
     'it reflects the reporting-basis transition rather than a change in transmission.',
     'docs/07_2024_2025断点核实报告.md'],
    ['scripts/p2_data.py',
     'Assemble the six data streams into the cross-system ratio series and fit the piecewise '
     'log-linear models, reporting APC, both AAPC variants and EAPC for every series.',
     'processed/gbd_incidence_series.csv; processed/p2_ratio_series.csv; '
     'processed/joinpoint_p2.csv'],
    ['scripts/build_tables.py',
     'Compute all values reported in Table 1 and Supplementary Tables S11\u2013S16.',
     'tables/Table1.csv \u2026 Table7.csv'],
    ['scripts/figures_P2.py, scripts/figures_P3.py',
     'Render Figures 1\u20135 at 300 dpi in both raster and vector formats.',
     'figures/Fig1\u2013Fig5 .png / .pdf'],
    ['scripts/build_tables_docx.py',
     'Render Table 1 (main text) and Supplementary Tables S11\u2013S16 in the journal three-line format.',
     'tables/Tables_Table1_SuppS11-S16_定稿.docx'],
    ['scripts/build_methods_docx.py, scripts/build_results_docx.py',
     'Render the Methods and Results sections on the manuscript template.',
     'Component drafts in the working folder (not part of the submission)'],
    ['scripts/build_manuscript_docx.py',
     'Assemble the complete manuscript (English submission version and Chinese review version), '
     'including reference renumbering, the Lancet mid-dot decimal conversion and the citation cross-check.',
     'manuscript/Manuscript_Submission_LancetRHWP_v1.docx; manuscript/Manuscript_FullText_v1.docx; manuscript/Manuscript_Chinese_Full_v1.docx'],
    ['scripts/build_supplementary.py',
     'Generate this Supplementary file and the machine-readable supplementary data files.',
     'supplementary/Supplementary_Information_S1-S10.docx; supplementary/data/*.csv'],
]

S8_ORDER = [
    'Raw retrieval and parsing: fetch_all.py \u2192 parse_all.py \u2192 verify.py',
    'Provincial and age extension: fetch_2021_2024.py \u2192 verify_2x_defect.py \u2192 '
    'build_2021_2024.py \u2192 verify_breakpoint.py',
    'Analysis base: p2_data.py \u2192 build_tables.py',
    'Figures: figures_P2.py \u2192 figures_P3.py',
    'Rendering: build_tables_docx.py; build_methods_docx.py; build_results_docx.py; '
    'build_manuscript_docx.py; build_supplementary.py',
]

S8_SOFT = [
    'Python 3.13',
    'numpy 2.x, pandas 2.x (data assembly and statistics)',
    'matplotlib 3.x (figures, 300 dpi, Arial, vector PDF)',
    'All decimal points in the manuscript, tables, figure labels and this file follow the Lancet '
    'convention of a mid-dot (U+00B7, e.g. 23\u00b74); machine-readable CSV files retain the ordinary '
    'decimal point so that the values remain numerically parseable.',
    'scipy 1.x (correlation analyses in Results: the gap is not explained by under-reporting)',
    'python-docx 1.x (manuscript and supplementary rendering)',
    'Fitting routines are implemented directly (numpy least squares) rather than through a '
    'joinpoint package, so that break-point search, model selection and the three trend summary '
    'estimators are all explicit and reproducible; the implementation is validated against the '
    'published behaviour of the NCI Joinpoint convention for the AAPC.',
]

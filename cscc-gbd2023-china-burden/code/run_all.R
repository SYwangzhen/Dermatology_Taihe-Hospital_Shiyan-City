## ============================================================
## run_all.R — 主入口（按序执行全部分析）
## 用法：
##   cd <工程>/R
##   Rscript run_all.R --demo    # 合成数据演示（默认）
##   Rscript run_all.R --real    # 读取 data/raw/ 真实下载数据
## ============================================================
source(file.path(getwd(), "00_config.R"))    # 需在 R/ 目录运行
source(file.path(R_DIR, "01_load_clean.R"))
source(file.path(R_DIR, "02_eapc_trend.R"))
source(file.path(R_DIR, "03_joinpoint.R"))
source(file.path(R_DIR, "04_apc.R"))
source(file.path(R_DIR, "05_decomposition.R"))
source(file.path(R_DIR, "06_figures.R"))
source(file.path(R_DIR, "07_tables.R"))

cat("==========================================\n")
cat(sprintf("China cSCC GBD 2023 pipeline  |  mode: %s\n",
            if (DEMO_MODE) "DEMO (synthetic)" else "REAL (downloaded data)"))
cat("==========================================\n")

## 1) 读入
dat <- load_data()

## 2) EAPC + 描述统计（Table1 数据源）
d_trend <- trend_stats(dat$asr)

## 3) Joinpoint（Incidence/Deaths 分段）
jp <- run_joinpoint(dat$asr)

## 4) APC 视角（描述性）
apc <- run_apc(dat$agesex)

## 5) 分解
decomp <- run_decomposition(dat$agesex)

## 6) 图
render_all_figures(dat$asr, jp, apc, decomp)

## 7) 表
tab1 <- make_table1(dat$asr, dat$agesex)
jt   <- save_joinpoint_tables(jp)

## 7b) 补充 CSV 导出（eTable 2/3 数值；08_extract_supp.R 独立运行时输出相同内容，
##     主入口亦直接写出，保证"单一入口生成全部声明输出"）
write.csv(apc$cohort, file.path(OUT_TAB, "APC_cohort_summary.csv"), row.names = FALSE)
dec_out <- do.call(rbind, decomp)
write.csv(dec_out, file.path(OUT_TAB, "Decomposition_summary.csv"), row.names = FALSE)
cat("[out] APC_cohort_summary.csv, Decomposition_summary.csv written to output/tables\n")

## 8) 分解闭合断言：growth+aging+epi == net（每区间相对容差 1e-6）
for (m in names(decomp)) {
  dfm <- decomp[[m]]
  resid <- dfm$population_growth + dfm$population_aging +
           dfm$epidemiological_change - dfm$total_change
  rel <- abs(resid) / pmax(1, abs(dfm$total_change))
  if (max(rel) > 1e-6)
    stop(sprintf("decomposition not closed for %s (max rel residual %.3g)", m, max(rel)))
}
cat("[check] decomposition closure assertions passed (7 intervals x 2 measures).\n")

## 9) Python 阶段（真实模式）：重分析、HAC 敏感性、证据表（eTable 5 / >=65 / M-I）、
##    最终版 Figures 2-4（分解菱形图 / 年龄别演化 / 跨周期对照，数据取自管线输出并断言）
if (!DEMO_MODE) {
  py <- Sys.getenv("PYTHON", unset = "python")
  for (script in c("reanalysis_v23.py", "hac_eapc.py", "evidence_tables.py",
                   "make_figures_final.py")) {
    p <- file.path(BASE, script)
    if (!file.exists(p)) {              # 投稿 zip 布局：脚本位于 code/ 子目录
      p2 <- file.path(BASE, "code", script)
      if (file.exists(p2)) p <- p2 else stop("missing Python script: ", p)
    }
    cat(sprintf("[py] running %s ...\n", script))
    st <- system2(py, shQuote(p), stdout = "", stderr = "")
    if (st != 0) stop("Python stage failed: ", script, " (exit ", st, ")")
  }
}

## 10) 控制台速览
cat("\n---- Snapshot (China / Both sexes / start->end) ----\n")
print(tab1[tab1$location == FOCUS_LOC & tab1$sex == "Both",
           c("measure", "cases_1990", "cases_2023", "ASR_1990", "ASR_2023", "EAPC")])
cat("\nAll done. Outputs: output/figures, output/tables.\n")
cat(if (DEMO_MODE) "\n! DEMO synthetic data - numbers NOT citable.\n  Download real GBD 2023 data then rerun: Rscript run_all.R --real\n"
    else "\nReal-data results.\n")

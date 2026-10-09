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
cat(sprintf("China Syphilis GBD 2023 pipeline (CDA abstract)  |  mode: %s\n",
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

## 8) 控制台速览
cat("\n---- Snapshot (China / Both sexes / start->end) ----\n")
print(tab1[tab1$location == FOCUS_LOC & tab1$sex == "Both",
           c("measure", "cases_1990", "cases_2023", "ASR_1990", "ASR_2023", "EAPC")])
cat("\nAll done. Outputs: output/figures, output/tables.\n")
cat(if (DEMO_MODE) "\n! DEMO synthetic data - numbers NOT citable.\n  Download real GBD 2023 data then rerun: Rscript run_all.R --real\n"
    else "\nReal-data results.\n")

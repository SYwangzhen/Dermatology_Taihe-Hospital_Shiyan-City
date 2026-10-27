## ============================================================
## 08_extract_supp.R — 导出 eTable 2/3 数值（supplement）
## 供 Manuscript Results/图注引用；输出 output/tables/
## 用法：Rscript 08_extract_supp.R --real   （或 --demo）
## 注：v2.0（审稿 N2 修订）出生队列仅保留 55-79 岁窗口内完全
##     可观测的 1935/1940 两队列，参照队列 = 1935。
## ============================================================
source(file.path(getwd(), "00_config.R"))
source(file.path(R_DIR, "01_load_clean.R"))
source(file.path(R_DIR, "04_apc.R"))
source(file.path(R_DIR, "05_decomposition.R"))

args <- commandArgs(trailingOnly = TRUE)
if ("--real" %in% args) DEMO_MODE <<- FALSE
if (DEMO_MODE) { source(file.path(R_DIR, "demo_data.R")) }

dat <- load_data()

## ---- 1) APC cohort index（China, Both, Incidence；仅全可观测队列）----
apc <- run_apc(dat$agesex)
cq  <- apc$cohort
write.csv(cq, file.path(OUT_TAB, "APC_cohort_summary.csv"), row.names = FALSE)
cat("\n[APC cohort index] China Both Incidence; fully observed cohorts only, ref 1935 = 1\n")
print(cq, row.names = FALSE)

## ---- 2) 分解（China, Both, Incidence & Deaths）----
dec <- run_decomposition(dat$agesex)
out <- do.call(rbind, dec)
write.csv(out, file.path(OUT_TAB, "Decomposition_summary.csv"), row.names = FALSE)
cat("\n[Decomposition] China Both, counts change allocated to 3 factors\n")
print(out, row.names = FALSE)

cat("\nSupplementary CSVs written to:", normalizePath(file.path(OUT_TAB), winslash = "/"), "\n")

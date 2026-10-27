## ============================================================
## 00_config.R — 中国皮肤鳞状细胞癌(cSCC) GBD 2023 分析管线 · 配置
## 目的：中国 cSCC 1990-2023 负担 + EAPC + Joinpoint + APC + 分解
## 运行方式：Rscript run_all.R --demo    （合成数据演示全流程）
##           Rscript run_all.R --real    （读 data/raw/ 真实下载数据）
## ============================================================
options(stringsAsFactors = FALSE, scipen = 999)

## Windows 下把 locale 切到用户默认（中文路径/PNG 设备必需）
if (.Platform$OS.type == "windows") {
  try(Sys.setlocale("LC_CTYPE", ""), silent = TRUE)
  try(Sys.setlocale("LC_COLLATE", ""), silent = TRUE)
}

## ---- 路径（运行前 cd 到 <工程>/R/，工程根在其上级）----
R_DIR   <- getwd()                                # 当前工作目录 = R/
BASE    <- normalizePath(file.path(R_DIR, ".."), winslash = "/")
DATA_DIR <- file.path(BASE, "data", "raw")
OUT_FIG  <- file.path(BASE, "output", "figures")
OUT_TAB  <- file.path(BASE, "output", "tables")
dir.create(DATA_DIR, recursive = TRUE, showWarnings = FALSE)
dir.create(OUT_FIG,  recursive = TRUE, showWarnings = FALSE)
dir.create(OUT_TAB,  recursive = TRUE, showWarnings = FALSE)

`%||%` <- function(a, b) if (is.null(a) || length(a) == 0 || (length(a)==1 && is.na(a))) b else a

## ---- 命令行参数（demo / real）----
args <- commandArgs(trailingOnly = TRUE)
DEMO_MODE <- if (any(grepl("^--real$", args))) FALSE else TRUE

## ---- 分析口径 ----
YEARS      <- 1990:2023
MEASURES   <- c("Incidence", "Prevalence", "Deaths", "DALYs")
MEAS_LABEL <- c(Incidence = "ASIR", Prevalence = "ASPR",
                Deaths = "ASDR", DALYs = "DALY rate")
SEXES      <- c("Male", "Female", "Both")
FOCUS_LOC  <- "China"          # 分析主体
REF_LOCS   <- c("Global", "High SDI")  # 对照（Results Tool 中 SDI 层 location name 即 "High SDI"）
## 年龄组（GBD 5 岁分组 20 组；分解/APC 共用；真实与 demo 数据均归一为此命名）
AGE_GROUPS <- c("0-4","5-9","10-14","15-19","20-24","25-29","30-34",
                "35-39","40-44","45-49","50-54","55-59","60-64",
                "65-69","70-74","75-79","80-84","85-89","90-94","95+")

## ---- 真实数据文件名（按 01 下载快照存放）----
FILE_ASR   <- file.path(DATA_DIR, "A_ASR_1990_2023.csv")     # age-standardized 年度序列
FILE_AGESEX<- file.path(DATA_DIR, "B_age_sex_1990_2023.csv")  # age×sex 计数/率
FILE_POP   <- file.path(DATA_DIR, "C_Population_1990_2023.csv") # GBD 2023 人口（直接下载，解压自 IHME-GBD_2023_DATA-670c8efe-1.zip）

## ---- 输出前缀（demo 模式下加 _DEMO 后缀，避免误当正式结果）----
TAG <- if (DEMO_MODE) "_DEMO" else ""
WATERMARK <- if (DEMO_MODE) "SYNTHETIC DEMO DATA - replace with real GBD 2023 downloads" else ""

cat(sprintf("[config] BASE=%s\n[config] DEMO_MODE=%s\n", BASE, DEMO_MODE))

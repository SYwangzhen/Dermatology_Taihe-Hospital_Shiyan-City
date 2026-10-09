## 重出 Table1（EAPC/UI 分隔符修复版）
source("00_config.R")
DEMO_MODE <- FALSE
WATERMARK <- ""
TAG       <- ""
source("01_load_clean.R")
source("02_eapc_trend.R")
source("07_tables.R")

dat <- load_data()
invisible(make_table1(dat$asr, dat$agesex))
cat("[done] Table1 regenerated\n")

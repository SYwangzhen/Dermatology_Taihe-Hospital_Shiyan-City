## 只重出 Figure2（分解图，图例移至整图底部单行）
source("00_config.R")
DEMO_MODE <- FALSE
WATERMARK <- ""
TAG       <- ""          # 覆盖 DEMO_MODE 后必须同步，否则文件名带 _DEMO
source("01_load_clean.R")
source("05_decomposition.R")
source("06_figures.R")

dat <- load_data()
decomp <- run_decomposition(dat$agesex)
fig2_decomp(decomp)
cat("[done] Figure2 regenerated (real data)\n")

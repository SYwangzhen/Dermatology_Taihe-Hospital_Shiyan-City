## export_extra_results.R -- 导出分解结果与年龄模式数字（真实模式）
source("00_config.R")
DEMO_MODE <- FALSE
source("01_load_clean.R")
source("02_eapc_trend.R")
source("03_joinpoint.R")
source("04_apc.R")
source("05_decomposition.R")

dat    <- load_data()
decomp <- run_decomposition(dat$agesex)

out_dir <- file.path(BASE, "output", "tables")
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

## ---- 1) 分解表：各测量 x 各时段三因子贡献 ----
rows <- list()
for (ms in names(decomp)) {
  d <- decomp[[ms]]
  for (i in seq_along(d$period)) {
    rows[[length(rows) + 1]] <- data.frame(
      measure = ms, period = d$period[i],
      population_growth = round(d$population_growth[i], 0),
      population_aging  = round(d$population_aging[i], 0),
      epidemiological_change = round(d$epidemiological_change[i], 0),
      total_change = round(d$population_growth[i] + d$population_aging[i] + d$epidemiological_change[i], 0))
  }
}
decomp_tab <- do.call(rbind, rows)
write.csv(decomp_tab, file.path(out_dir, "Decomposition_summary.csv"), row.names = FALSE)
cat("---- Decomposition (China) ----\n")
print(decomp_tab)

## ---- 2) 2023 中国年龄别发病率 tops（年龄模式）----
ag23 <- dat$agesex[dat$agesex$location == "China" & dat$agesex$sex == "Both" &
                   dat$agesex$measure == "Incidence" & dat$agesex$year == 2023, ]
ag23 <- ag23[order(ag23$rate, decreasing = TRUE), ]
cat("\n---- China 2023 incidence rate by age (top 8) ----\n")
print(ag23[1:8, c("age", "count", "rate")])

## ---- 3) 2023 性别计数 ----
sx <- dat$agesex[dat$agesex$location == "China" & dat$agesex$sex != "Both" &
                 dat$agesex$measure == "Incidence" & dat$agesex$year == 2023, ]
agg <- aggregate(count ~ sex, data = sx, FUN = sum)
cat("\n---- China 2023 incident cases by sex ----\n")
print(agg)

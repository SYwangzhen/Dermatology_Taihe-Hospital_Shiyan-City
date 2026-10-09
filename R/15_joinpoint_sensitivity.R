## ============================================================
## 15_joinpoint_sensitivity.R — 死亡 Joinpoint 末端段敏感性分析
## 背景：主模型 Deaths 最优解含 2021-2023 末端段（仅 3 个年度估计），
##       二轮复审建议补"去掉 2021 断点"的敏感性分析。
## 做法：Deaths 序列强制单断点（BIC 网格择优），即把 2020 断点并入
##       后段，报告合并后 2006-2023 段 APC(95%CI)。
## 输出：output/tables/Joinpoint_sensitivity_deaths.csv
## ============================================================
source("00_config.R")
DEMO_MODE <- FALSE
WATERMARK <- ""
TAG       <- ""
source("01_load_clean.R")
source("03_joinpoint.R")

dat <- load_data()
asr <- dat$asr

d <- asr[asr$location == FOCUS_LOC & asr$sex == "Both" &
         asr$measure == "Deaths" & asr$year %in% YEARS, ]
d <- d[order(d$year), ]
d <- d[is.finite(d$val) & d$val > 0, ]

cat(sprintf("[sensitivity] Deaths n=%d years %d-%d\n",
            nrow(d), min(d$year), max(d$year)))

## —— 强制单断点：BIC 网格择优（候选断点与主模型同规则）——
cand <- grid_knots(d$year)
best1 <- list(bic = Inf, knots = numeric(0))
for (k1 in cand) {
  r <- fit_segments(d$year, d$val, k1)
  if (r$bic < best1$bic) best1 <- list(knots = k1, fit = r$fit, bic = r$bic)
}
cat(sprintf("[sensitivity] best single knot = %d (BIC %.2f)\n",
            best1$knots, best1$bic))

## —— 主模型 2 断点最优（对照，应与 Joinpoint_summary.csv 一致）——
best2 <- find_best_segments(d$year, d$val)
cat(sprintf("[main] 2-knot best = %s (BIC %.2f)\n",
            paste(best2$knots, collapse = ", "), best2$bic))

sm1 <- segment_summary(d$year, d$val, best1)
sm1$model <- "single-knot (2021/2020 breakpoint removed)"
sm2 <- segment_summary(d$year, d$val, best2)
sm2$model <- "main model (2 knots)"

out <- rbind(sm2, sm1)
out <- out[, c("model", "segment", "years", "apc", "apc_lo", "apc_hi", "aapc")]
p_csv <- file.path(OUT_TAB, "Joinpoint_sensitivity_deaths.csv")
write.csv(out, p_csv, row.names = FALSE)
cat("[tab] written:", p_csv, "\n")
print(out, row.names = FALSE, digits = 3)

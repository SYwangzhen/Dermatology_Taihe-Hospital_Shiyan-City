## ============================================================
## 09_n1_evidence.R — 审稿 N1 数值证据（供 13_ResponseLetter 引用）
## 目的：正面回应「分段 APC 与 Table 1 端点/EAPC 数学上不自洽」：
##   1) 端点几何平均增速（CAGR） vs 全期 EAPC（log-linear 回归）
##   2) 剔除 2011-2016 再估计瞬变后的 EAPC（应与 CAGR 接近）
##   3) 3 段模型对 2023 端点的预测 vs GBD 实际点估计（展示未端段
##      斜率被瞬变下行臂主导 → 外推必然低估端点）
##   4) 3 断点(4 段)再拟合（中性化瞬变）供敏感性展示
## 输出：output/tables/N1_evidence.csv + 控制台
## 用法：Rscript 09_n1_evidence.R --real
## ============================================================
source(file.path(getwd(), "00_config.R"))
source(file.path(R_DIR, "01_load_clean.R"))
source(file.path(R_DIR, "03_joinpoint.R"))

args <- commandArgs(trailingOnly = TRUE)
if ("--real" %in% args) DEMO_MODE <<- FALSE
if (DEMO_MODE) { source(file.path(R_DIR, "demo_data.R")) }

dat <- load_data()
asr <- dat$asr
d <- asr[asr$location == FOCUS_LOC & asr$sex == "Both" &
         asr$measure %in% c("Incidence", "Deaths") & asr$year %in% YEARS, ]
d <- d[order(d$measure, d$year), ]

## ---- 工具：log-linear EAPC ----
eapc_fit <- function(sub) {
  fit <- lm(log(val) ~ year, data = sub)
  b <- coef(fit)["year"]; se <- sqrt(vcov(fit)["year", "year"])
  data.frame(eapc = 100 * (exp(b) - 1),
             lo   = 100 * (exp(b - 1.96 * se) - 1),
             hi   = 100 * (exp(b + 1.96 * se) - 1))
}
cagr_fun <- function(v0, v1, n = 33) 100 * ((v1 / v0) ^ (1 / n) - 1)

## ---- 泛化断点搜索（0..max_k 断点，间距 ≥3）----
find_best_k <- function(yr, y, max_k = 3) {
  cand <- grid_knots(yr)
  best <- fit_segments(yr, y, numeric(0))
  best$knots <- numeric(0)
  search <- function(nk, start = 1, cur = numeric(0)) {
    if (nk == 0) { assign("cur", cur, envir = parent.frame()); return(NULL) }
    if (length(cur) == nk) {
      r <- fit_segments(yr, y, cur)
      if (r$bic < best$bic) { best <<- list(knots = cur, fit = r$fit, bic = r$bic) }
      return(NULL)
    }
    lo <- if (length(cur)) match(cur[length(cur)], cand) + 1 else start
    if (lo > length(cand)) return(NULL)
    for (i in lo:length(cand)) {
      k <- cand[i]
      ok <- TRUE
      if (length(cur)) if (k - cur[length(cur)] < 3) ok <- FALSE
      if (ok) search(nk, i + 1, c(cur, k))
    }
  }
  for (nk in 1:max_k) search(nk)
  best
}

rows <- list()
for (m in c("Incidence", "Deaths")) {
  sub <- d[d$measure == m, ]
  sub <- sub[is.finite(sub$val) & sub$val > 0, ]
  v1990 <- sub$val[sub$year == 1990]; v2023 <- sub$val[sub$year == 2023]
  ## 关键年份（瞬变前后）——展示 ASIR 驼峰
  yr_key <- c(1990, 2008, 2010, 2015, 2016, 2021, 2023)
  for (yy in yr_key) {
    vv <- sub$val[sub$year == yy]
    rows[[length(rows) + 1]] <- data.frame(
      measure = m, item = sprintf("ASR %d", yy), value = round(vv, 4))
  }
  ## 端点 CAGR
  rows[[length(rows) + 1]] <- data.frame(
    measure = m, item = "endpoint CAGR 1990-2023 (%)", value = round(cagr_fun(v1990, v2023), 3))
  ## 全期 EAPC
  e_full <- eapc_fit(sub)
  rows[[length(rows) + 1]] <- data.frame(
    measure = m,
    item = "EAPC full 1990-2023 (%) [95% CI]",
    value = round(e_full$eapc, 2)); rows[[length(rows)]]$item <- sprintf("%s [%s, %s]",
      rows[[length(rows)]]$item, round(e_full$lo, 2), round(e_full$hi, 2))
  ## 剔除 2011-2016 的 EAPC
  sub_noT <- sub[!(sub$year %in% 2011:2016), ]
  e_noT <- eapc_fit(sub_noT)
  rows[[length(rows) + 1]] <- data.frame(
    measure = m,
    item = "EAPC excl 2011-2016 (%) [95% CI]",
    value = round(e_noT$eapc, 2)); rows[[length(rows)]]$item <- sprintf("%s [%s, %s]",
      rows[[length(rows)]]$item, round(e_noT$lo, 2), round(e_noT$hi, 2))

  ## 3 段（BIC，2 断点）→ 对 2023 的模型拟合值（在原序列上 predict 后取 2023）
  b3 <- find_best_k(sub$year, sub$val, max_k = 2)
  pred_all <- exp(as.numeric(predict(b3$fit)))
  names(pred_all) <- sub$year
  pred_2023 <- pred_all[as.character(2023)]
  rows[[length(rows) + 1]] <- data.frame(measure = m,
    item = "3-seg (BIC) knots",
    value = paste(b3$knots, collapse = ","))
  rows[[length(rows) + 1]] <- data.frame(
    measure = m, item = "3-seg predicted ASR 2023", value = round(as.numeric(pred_2023), 3))
  sm3 <- segment_summary(sub$year, sub$val, b3)
  for (i in seq_len(nrow(sm3))) {
    rows[[length(rows) + 1]] <- data.frame(
      measure = m,
      item = sprintf("3-seg APC %s (%%) [95%% CI]", sm3$years[i]),
      value = round(sm3$apc[i], 2))
    rows[[length(rows)]]$item <- sprintf("%s [%s, %s]", rows[[length(rows)]]$item,
                                         round(sm3$apc_lo[i], 2), round(sm3$apc_hi[i], 2))
  }
  rows[[length(rows) + 1]] <- data.frame(
    measure = m, item = "3-seg AAPC (%)", value = round(sm3$aapc[1], 2))

  ## 4 段（BIC，3 断点）
  b4 <- find_best_k(sub$year, sub$val, max_k = 3)
  rows[[length(rows) + 1]] <- data.frame(measure = m,
    item = "4-seg (BIC, 3 knots) knots",
    value = paste(b4$knots, collapse = ","))
  sm4 <- segment_summary(sub$year, sub$val, b4)
  for (i in seq_len(nrow(sm4))) {
    rows[[length(rows) + 1]] <- data.frame(
      measure = m,
      item = sprintf("4-seg APC %s (%%) [95%% CI]", sm4$years[i]),
      value = round(sm4$apc[i], 2))
    rows[[length(rows)]]$item <- sprintf("%s [%s, %s]", rows[[length(rows)]]$item,
                                         round(sm4$apc_lo[i], 2), round(sm4$apc_hi[i], 2))
  }
  rows[[length(rows) + 1]] <- data.frame(
    measure = m, item = "4-seg AAPC (%)", value = round(sm4$aapc[1], 2))
  cat(sprintf("[%s] 3-seg BIC=%s 4-seg BIC=%s\n", m,
              round(b3$bic,1), round(b4$bic,1)))
}

ev <- do.call(rbind, rows)
write.csv(ev, file.path(OUT_TAB, "N1_evidence.csv"), row.names = FALSE)
print(ev, row.names = FALSE)
cat("\nN1 evidence written to:", file.path(OUT_TAB, "N1_evidence.csv"), "\n")

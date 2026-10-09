## ============================================================
## 02_eapc_trend.R — 负担描述 + EAPC（整体趋势）
## 产出：d_trend（每 location×sex×measure 的 1990/2023 值 + EAPC(95%CI)）
## ============================================================

calc_eapc <- function(x, y) {
  ## x = 年份, y = ASR；EAPC = 100*(exp(beta)-1)
  fit <- lm(log(y) ~ x)
  b   <- unname(coef(fit)[2])
  ci  <- unname(confint(fit)[2, ])
  c(eapc = 100 * (exp(b) - 1),
    lo   = 100 * (exp(ci[1]) - 1),
    hi   = 100 * (exp(ci[2]) - 1))
}

trend_stats <- function(d_asr) {
  ## 仅用 Rate(ASR) 且 location ∈ FOCUS∪REF
  d <- d_asr[d_asr$location %in% c(FOCUS_LOC, REF_LOCS), ]
  d <- d[d$measure %in% MEASURES, ]
  yrs_use <- YEARS
  d <- d[d$year %in% yrs_use, ]

  rows <- split(d, list(d$location, d$sex, d$measure), drop = TRUE)
  res <- do.call(rbind, lapply(rows, function(sub) {
    sub <- sub[order(sub$year), ]
    y0 <- sub$year[1]; y1 <- sub$year[nrow(sub)]
    v0 <- sub$val[1];        v1 <- sub$val[nrow(sub)]
    u0 <- sub$upper[1];      u1 <- sub$upper[nrow(sub)]
    l0 <- sub$lower[1];      l1 <- sub$lower[nrow(sub)]
    e  <- calc_eapc(sub$year, sub$val)
    data.frame(location = sub$location[1], sex = sub$sex[1],
               measure  = sub$measure[1],
               year0 = y0, value0 = v0, lower0 = l0, upper0 = u0,
               year1 = y1, value1 = v1, lower1 = l1, upper1 = u1,
               pct_change = (v1 - v0) / v0 * 100,
               eapc = e[["eapc"]], eapc_lo = e[["lo"]], eapc_hi = e[["hi"]])
  }))
  rownames(res) <- NULL
  res
}

trend_class <- function(eapc_lo, eapc_hi) {
  ifelse(eapc_lo > 0 & eapc_hi > 0, "increase",
  ifelse(eapc_lo < 0 & eapc_hi < 0, "decrease", "stable"))
}

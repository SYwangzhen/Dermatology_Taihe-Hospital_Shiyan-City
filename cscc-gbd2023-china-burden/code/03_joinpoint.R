## ============================================================
## 03_joinpoint.R — 分段趋势（Joinpoint 型）回归
## 方法：log(ASR) ~ 年 的分段线性，断点数 0-2 用 BIC 网格择优；
##       输出每段 APC、总期 AAPC（95%CI）。
## 注：本实现为 segmented log-linear grid-search sensitivity
##     analysis。BIC 的参数惩罚仅计入设计矩阵列数，未计入被
##     网格搜索的断点位置，故结果不等价于 NCI Joinpoint 软件
##     的正式输出；如需正式 Joinpoint 估计，请用 NCI 软件复核
##     （数据可由本脚本导出）。
## ============================================================

## 构造含 breakpoint 的线性设计矩阵（含截距与全部段斜率）
seg_design <- function(yr, knots) {
  X <- cbind(1, yr - min(yr))
  if (length(knots)) for (tk in knots) X <- cbind(X, pmax(yr - tk, 0))
  X
}

fit_segments <- function(yr, y, knots) {
  ## 对断点组合拟合，返回 BIC
  X <- seg_design(yr, knots)
  fit <- lm(log(y) ~ X - 1)
  n <- length(yr); k <- ncol(X)
  list(fit = fit, bic = n * log(sum(resid(fit)^2) / n) + k * log(n))
}

grid_knots <- function(yr) {
  ## 候选断点：距端点 ≥3 年的中间年份
  yr[4:(length(yr) - 3)]
}

find_best_segments <- function(yr, y) {
  cand <- grid_knots(yr)
  best <- list(bic = Inf)
  ## 0 个断点
  r0 <- fit_segments(yr, y, numeric(0))
  best <- list(knots = numeric(0), fit = r0$fit, bic = r0$bic)
  ## 1 个断点
  for (k1 in cand) {
    r <- fit_segments(yr, y, k1)
    if (r$bic < best$bic) best <- list(knots = k1, fit = r$fit, bic = r$bic)
  }
  ## 2 个断点（网格组合，33 年规模下可行）
  if (length(cand) >= 4) {
    for (i in 1:(length(cand) - 2)) for (j in (i + 1):length(cand)) {
      if (cand[j] - cand[i] < 3) next
      r <- fit_segments(yr, y, c(cand[i], cand[j]))
      if (r$bic < best$bic) best <- list(knots = c(cand[i], cand[j]), fit = r$fit, bic = r$bic)
    }
  }
  best
}

segment_summary <- function(yr, y, best) {
  fit <- best$fit; knots <- sort(best$knots)
  X <- seg_design(yr, knots)
  b <- coef(fit); V <- vcov(fit)
  ## 各段斜率（含 95%CI）
  ## 连续铰链（hinge）基：log(y) = b1 + b2·(yr-1990) + Σ g_j·(yr-k_j)+
  ## 段 s 斜率 = b2 + Σ_{j=1..(s-1)} g_j（即全部已进入的铰链斜率之和）。
  ## 修正（2026-09-04 二轮审稿）：旧版 a[2+(s-1)] 仅累加最后一个铰链，
  ## 漏掉中间铰链，导致 ≥2 断点时第 3 段斜率被高估（如 −25.8% vs 真值 −13.4%）。
  nseg <- length(knots) + 1
  seg_lo <- c(min(yr), knots + 1); seg_hi <- c(knots, max(yr))
  slope <- numeric(nseg); se <- numeric(nseg)
  for (s in 1:nseg) {
    a <- rep(0, ncol(X)); a[2] <- 1
    if (s > 1) a[3:(s + 1)] <- 1
    slope[s] <- sum(a * b)
    se[s]    <- sqrt(t(a) %*% V %*% a)
  }
  ## AAPC（全期，按线段覆盖的年区间长度加权）
  ## 连续铰链模型中每段斜率作用于相邻年份之间的区间：
  ## 段 s 覆盖 [bounds[s], bounds[s+1]]，即 diff(bounds) 个年度间隔；
  ## 权重 = diff(bounds) / (max(yr) - min(yr))，与 NCI 定义一致
  ## （权重与线段长度成比例），而非每段的观测点数。
  bounds <- c(min(yr), sort(knots), max(yr))
  w <- diff(bounds) / (max(yr) - min(yr))
  stopifnot(abs(sum(w) - 1) < 1e-12)
  aapc_log <- sum(w * slope)
  data.frame(
    segment = seq_len(nseg),
    years   = paste0(seg_lo, "-", seg_hi),
    apc     = 100 * (exp(slope) - 1),
    apc_lo  = 100 * (exp(slope - 1.96 * se) - 1),
    apc_hi  = 100 * (exp(slope + 1.96 * se) - 1),
    aapc    = 100 * (exp(aapc_log) - 1))
}

run_joinpoint <- function(d_asr) {
  d <- d_asr[d_asr$location == FOCUS_LOC & d_asr$sex == "Both" &
             d_asr$measure %in% c("Incidence", "Deaths"), ]
  d <- d[d$year %in% YEARS, ]
  out <- list()
  for (m in unique(d$measure)) {
    sub <- d[d$measure == m, ]
    sub <- sub[order(sub$year), ]
    sub <- sub[is.finite(sub$val) & sub$val > 0, ]
    best <- find_best_segments(sub$year, sub$val)
    sm   <- segment_summary(sub$year, sub$val, best)
    out[[m]] <- list(summary = sm, knots = best$knots,
                     fit_years = sub$year, fit_val = sub$val,
                     fit_pred = as.numeric(predict(best$fit)))
  }
  out
}

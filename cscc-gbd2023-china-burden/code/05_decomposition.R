## ============================================================
## 05_decomposition.R — 病例数变化三因子分解
## 方法：Das Gupta 三因子分解（六排列等权平均实现；对三因子乘积
##       形式与闭式解数学等价，见 reanalysis_v23.py 的 das_gupta）。
## 因子：① 人口规模增长 ② 人口老龄化（年龄结构）③ 流行病学变化（年龄别率）
## 公式：D_t = sum_a N_t * s_t,a * r_t,a
##       (N=总人口, s=年龄占比, r=年龄别人均事件率)
## 数据：人口一律取自直接下载的 GBD 2023 人口表（01_load_clean.R），
##       不使用 count/rate 反推（正文与 eMethods 2 已废弃该流程）。
## ============================================================

## Shapley 三因子分解（向量化：按年龄组求和）
## 端点记号 E[abc]: a/b/c=1 表示该因子取期末(2023)值，0 取期初(1990)值
## 因子顺序 = (人口规模 N, 年龄结构 s, 年龄别率 r)
shapley3 <- function(N1, N2, s1, s2, r1, r2) {
  y <- function(N, s, r) sum(N * s * r)
  E111 <- y(N2, s2, r2); E000 <- y(N1, s1, r1)
  E100 <- y(N2, s1, r1); E010 <- y(N1, s2, r1); E001 <- y(N1, s1, r2)
  E110 <- y(N2, s2, r1); E101 <- y(N2, s1, r2); E011 <- y(N1, s2, r2)
  ## 6 条排列 (N,s,r) 依序累加因子的边际贡献
  v_pop <- ((E100 - E000) + (E100 - E000) + (E110 - E010) +
            (E111 - E011) + (E101 - E001) + (E111 - E011)) / 6
  v_age <- ((E110 - E100) + (E111 - E101) + (E010 - E000) +
            (E010 - E000) + (E111 - E101) + (E011 - E001)) / 6
  v_epi <- ((E111 - E110) + (E101 - E100) + (E111 - E110) +
            (E011 - E010) + (E001 - E000) + (E001 - E000)) / 6
  c(population_growth = v_pop, population_aging = v_age, epidemiological_change = v_epi)
}

decomp_pair <- function(cnt1, cnt2) {
  ## cnt: data.frame(age, count, pop) 两期
  key <- function(x) x[match(AGE_GROUPS, x$age), ]
  c1 <- key(cnt1); c2 <- key(cnt2)
  ok <- !is.na(c1$pop) & !is.na(c2$pop) & c1$pop > 0 & c2$pop > 0
  N1 <- sum(c1$pop[ok]); N2 <- sum(c2$pop[ok])
  s1 <- c1$pop[ok] / N1; s2 <- c2$pop[ok] / N2
  r1 <- c1$count[ok] / c1$pop[ok]; r2 <- c2$count[ok] / c2$pop[ok]
  shapley3(N1, N2, s1, s2, r1, r2)
}

run_decomposition <- function(d_agesex, measure_use = c("Incidence", "Deaths")) {
  d <- d_agesex[d_agesex$location == FOCUS_LOC & d_agesex$sex == "Both" &
                d_agesex$measure %in% measure_use & d_agesex$year %in% YEARS, ]
  d <- d[is.finite(d$pop) & d$pop > 0, ]
  span <- seq(1990, 2023, by = 5)
  res <- list()
  for (m in unique(d$measure)) {
    dm <- d[d$measure == m, ]
    out <- data.frame()
    for (i in seq_along(span)) {
      y0 <- span[i]
      if (y0 == 2023) break
      y1 <- min(y0 + 5, 2023)
      c0 <- dm[dm$year == y0, ]; c1 <- dm[dm$year == y1, ]
      if (!nrow(c0) || !nrow(c1)) next
      e  <- decomp_pair(c0, c1)
      tot <- sum(c1$count) - sum(c0$count)
      out <- rbind(out, data.frame(measure = m, period = paste0(y0, "-", y1),
                    total_change = tot,
                    population_growth = e[1], population_aging = e[2],
                    epidemiological_change = e[3]))
    }
    res[[m]] <- out
  }
  res
}

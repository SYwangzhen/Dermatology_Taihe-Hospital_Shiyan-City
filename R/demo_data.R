## ============================================================
## demo_data.R — 合成演示数据（仅 --demo 模式使用）
## 目的：无真实下载时跑通全管线、预览 Fig1/Table1 版式。
## 量级参考 GBD 2021 东亚 SCC 水平设定，仅用于版式演示，
## 数值不可引用。真实数据回填后自动切换。
## ============================================================

## 年龄组（GBD 20 组）
AGE_GROUPS <- c("0-4","5-9","10-14","15-19","20-24","25-29","30-34",
                "35-39","40-44","45-49","50-54","55-59","60-64",
                "65-69","70-74","75-79","80-84","85-89","90-94","95+")

make_demo_asr <- function() {
  ## 年×measure×sex×location 的 ASR 序列（含 95% UI）
  yrs <- 1990:2023
  loc_scale <- c(China = 1, Global = 1.9, `High SDI` = 2.4)
  sex_mult  <- c(Male = 1.6, Female = 0.8, Both = 1.2)
  out <- list()
  k <- 1
  for (m in MEASURES) {
    ## 各指标基础水平（演示：每 10 万人）
    base <- switch(m,
      Incidence  = 2.0, Prevalence = 2.6, Deaths = 1.1, DALYs = 26)
    gr  <- switch(m, Incidence = 0.045, Prevalence = 0.050,
                  Deaths = 0.012, DALYs = 0.010)  ## 年增长率(对数尺度)
    for (loc in names(loc_scale)) for (sx in SEXES) {
      asr0 <- base * loc_scale[loc] * sex_mult[sx]
      logr <- log(asr0) + gr * (yrs - 1990) + 0.02 * sin((yrs - 1990) / 3) ## 轻微波浪便于演示分段
      asr  <- exp(logr)
      set.seed(2026 + k)
      ui_l <- runif(length(yrs), 0.78, 0.9)      # 演示带宽
      ui_u <- runif(length(yrs), 1.12, 1.28)
      out[[k]] <- data.frame(measure = m, location = loc, sex = sx,
                             year = yrs, val = asr,
                             lower = asr * ui_l, upper = asr * ui_u,
                             metric = "Rate")
      k <- k + 1
    }
  }
  do.call(rbind, out)
}

make_demo_agesex <- function() {
  ## age×sex×year 的例数(count)与年龄别粗率(rate, /10 万)；pop=年龄组人口(自洽)
  yrs <- 1990:2023
  out <- list(); k <- 1
  peak_scale <- c(Incidence = 40, Deaths = 9, Prevalence = 240, DALYs = 120) # /10万(峰值量级)
  for (m in names(peak_scale)) {
    for (loc in c("China", "Global", "High SDI")) for (sx in c("Male", "Female")) {
      pop_share <- dnorm(seq_along(AGE_GROUPS), mean = 12, sd = 5)
      pop_share <- pop_share / sum(pop_share)
      for (a in seq_along(AGE_GROUPS)) {
        age_w <- dnorm(a, mean = 18, sd = 3.2)          # 高峰在 85-89
        age_w <- age_w / max(age_w)
        base_pop <- if (loc == "China") 5.5e8 else 3.6e9  # 单性别人口量级
        for (i in seq_along(yrs)) {
          yr <- yrs[i]
          agepop <- base_pop * pop_share[a] *
                    (1 + 0.006 * (yr - 1990)) * (if (sx == "Male") 1.05 else 1)
          rate  <- peak_scale[m] * (0.6 + 0.4 * age_w) *
                   exp(0.028 * (yr - 1990)) * (if (sx == "Male") 1.4 else 1)
          cnt   <- agepop * rate / 1e5
          out[[k]] <- data.frame(measure = m, location = loc, sex = sx,
                                 age = AGE_GROUPS[a], year = yr,
                                 count = cnt, rate = rate,
                                 lower = cnt * 0.75, upper = cnt * 1.3)
          k <- k + 1
        }
      }
    }
  }
  do.call(rbind, out)
}

gen_demo_data <- function() {
  asr  <- make_demo_asr()
  ages <- make_demo_agesex()
  ## 关键：demo 数据写独立 _DEMO 文件，绝不覆盖 data/raw/ 真实下载
  f_asr  <- sub("\\.csv$", "_DEMO.csv", FILE_ASR)
  f_ages <- sub("\\.csv$", "_DEMO.csv", FILE_AGESEX)
  write.csv(asr,  f_asr,  row.names = FALSE)
  write.csv(ages, f_ages, row.names = FALSE)
  cat(sprintf("[demo] synthetic data written (DEMO files, real data untouched):\n  %s (%d rows)\n  %s (%d rows)\n",
              f_asr, nrow(asr), f_ages, nrow(ages)))
}

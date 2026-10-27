## ============================================================
## 04_apc.R — 年龄-时期-队列（APC）视角分析
## 说明：GBD 论文中"APC"常有两种用法：① 严格 APC 统计模型
##       （需 NCI Age-Period-Cohort 工具或 R 包 BAPC/apc，脚本见注释）；
##       ② 描述性年龄×时期×队列分层（本文采用，稳健且无识别争议）。
## 产出：age×period 率矩阵；出生队列发病率指数（以参照队列=1）；
##       供 Fig2 绘制的 cohort 曲线数据。
## ============================================================

age_mid <- function(ag) {
  ## "0-4" -> 2, "95+" -> 97
  ifelse(ag == "95+", 97,
         (as.numeric(sub("-.*", "", ag)) + as.numeric(sub(".*-", "", ag))) / 2)
}

run_apc <- function(d_agesex) {
  d <- d_agesex[d_agesex$location == FOCUS_LOC & d_agesex$sex == "Both" &
                d_agesex$measure == "Incidence", ]
  d$age_mid <- age_mid(d$age)
  d$cohort  <- d$year - d$age_mid   ## 出生年份（约）

  ## 1) age × period 矩阵（age-specific rate / 10 万）
  ap_mat <- tapply(d$rate, list(d$age, d$year), sum)
  ## 2) 队列视角：以 5 年队列分组
  d$cohort5 <- floor(d$cohort / 5) * 5
  d$cohort5[is.na(d$cohort5)] <- NA
  cq <- d[!is.na(d$cohort5) & d$cohort5 >= 1900 & d$cohort5 <= 2005, ]
  ## 队列指数：仅保留 55-79 岁窗口在 1990-2023 内完全可观测的队列
  ## （出生 1935-1944 年 ⇔ cohort5 桶 1935 与 1940；其余桶部分/全部落在数据期外，
  ##  直接比较会产生年龄截断偏倚——见 07 稿件 Results/审稿回应 N2）
  cq_mid <- cq[cq$age_mid >= 55 & cq$age_mid <= 79, ]
  qsum <- aggregate(rate ~ cohort5, data = cq_mid, FUN = mean)
  qsum <- qsum[qsum$cohort5 >= 1935 & qsum$cohort5 <= 1940, ]
  ref <- "1935"
  ref_rate <- qsum$rate[qsum$cohort5 == as.numeric(ref)]
  ref_rate <- if (length(ref_rate)) ref_rate else mean(qsum$rate)
  qsum$index <- qsum$rate / ref_rate
  qsum <- qsum[order(qsum$cohort5), ]
  ## 3) cohort 曲线数据（每个队列 45-89 岁轨迹，用于 Fig2）
  fig <- cq[cq$age_mid >= 40 & cq$age_mid <= 89, c("cohort5", "age_mid", "rate")]
  fig <- aggregate(rate ~ cohort5 + age_mid, data = fig, FUN = mean)
  list(age_period = ap_mat, cohort = qsum, fig = fig,
       note = "descriptive APC layering; strict APC model: use NCI APC tool or R package BAPC")
}

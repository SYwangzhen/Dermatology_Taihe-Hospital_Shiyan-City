## ============================================================
## 06_figures.R — 出版级图输出（300 dpi TIFF/PNG + PDF）
## Figure 1：中国梅毒四指标 ASR 1990-2023 双轴趋势（95% UI 带状）
##           A：ASIR 与 ASDR    B：ASPR 与 DALY 率
##           浅灰带 = 2011-2016 模型估计瞬变（非真实疾病加速）
## Figure 2：发病/死亡例数变化的三因子分解（5 年跨度堆叠）
## Research Letter 备用：RL_Fig1 四宫格
## 注：v2.0 起不再叠加 joinpoint 断点竖线——分段模型仅贴合 2011-16
##     瞬变，正文不作相变解读（结果见 eTable 1）。
## ============================================================

save_pub <- function(path_png, w_mm, h_mm, res = 300) {
  png(path_png, width = w_mm / 25.4, height = h_mm / 25.4,
      units = "in", res = res, type = "cairo")
}
save_pdf <- function(path_pdf, w_mm, h_mm) {
  pdf(path_pdf, width = w_mm / 25.4, height = h_mm / 25.4)
}

add_watermark <- function(txt = WATERMARK) {
  if (nzchar(txt)) mtext(txt, side = 1, line = -1.2, cex = 0.62,
                         col = grDevices::rgb(0.7, 0.1, 0.1, 0.55), adj = 1)
}

## —— 取 China×sex=Both 的四指标 ASR 序列 ----
focus_series <- function(d_asr, measure_use = MEASURES, sex_use = "Both") {
  d <- d_asr[d_asr$location == FOCUS_LOC & d_asr$sex == sex_use &
             d_asr$measure %in% measure_use & d_asr$year %in% YEARS, ]
  d[order(d$measure, d$year), ]
}

## 双轴折线（带状=95% UI；shade=高亮年份区间，如 c(2011,2016)）
twoline <- function(d1, d2, col1, col2, main = "", ylab1 = "", ylab2 = "",
                    ylim1 = NULL, ylim2 = NULL, shade = NULL) {
  r1 <- range(d1$val, if (!is.null(ylim1)) ylim1 else NULL)
  r2 <- range(d2$val, if (!is.null(ylim2)) ylim2 else NULL)
  plot(d1$year, d1$val, type = "n", xlab = "Year", ylab = "", las = 1,
       main = main, xlim = range(YEARS), ylim = r1 * c(0.92, 1.08))
  ## 浅灰带（2011-2016 瞬变），置于曲线之下
  if (!is.null(shade)) {
    u <- par("usr")
    rect(shade[1], u[3], shade[2], u[4],
         col = grDevices::rgb(0.4, 0.4, 0.4, 0.07), border = NA)
  }
  mtext(ylab1, side = 2, line = 2.6, cex = 0.8)
  polygon(c(d1$year, rev(d1$year)), c(d1$lower, rev(d1$upper)),
          col = grDevices::adjustcolor(col1, 0.15), border = NA)
  lines(d1$year, d1$val, col = col1, lwd = 2)
  par(new = TRUE)
  plot(d2$year, d2$val, type = "n", xaxt = "n", yaxt = "n", xlab = "",
       ylab = "", ylim = r2 * c(0.92, 1.08))
  axis(4, las = 1)
  mtext(ylab2, side = 4, line = 2.6, cex = 0.8)
  polygon(c(d2$year, rev(d2$year)), c(d2$lower, rev(d2$upper)),
          col = grDevices::adjustcolor(col2, 0.15), border = NA)
  lines(d2$year, d2$val, col = col2, lwd = 2, lty = 2)
  par(new = FALSE)
}

fig1_main <- function(d_asr, out_prefix = "Figure1") {
  S <- focus_series(d_asr)
  inc <- S[S$measure == "Incidence", ];  prev <- S[S$measure == "Prevalence", ]
  dea <- S[S$measure == "Deaths", ];     dal <- S[S$measure == "DALYs", ]
  mm <- 180
  save_pub(file.path(OUT_FIG, paste0(out_prefix, TAG, ".png")), mm, 0.62 * mm)
  par(mar = c(4, 4.6, 2.4, 4.6), mfrow = c(1, 2), cex.axis = 0.85, cex.lab = 0.9)
  twoline(inc, dea, "#C0392B", "#2471A3",
          main = "A  ASIR & ASDR (China)",
          ylab1 = "ASIR per 100 000", ylab2 = "ASDR per 100 000",
          shade = NULL)
  twoline(prev, dal, "#1E8449", "#7D3C98",
          main = "B  ASPR & DALY rate (China)",
          ylab1 = "ASPR per 100 000", ylab2 = "DALY rate per 100 000",
          shade = NULL)
  add_watermark()
  dev.off()
  save_pdf(file.path(OUT_FIG, paste0(out_prefix, TAG, ".pdf")), mm, 0.62 * mm)
  par(mar = c(4, 4.6, 2.4, 4.6), mfrow = c(1, 2), cex.axis = 0.85, cex.lab = 0.9)
  twoline(inc, dea, "#C0392B", "#2471A3", main = "A  ASIR & ASDR",
          ylab1 = "ASIR", ylab2 = "ASDR", shade = NULL)
  twoline(prev, dal, "#1E8449", "#7D3C98", main = "B  ASPR & DALY rate",
          ylab1 = "ASPR", ylab2 = "DALY rate", shade = NULL)
  add_watermark()
  dev.off()
  cat("[fig] Figure1 written (PNG+PDF)\n")
}

fig2_decomp <- function(decomp, out_prefix = "Figure2") {
  d1 <- decomp[["Incidence"]]; d2 <- decomp[["Deaths"]]
  x <- d1$period
  mat <- rbind(d1$population_growth, d1$population_aging, d1$epidemiological_change)
  mat2 <- rbind(d2$population_growth, d2$population_aging, d2$epidemiological_change)
  mm <- 180
  save_pub(file.path(OUT_FIG, paste0(out_prefix, TAG, ".png")), mm, 0.52 * mm)
  par(mfrow = c(1, 2), mar = c(6.6, 4.4, 2.4, 1.2), cex.axis = 0.8, cex.lab = 0.85)
  barplot(mat, names.arg = x, col = c("#2E86C1", "#F4D03F", "#CB4335"), border = NA,
          las = 2, ylab = "Change in cases", main = "A  Incident cases")
  abline(h = 0)
  barplot(mat2, names.arg = x, col = c("#2E86C1", "#F4D03F", "#CB4335"), border = NA,
          las = 2, ylab = "Change in deaths", main = "B  Deaths")
  abline(h = 0)
  ## 图例移至整图底部，单行居中（不占面板内部空间）
  legend(x = grconvertX(0.5, "ndc", "user"),
         y = grconvertY(0.030, "ndc", "user"),
         legend = c("Population growth", "Population aging",
                    "Epidemiological change"),
         fill = c("#2E86C1", "#F4D03F", "#CB4335"),
         cex = 0.72, bty = "n", ncol = 3, xjust = 0.5, yjust = 0.5, xpd = NA)
  add_watermark(); dev.off()
  save_pdf(file.path(OUT_FIG, paste0(out_prefix, TAG, ".pdf")), mm, 0.52 * mm)
  par(mfrow = c(1, 2), mar = c(6.6, 4.4, 2.4, 1.2), cex.axis = 0.8)
  barplot(mat, names.arg = x, col = c("#2E86C1", "#F4D03F", "#CB4335"), border = NA,
          las = 2, main = "A", ylab = "Change in cases"); abline(h = 0)
  barplot(mat2, names.arg = x, col = c("#2E86C1", "#F4D03F", "#CB4335"), border = NA,
          las = 2, main = "B", ylab = "Change in deaths"); abline(h = 0)
  legend(x = grconvertX(0.5, "ndc", "user"),
         y = grconvertY(0.030, "ndc", "user"),
         legend = c("Population growth", "Population aging",
                    "Epidemiological change"),
         fill = c("#2E86C1", "#F4D03F", "#CB4335"),
         cex = 0.72, bty = "n", ncol = 3, xjust = 0.5, yjust = 0.5, xpd = NA)
  add_watermark(); dev.off()
  cat("[fig] Figure2 written\n")
}

## —— Research Letter 备用：单部件四宫格 ——
rl_fig1 <- function(d_asr, out_prefix = "RL_Fig1") {
  S <- focus_series(d_asr)
  mm <- 180
  save_pub(file.path(OUT_FIG, paste0(out_prefix, TAG, ".png")), mm, mm)
  par(mfrow = c(2, 2), mar = c(3.6, 4, 2.4, 1), cex.axis = 0.75)
  for (m in MEASURES) {
    s <- S[S$measure == m, ]
    plot(s$year, s$val, type = "l", lwd = 2, col = "#C0392B", las = 1,
         ylab = paste0(MEAS_LABEL[m], " per 100 000"), xlab = "Year",
         main = MEAS_LABEL[m])
    polygon(c(s$year, rev(s$year)), c(s$lower, rev(s$upper)),
            col = grDevices::adjustcolor("#C0392B", 0.12), border = NA)
  }
  add_watermark(); dev.off()
  cat("[fig] RL_Fig1 written (Research Letter backup)\n")
}

render_all_figures <- function(d_asr, jp, apc, decomp) {
  fig1_main(d_asr)
  fig2_decomp(decomp)
  rl_fig1(d_asr)
}

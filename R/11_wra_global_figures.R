## ============================================================
## 11_wra_global_figures.R — A 档扩展（真实数据，无需新下载）
## Figure6：WRA(15-49 岁女性) 发病率/DALY 率趋势 中国 vs 全球
## Figure7：2023 绝对数 vs 率 双面板对比（中/全球/高SDI）
## Figure8：中国 2023 发病年龄-性别金字塔
## Table3 ：性别分层 EAPC（ASIR/ASPR/ASMR/DALY 率 × 中/全球/高SDI）
## Table4 ：WRA 汇总（1990/2023 率 + EAPC）
## ============================================================
source("00_config.R")
DEMO_MODE <- FALSE
WATERMARK <- ""
TAG       <- ""
source("01_load_clean.R")
source("06_figures.R")   # save_pub / save_pdf / add_watermark

dat <- load_data()
asr <- dat$asr
agx <- dat$agesex

out_f <- OUT_FIG
out_t <- OUT_TAB

## WRA 年龄组（15-49 岁，GBD 5 岁分组 7 组）
WRA_AGES <- c("15-19","20-24","25-29","30-34","35-39","40-44","45-49")

## —— EAPC：ln(rate) 对 year 的对数线性回归 ——
## 95% CI 用 confint()（t 分布），与 02_eapc_trend.R calc_eapc 口径统一（2026-10-09 复审修订）
eapc_of <- function(yr, v) {
  ok <- is.finite(v) & v > 0
  if (sum(ok) < 5) return(c(EAPC = NA, lo = NA, hi = NA))
  fit <- lm(log(v[ok]) ~ yr[ok])
  b   <- unname(coef(fit)[2])
  ci  <- unname(confint(fit)[2, ])
  c(EAPC = 100 * (exp(b) - 1),
    lo   = 100 * (exp(ci[1]) - 1),
    hi   = 100 * (exp(ci[2]) - 1))
}

## ============ WRA 序列（Female, 15-49 岁合计率 = sum(count)/sum(pop)*1e5） ============
wra_series <- function(ms) {
  d <- agx[agx$sex == "Female" & agx$age %in% WRA_AGES &
           agx$measure == ms & agx$location %in% c("China", "Global"), ]
  agg <- aggregate(cbind(count, pop) ~ location + year, data = d, FUN = sum)
  agg$rate <- ifelse(agg$pop > 0, agg$count / agg$pop * 1e5, NA)
  agg[order(agg$location, agg$year), ]
}
wra_inc <- wra_series("Incidence")
wra_dal <- wra_series("DALYs")

## ---------- Figure6：WRA 专项 ----------
f6 <- function() {
  mm <- 180
  cols <- c(China = "#C0392B", Global = "#1F618D")
  save_pub(file.path(out_f, "Figure6.png"), mm, 0.60 * mm)
  par(mfrow = c(1, 2), mar = c(4, 4.4, 2.4, 1.0), cex.axis = 0.85, cex.lab = 0.9)
  for (k in 1:2) {
    d <- if (k == 1) wra_inc else wra_dal
    ylab <- if (k == 1) "Incidence per 100 000 women" else "DALY rate per 100 000 women"
    main <- if (k == 1) "A  WRA incidence (ages 15-49)" else "B  WRA DALY rate"
    plot(range(YEARS), range(d$rate, na.rm = TRUE) * c(0, 1.08), type = "n",
         xlab = "Year", ylab = ylab, las = 1, main = main)
    for (lc in c("China", "Global")) {
      dd <- d[d$location == lc & is.finite(d$rate), ]
      dd <- dd[order(dd$year), ]
      lines(dd$year, dd$rate, col = cols[[lc]], lwd = 2.2)
    }
    if (k == 1) legend("topleft", legend = c("China", "Global"), col = cols,
                       lwd = 2.2, cex = 0.8, bty = "n")
  }
  add_watermark(); dev.off()
  save_pdf(file.path(out_f, "Figure6.pdf"), mm, 0.60 * mm)
  par(mfrow = c(1, 2), mar = c(4, 4.4, 2.4, 1.0), cex.axis = 0.85, cex.lab = 0.9)
  for (k in 1:2) {
    d <- if (k == 1) wra_inc else wra_dal
    ylab <- if (k == 1) "Incidence per 100 000 women" else "DALY rate per 100 000 women"
    plot(range(YEARS), range(d$rate, na.rm = TRUE) * c(0, 1.08), type = "n",
         xlab = "Year", ylab = ylab, las = 1)
    for (lc in c("China", "Global")) {
      dd <- d[d$location == lc & is.finite(d$rate), ]
      dd <- dd[order(dd$year), ]
      lines(dd$year, dd$rate, col = cols[[lc]], lwd = 2.2)
    }
  }
  add_watermark(); dev.off()
  cat("[fig] Figure6 written\n")
}

## ---------- Figure7：2023 绝对数 vs 率 双面板 ----------
f7 <- function() {
  locs <- c("China", "Global", "High SDI")
  cols <- c(China = "#C0392B", Global = "#1F618D", "High SDI" = "#229954")
  pick <- function(ms, metric) {
    if (metric == "count") {
      d <- agx[agx$location %in% locs & agx$year == 2023 & agx$measure == ms &
               agx$sex == "Both" & agx$age %in% AGE_GROUPS, ]
      tapply(d$count, d$location, sum)
    } else {
      d <- asr[asr$location %in% locs & asr$year == 2023 & asr$measure == ms &
               asr$sex == "Both", ]
      setNames(d$val, d$location)
    }
  }
  inc_n  <- pick("Incidence", "count")
  inc_r  <- pick("Incidence", "rate")
  prev_n <- pick("Prevalence", "count")
  prev_r <- pick("Prevalence", "rate")
  mm <- 180
  save_pub(file.path(out_f, "Figure7.png"), mm, 0.72 * mm)
  par(mfrow = c(2, 2), mar = c(5.5, 4.8, 2.4, 1.0), cex.axis = 0.85, cex.lab = 0.9)
  bar_chart <- function(v, ylab, main, sci = FALSE) {
    v <- v[locs]
    if (sci) {
      bp <- barplot(v, col = cols[locs], border = NA, las = 1,
                    ylab = ylab, main = main, ylim = c(0, max(v) * 1.18))
      text(bp, v, labels = sprintf("%.1f", v), pos = 3, cex = 0.75, xpd = NA)
    } else {
      vm <- v / 1e6
      bp <- barplot(vm, col = cols[locs], border = NA, las = 1,
                    ylab = ylab, main = main, ylim = c(0, max(vm) * 1.18))
      text(bp, vm, labels = sprintf("%.1fM", vm), pos = 3, cex = 0.75, xpd = NA)
    }
    abline(h = 0)
  }
  bar_chart(inc_n,  "Incident cases, millions (2023)", "A  Incident cases",      sci = FALSE)
  bar_chart(inc_r,  "ASIR per 100 000 (2023)",         "B  ASIR",                sci = TRUE)
  bar_chart(prev_n, "Prevalent cases, millions (2023)","C  Prevalent cases",     sci = FALSE)
  bar_chart(prev_r, "ASPR per 100 000 (2023)",         "D  ASPR",                sci = TRUE)
  add_watermark(); dev.off()
  save_pdf(file.path(out_f, "Figure7.pdf"), mm, 0.72 * mm)
  par(mfrow = c(2, 2), mar = c(5.5, 4.8, 2.4, 1.0), cex.axis = 0.85, cex.lab = 0.9)
  bar_chart(inc_n,  "Incident cases, millions (2023)", "A", sci = FALSE)
  bar_chart(inc_r,  "ASIR per 100 000",                "B", sci = TRUE)
  bar_chart(prev_n, "Prevalent cases, millions (2023)","C", sci = FALSE)
  bar_chart(prev_r, "ASPR per 100 000",                "D", sci = TRUE)
  add_watermark(); dev.off()
  cat("[fig] Figure7 written\n")
}

## ---------- Figure8：年龄-性别金字塔（中国 2023 发病率） ----------
f8 <- function() {
  ACUTE <- AGE_GROUPS[1:13]   # 0-4 .. 60-64（65+ 发病为零，不展示全零行）
  d23 <- agx[agx$location == "China" & agx$year == 2023 &
             agx$measure == "Incidence" & agx$sex %in% c("Male", "Female") &
             agx$age %in% ACUTE, ]
  r_m <- tapply(d23$rate[d23$sex == "Male"],   factor(d23$age[d23$sex == "Male"],   ACUTE), sum)
  r_f <- tapply(d23$rate[d23$sex == "Female"], factor(d23$age[d23$sex == "Female"], ACUTE), sum)
  r_m[is.na(r_m)] <- 0; r_f[is.na(r_f)] <- 0
  mm <- 140
  lim <- max(c(r_m, r_f)) * 1.15
  tk <- as.vector(pretty(c(0, lim)))
  tk <- tk[tk <= lim & tk >= 0]
  draw_pyramid <- function() {
    par(mar = c(4.5, 3.6, 2.4, 1.2), cex.axis = 0.75, cex.lab = 0.9)
    bp <- barplot(-r_m, horiz = TRUE, las = 1, xlim = c(-lim, lim),
                  col = "#1F618D", border = NA, axes = FALSE,
                  names.arg = rep("", length(r_m)),
                  main = "Age-sex pyramid of syphilis incidence, China 2023")
    barplot(r_f, horiz = TRUE, add = TRUE, col = "#C0392B", border = NA,
            axes = FALSE, names.arg = rep("", length(r_f)))
    axis(1, at = c(-rev(tk), tk), labels = c(rev(tk), tk), las = 1)
    age_lab <- ifelse(seq_along(ACUTE) %% 2 == 1, AGE_GROUPS, "")
    age_lab[length(ACUTE)] <- "60-64"
    axis(2, at = bp, labels = age_lab, las = 1, tick = FALSE, cex.axis = 0.68)
    abline(v = 0, col = "grey40")
    text(-lim * 0.62, length(AGE_GROUPS) - 1.5, "Male", col = "#1F618D", cex = 1.0, font = 2)
    text( lim * 0.62, length(AGE_GROUPS) - 1.5, "Female", col = "#C0392B", cex = 1.0, font = 2)
    mtext("Incidence per 100 000", side = 1, line = 2.9, cex = 0.85)
  }
  save_pub(file.path(out_f, "Figure8.png"), mm, 1.00 * mm)
  draw_pyramid()
  add_watermark(); dev.off()
  save_pdf(file.path(out_f, "Figure8.pdf"), mm, 1.00 * mm)
  draw_pyramid()
  add_watermark(); dev.off()
  cat("[fig] Figure8 written\n")
}

## ---------- Table3：性别分层 EAPC ----------
t3 <- function() {
  locs <- c("China", "Global", "High SDI")
  rows <- list()
  i <- 0
  for (lc in locs) for (sx in c("Male", "Female", "Both")) for (ms in MEASURES) {
    d <- asr[asr$location == lc & asr$sex == sx & asr$measure == ms &
             asr$year %in% YEARS, ]
    d <- d[order(d$year), ]
    e <- eapc_of(d$year, d$val)
    v23 <- as.numeric(d$val[d$year == 2023])
    v23 <- if (length(v23)) v23[1] else NA_real_
    i <- i + 1
    rows[[i]] <- data.frame(location = lc, sex = sx, measure = ms,
                            rate_2023 = round(v23, 2),
                            EAPC = round(e["EAPC"], 2),
                            EAPC_95lo = round(e["lo"], 2),
                            EAPC_95hi = round(e["hi"], 2))
  }
  tab <- do.call(rbind, rows)
  tab$measure <- MEAS_LABEL[tab$measure]
  write.csv(tab, file.path(out_t, "Table3_sex_eapc.csv"), row.names = FALSE)
  cat("[tab] Table3 written:", file.path(out_t, "Table3_sex_eapc.csv"), "\n")
  print(tab, row.names = FALSE)
}

## ---------- Table4：WRA 汇总 ----------
t4 <- function() {
  rows <- list(); i <- 0
  for (nm in c("Incidence", "DALYs")) {
    d <- if (nm == "Incidence") wra_inc else wra_dal
    for (lc in c("China", "Global")) {
      dd <- d[d$location == lc & is.finite(d$rate), ]
      dd <- dd[order(dd$year), ]
      e  <- eapc_of(dd$year, dd$rate)
      i <- i + 1
      rows[[i]] <- data.frame(
        indicator = paste0("WRA ", nm, " rate (15-49, /100000)"),
        location  = lc,
        y1990 = round(dd$rate[dd$year == 1990], 2),
        y2010 = round(dd$rate[dd$year == 2010], 2),
        y2023 = round(dd$rate[dd$year == 2023], 2),
        cases_2023 = round(dd$count[dd$year == 2023]),
        EAPC = round(e["EAPC"], 2),
        EAPC_95lo = round(e["lo"], 2), EAPC_95hi = round(e["hi"], 2))
    }
  }
  tab <- do.call(rbind, rows)
  write.csv(tab, file.path(out_t, "Table4_WRA.csv"), row.names = FALSE)
  cat("[tab] Table4 written:", file.path(out_t, "Table4_WRA.csv"), "\n")
  print(tab, row.names = FALSE)
}

f6(); f7(); f8(); t3(); t4()
cat("\n[A-tier] extra figures/tables done.\n")

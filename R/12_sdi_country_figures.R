## ============================================================
## 12_sdi_country_figures.R — B/C 档（国家级 + SDI）
## Figure9 ：SDI-ASIR 国家散点（204 国，按 SDI 分位着色，中国标红）
## Figure11：SDI 五分位 vs 中国 ASIR 趋势（1990-2023）
## Table5  ：2023 ASIR Top10 国家 + 中国排名
## ============================================================
source("00_config.R")
DEMO_MODE <- FALSE
WATERMARK <- ""
TAG       <- ""
source("01_load_clean.R")
source("06_figures.R")

dat <- load_data()
asr <- dat$asr
out_f <- OUT_FIG; out_t <- OUT_TAB

## ---- 读 D（国家级 2023）----
dc <- read.csv(file.path(BASE, "data", "raw", "D_countries_2023.csv"), check.names = FALSE)
dc <- cn_en_col(dc, c("measure", "measure_name"))
d_i <- dc[dc$measure_name == "Incidence" & dc$metric_name == "Rate",
          c("location_id", "location_name", "val")]
names(d_i)[3] <- "ASIR"
d_y <- dc[dc$measure_name == "DALYs" & dc$metric_name == "Rate",
          c("location_id", "val")]
names(d_y)[2] <- "ASDALY"

## ---- 读 E（SDI，全地点 1950-2023）----
se <- read.csv(file.path(BASE, "data", "raw", "E_sdi_countries.csv"), check.names = FALSE)
s23 <- aggregate(mean_value ~ location_id, data = se[se$year_id == 2023, ], FUN = mean)
names(s23)[2] <- "SDI"

## ---- 按 location_id 精确合并（SDI 文件含次国家级，名字有重名，ID 唯一）----
mer <- merge(d_i, d_y, by = "location_id", all.x = TRUE)
mer <- merge(mer, s23, by = "location_id", all.x = TRUE)
cat("[merge] countries:", nrow(mer), "; with SDI:", sum(!is.na(mer$SDI)), "\n")
miss <- mer$location_name[is.na(mer$SDI)]
if (length(miss)) cat("[merge] no-SDI countries:", paste(miss, collapse = "; "), "\n")

## 剔除聚合行（若误入）：人口/全球级别不在 D 中，204 国应为纯国家
## ---- SDI 分位着色 ----
cuts <- c(0.5316, 0.6305, 0.6767, 0.7188)
quint_lab <- c("Low SDI", "Low-middle SDI", "Middle SDI", "High-middle SDI", "High SDI")
mer$quint <- quint_lab[findInterval(mer$SDI, cuts) + 1]
mer$quint[is.na(mer$SDI)] <- NA

## ============ Figure9：SDI-ASIR 散点 ============
f9 <- function() {
  qcols <- c("Low SDI" = "#67001F", "Low-middle SDI" = "#C0392B",
             "Middle SDI" = "#E67E22", "High-middle SDI" = "#7FB3D5",
             "High SDI" = "#1F618D")
  d <- mer[!is.na(mer$SDI), ]
  mm <- 180
  save_pub(file.path(out_f, "Figure9.png"), mm, 0.72 * mm)
  par(mar = c(4.6, 4.6, 2.4, 1.2), cex.axis = 0.85, cex.lab = 0.95)
  plot(d$SDI, d$ASIR, col = qcols[d$quint], pch = 19, cex = 0.62,
       xlab = "Sociodemographic Index (SDI), 2023",
       ylab = "ASIR per 100 000", las = 1,
       main = "Syphilis ASIR vs SDI across countries, 2023",
       xlim = c(0.2, 1.0))
  ## 全球拟合线（loess）
  fit <- loess(ASIR ~ SDI, data = d, span = 0.7)
  sdx <- seq(min(d$SDI), max(d$SDI), length.out = 200)
  lines(sdx, predict(fit, sdx), col = "grey35", lwd = 1.6, lty = 2)
  ## 中国标红加粗
  ch <- mer[mer$location_name == "China", ]
  points(ch$SDI, ch$ASIR, col = "black", pch = 21, cex = 1.7, lwd = 2.4, bg = "#1F618D")  # High SDI fill
  text(ch$SDI, ch$ASIR, labels = "China", pos = 2, cex = 0.9, font = 2, offset = 0.5)
  legend("topright", legend = quint_lab, col = qcols, pch = 19,
         cex = 0.68, bty = "n", pt.cex = 0.9)
  legend("topleft", legend = "Global loess fit", col = "grey35", lty = 2,
         lwd = 1.6, cex = 0.68, bty = "n")
  add_watermark(); dev.off()
  save_pdf(file.path(out_f, "Figure9.pdf"), mm, 0.72 * mm)
  par(mar = c(4.6, 4.6, 2.4, 1.2), cex.axis = 0.85, cex.lab = 0.95)
  plot(d$SDI, d$ASIR, col = qcols[d$quint], pch = 19, cex = 0.62,
       xlab = "Sociodemographic Index (SDI), 2023",
       ylab = "ASIR per 100 000", las = 1, xlim = c(0.2, 1.0))
  lines(sdx, predict(fit, sdx), col = "grey35", lwd = 1.6, lty = 2)
  points(ch$SDI, ch$ASIR, col = "black", pch = 21, cex = 1.7, lwd = 2.4, bg = "#1F618D")  # High SDI fill
  text(ch$SDI, ch$ASIR, labels = "China", pos = 2, cex = 0.9, font = 2, offset = 0.5)
  add_watermark(); dev.off()
  cat("[fig] Figure9 written\n")
}

## ============ Figure11：SDI 五分位 vs 中国 ASIR 趋势 ============
f11 <- function() {
  cq <- read.csv(file.path(BASE, "data", "raw", "C_sdi_regions_1990_2023.csv"), check.names = FALSE)
  cq <- cn_en_col(cq, c("location", "location_name"))
  qq <- cq[cq$measure_name == "Incidence" & cq$metric_name == "Rate" &
           cq$sex_name == "Both" & cq$age_name == "Age-standardized" &
           grepl("SDI", cq$location_name), c("location_name", "year", "val")]
  ## 中国序列（来自 A 文件）
  ch <- asr[asr$location == "China" & asr$measure == "Incidence" &
            asr$sex == "Both" & asr$year %in% YEARS, c("year", "val")]
  cols <- c("Low SDI" = "#67001F", "Low-middle SDI" = "#C0392B",
            "Middle SDI" = "#E67E22", "High-middle SDI" = "#7FB3D5",
            "High SDI" = "#1F618D", "China" = "#000000")
  mm <- 180
  save_pub(file.path(out_f, "Figure11.png"), mm, 0.60 * mm)
  par(mar = c(4.4, 4.6, 2.4, 1.0), cex.axis = 0.85, cex.lab = 0.9)
  allv <- c(qq$val, ch$val)
  plot(range(YEARS), range(allv) * c(0.9, 1.06), type = "n",
       xlab = "Year", ylab = "ASIR per 100 000", las = 1,
       main = "ASIR trends: China vs SDI quintiles")
  for (lc in names(cols)) {
    d <- if (lc == "China") ch else qq[qq$location_name == lc, ]
    d <- d[order(d$year), ]
    lw <- if (lc == "China") 2.8 else 2.0
    lines(d$year, d$val, col = cols[[lc]], lwd = lw,
          lty = if (lc == "China") 1 else 1)
  }
  legend("topleft", legend = c("China", quint_lab),
         col = c(cols[["China"]], cols[quint_lab]),
         lwd = c(2.8, rep(2.0, 5)), cex = 0.68, bty = "n", ncol = 2)
  add_watermark(); dev.off()
  save_pdf(file.path(out_f, "Figure11.pdf"), mm, 0.60 * mm)
  par(mar = c(4.4, 4.6, 2.4, 1.0), cex.axis = 0.85, cex.lab = 0.9)
  plot(range(YEARS), range(allv) * c(0.9, 1.06), type = "n",
       xlab = "Year", ylab = "ASIR per 100 000", las = 1)
  for (lc in names(cols)) {
    d <- if (lc == "China") ch else qq[qq$location_name == lc, ]
    d <- d[order(d$year), ]
    lines(d$year, d$val, col = cols[[lc]], lwd = if (lc == "China") 2.8 else 2.0)
  }
  add_watermark(); dev.off()
  cat("[fig] Figure11 written\n")
}

## ============ Table5：Top10 国家 ASIR 2023 + 中国排名 ============
t5 <- function() {
  d <- mer[!is.na(mer$ASIR), ]
  d <- d[order(-d$ASIR), ]
  d$rank <- seq_len(nrow(d))
  top10 <- head(d[, c("rank", "location_name", "ASIR", "ASDALY", "SDI", "quint")], 10)
  ch_rank <- d$rank[d$location_name == "China"]
  ch_row <- d[d$location_name == "China", c("rank", "location_name", "ASIR", "ASDALY", "SDI", "quint")]
  tab <- rbind(top10, `...` = c(NA, "", NA, NA, NA, ""), ch_row)
  names(tab) <- c("Rank", "Country", "ASIR_2023", "ASDALY_2023", "SDI_2023", "SDI_quintile")
  tab$ASIR_2023 <- round(as.numeric(tab$ASIR_2023), 1)
  tab$ASDALY_2023 <- round(as.numeric(tab$ASDALY_2023), 1)
  tab$SDI_2023 <- round(as.numeric(tab$SDI_2023), 3)
  write.csv(tab, file.path(out_t, "Table5_country_ranking_2023.csv"), row.names = FALSE)
  cat("[tab] Table5 written. China rank:", ch_rank, "/", nrow(d), "\n")
  print(tab, row.names = FALSE)
}

f9(); f11(); t5()
cat("\n[B/C-tier] figures done (Figure10 map pending 3 regions).\n")

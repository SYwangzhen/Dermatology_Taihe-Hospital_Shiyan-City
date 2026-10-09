## ============================================================
## 14_region_ranking.R — 21 GBD 地区横向对比
## Figure10：2023 ASIR 地区排序横条图（East Asia 标红，Global 虚线参照）
## Table6 ：各地区 2023 ASIR/ASDALY + 1990-2023 EAPC
## 数据：C_sdi_regions_1990_2023.csv + C2_missing3regions_1990_2023.csv
##       （High-income North America 若未到货则先出 20 地区版，到货后重跑即自动升级）
## ============================================================
source("00_config.R")
DEMO_MODE <- FALSE
WATERMARK <- ""
source("01_load_clean.R")
source("06_figures.R")

out_f <- OUT_FIG; out_t <- OUT_TAB
REGIONS_21 <- c("High-income Asia Pacific", "Central Asia", "East Asia",
                "Oceania", "Southeast Asia", "South Asia",
                "Central Europe", "Eastern Europe", "Western Europe",
                "Australasia", "Southern Latin America", "Tropical Latin America",
                "Central Latin America", "Andean Latin America", "Caribbean",
                "High-income North America",
                "North Africa and Middle East",
                "Western Sub-Saharan Africa", "Eastern Sub-Saharan Africa",
                "Central Sub-Saharan Africa", "Southern Sub-Saharan Africa")

## ---- 读入并合并地区数据（C1 主文件 + C2 缺3地区 + C3 HINA）----
f1 <- file.path(BASE, "data", "raw", "C_sdi_regions_1990_2023.csv")
f2 <- file.path(BASE, "data", "raw", "C2_missing3regions_1990_2023.csv")
f3 <- file.path(BASE, "data", "raw", "C3_hina_1990_2023.csv")
c1 <- read.csv(f1, check.names = FALSE)
c2 <- if (file.exists(f2)) read.csv(f2, check.names = FALSE) else NULL
c3 <- if (file.exists(f3)) read.csv(f3, check.names = FALSE) else NULL
dat <- rbind(c1, c2, c3)
dat <- cn_en_col(dat, c("measure", "measure_name"))
dat <- cn_en_col(dat, c("location", "location_name"))
yc  <- if ("year" %in% names(dat)) "year" else "year_id"

present <- intersect(REGIONS_21, unique(dat$location_name))
missing <- setdiff(REGIONS_21, present)
cat("[regions] present:", length(present), "/21")
if (length(missing)) cat(" | missing:", paste(missing, collapse = "; "))
cat("\n")

## ---- 2023 断面 ----
d23 <- dat[dat$location_name %in% present & dat[[yc]] == 2023 &
           dat$metric_name == "Rate" & dat$sex_name == "Both" &
           dat$age_name == "Age-standardized", ]
d_asir   <- d23[d23$measure_name == "Incidence", c("location_name", "val")]
d_asdaly <- d23[d23$measure_name == "DALYs",  c("location_name", "val")]
names(d_asir)[2] <- "ASIR"; names(d_asdaly)[2] <- "ASDALY"
reg <- merge(d_asir, d_asdaly, by = "location_name")

## ---- EAPC（1990-2023 ASIR）----
## 95% CI 用 confint()（t 分布），与 02_eapc_trend.R calc_eapc 口径统一（2026-10-09 复审修订）
eapc_of <- function(v, yr) {
  ok <- is.finite(v) & v > 0
  if (sum(ok) < 10) return(c(EAPC = NA_real_, lo = NA_real_, hi = NA_real_))
  fit <- lm(log(v[ok]) ~ yr[ok])
  b  <- unname(coef(fit)[2])
  ci <- unname(confint(fit)[2, ])
  c(EAPC = 100 * (exp(b) - 1),
    lo   = 100 * (exp(ci[1]) - 1),
    hi   = 100 * (exp(ci[2]) - 1))
}
eapc_list <- lapply(present, function(lc) {
  d <- dat[dat$location_name == lc & dat$measure_name == "Incidence" &
           dat$metric_name == "Rate" & dat$sex_name == "Both" &
           dat$age_name == "Age-standardized" &
           dat[[yc]] %in% 1990:2023, ]
  d <- d[order(d[[yc]]), ]
  eapc_of(d$val, d[[yc]])
})
eapc_df <- do.call(rbind, eapc_list)
reg <- merge(reg, data.frame(location_name = present, eapc_df), by = "location_name")
reg <- reg[order(-reg$ASIR), ]

## ---- Table6 ----
t6 <- data.frame(Region = reg$location_name,
                 ASIR_2023 = round(reg$ASIR, 2),
                 ASDALY_2023 = round(reg$ASDALY, 2),
                 EAPC_ASIR = round(reg$EAPC, 2),
                 EAPC_lo = round(reg$lo, 2),
                 EAPC_hi = round(reg$hi, 2))
write.csv(t6, file.path(out_t, "Table6_region_ranking_2023.csv"), row.names = FALSE, fileEncoding = "UTF-8")
cat("[Table6] written:", nrow(t6), "regions\n")
print(t6, row.names = FALSE)

## ============ Figure10：地区排序横条图 ============
## 全球参照线（若在数据内）
glob <- dat[dat$location_name == "Global" & dat[[yc]] == 2023 &
            dat$measure_name == "Incidence" & dat$metric_name == "Rate" &
            dat$sex_name == "Both" & dat$age_name == "Age-standardized", "val"]
glob <- if (length(glob)) glob[1] else NA_real_

draw_f10 <- function() {
  v <- rev(reg$ASIR)               # barplot 首元素在底部 -> 反转使最大值在顶部
  names(v) <- rev(reg$location)
  cols <- rep("grey62", length(v))
  cols[names(v) == "East Asia"] <- "#C0392B"
  par(mar = c(4.2, 13.5, 2.4, 2.6), cex.axis = 0.82, cex.lab = 0.95, xpd = TRUE)
  bp <- barplot(v, horiz = TRUE, las = 1, col = cols, border = NA,
                xlim = c(0, max(v) * 1.18),
                xlab = "ASIR per 100 000 (2023)",
                names.arg = names(v),
                main = "Syphilis ASIR by GBD region, 2023")
  yv <- as.vector(bp)
  if (!is.na(glob)) {
    abline(v = glob, lty = 2, lwd = 1.6, col = "#1F618D")
    text(glob + max(v) * 0.015, max(yv) + 1.05,
         sprintf("Global %.0f", glob), pos = 4, cex = 0.82, col = "#1F618D", font = 2)
  }
  ## 数值标签加白色衬底，避免全局虚线穿过数字（2026-10-09 复审修订：
  ## High-income North America 106.4 的小数点被虚线压成"106|4"）
  tv <- sprintf("%.1f", v)
  for (i in seq_along(v)) {
    wlab <- strwidth(tv[i], units = "user", cex = 0.70)
    rect(v[i], yv[i] - 0.36, v[i] + wlab * 1.15, yv[i] + 0.36,
         col = "white", border = NA)
  }
  text(v, yv, labels = tv, pos = 4, cex = 0.70, col = "grey25")
}

mm <- 170
save_pub(file.path(out_f, "Figure10.png"), mm, 0.62 * mm)
draw_f10(); add_watermark(); dev.off()
save_pdf(file.path(out_f, "Figure10.pdf"), mm, 0.62 * mm)
draw_f10(); dev.off()
cat("[fig] Figure10.png / Figure10.pdf written\n")

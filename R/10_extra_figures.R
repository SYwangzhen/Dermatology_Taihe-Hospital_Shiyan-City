## ============================================================
## 10_extra_figures.R — 梅毒征文扩展图表（真实模式）
## Figure3：中国 ASIR/ASPR 性别对比（1990-2023）
## Figure4：中国 2023 年龄别发病模式（A 发病率 B 发病数）
## Figure5：中国 vs 全球 vs 高SDI（A ASIR B ASDR）
## Table2 ：中国 2023 年龄别新发感染数与发病率（分性别）
## ============================================================
source("00_config.R")
DEMO_MODE <- FALSE
WATERMARK <- ""
TAG       <- ""
source("01_load_clean.R")
source("06_figures.R")   # 复用 save_pub/save_pdf/add_watermark

dat <- load_data()
asr <- dat$asr
agx <- dat$agesex

out_f <- OUT_FIG
out_t <- OUT_TAB

## ---------- Figure3：性别对比 ----------
f3 <- function() {
  m_i <- asr[asr$location == "China" & asr$measure == "Incidence" & asr$sex %in% c("Male","Female"), ]
  m_i <- m_i[order(m_i$sex, m_i$year), ]
  p_i <- asr[asr$location == "China" & asr$measure == "Prevalence" & asr$sex %in% c("Male","Female"), ]
  p_i <- p_i[order(p_i$sex, p_i$year), ]
  mm <- 180
  save_pub(file.path(out_f, "Figure3.png"), mm, 0.60 * mm)
  par(mfrow = c(1, 2), mar = c(4, 4.4, 2.4, 1.0), cex.axis = 0.85, cex.lab = 0.9)
  plot(range(YEARS), range(c(m_i$val, p_i$val)) * c(0, 1.05), type = "n",
       xlab = "Year", ylab = "ASR per 100 000", las = 1,
       main = "A  ASIR by sex (China)")
  for (sx in c("Male", "Female")) {
    d <- m_i[m_i$sex == sx, ]
    lines(d$year, d$val, col = if (sx == "Male") "#1F618D" else "#C0392B", lwd = 2.2)
  }
  legend("topleft", legend = c("Male", "Female"), col = c("#1F618D", "#C0392B"),
         lwd = 2.2, cex = 0.8, bty = "n")
  plot(range(YEARS), range(c(p_i$val, m_i$val)) * c(0, 1.05), type = "n",
       xlab = "Year", ylab = "ASR per 100 000", las = 1,
       main = "B  ASPR by sex (China)")
  for (sx in c("Male", "Female")) {
    d <- p_i[p_i$sex == sx, ]
    lines(d$year, d$val, col = if (sx == "Male") "#1F618D" else "#C0392B", lwd = 2.2)
  }
  legend("topleft", legend = c("Male", "Female"), col = c("#1F618D", "#C0392B"),
         lwd = 2.2, cex = 0.8, bty = "n")
  add_watermark(); dev.off()
  save_pdf(file.path(out_f, "Figure3.pdf"), mm, 0.60 * mm)
  par(mfrow = c(1, 2), mar = c(4, 4.4, 2.4, 1.0), cex.axis = 0.85, cex.lab = 0.9)
  plot(range(YEARS), range(c(m_i$val, p_i$val)) * c(0, 1.05), type = "n",
       xlab = "Year", ylab = "ASR per 100 000", main = "A")
  for (sx in c("Male", "Female")) {
    d <- m_i[m_i$sex == sx, ]
    lines(d$year, d$val, col = if (sx == "Male") "#1F618D" else "#C0392B", lwd = 2.2)
  }
  plot(range(YEARS), range(c(p_i$val, m_i$val)) * c(0, 1.05), type = "n",
       xlab = "Year", ylab = "ASR per 100 000", main = "B")
  for (sx in c("Male", "Female")) {
    d <- p_i[p_i$sex == sx, ]
    lines(d$year, d$val, col = if (sx == "Male") "#1F618D" else "#C0392B", lwd = 2.2)
  }
  add_watermark(); dev.off()
  cat("[fig] Figure3 written\n")
}

## ---------- Figure4：2023 年龄别发病模式 ----------
f4 <- function() {
  ACUTE <- AGE_GROUPS[1:13]   # 0-4 .. 60-64（GBD 65+ 发病为零，不展示全零组）
  d23 <- agx[agx$location == "China" & agx$year == 2023 &
             agx$measure == "Incidence" & agx$sex %in% c("Male", "Female", "Both"), ]
  d23 <- d23[d23$age %in% ACUTE, ]
  d23$age <- factor(d23$age, levels = ACUTE)
  rate_m <- tapply(d23$rate[d23$sex == "Male"], d23$age[d23$sex == "Male"], sum)
  rate_f <- tapply(d23$rate[d23$sex == "Female"], d23$age[d23$sex == "Female"], sum)
  cnt_m  <- tapply(d23$count[d23$sex == "Male"], d23$age[d23$sex == "Male"], sum)
  cnt_f  <- tapply(d23$count[d23$sex == "Female"], d23$age[d23$sex == "Female"], sum)
  m4r <- rbind(Male = rate_m, Female = rate_f)
  m4c <- rbind(Male = cnt_m,  Female = cnt_f)
  mm <- 180
  save_pub(file.path(out_f, "Figure4.png"), mm, 0.60 * mm)
  par(mfrow = c(1, 2), mar = c(6.5, 4.4, 2.4, 1.0), cex.axis = 0.72, cex.lab = 0.9)
  barplot(m4r, beside = TRUE, las = 2, col = c("#1F618D", "#C0392B"),
          border = NA, ylab = "Incidence per 100 000",
          main = "A  Incidence rate by age")
  abline(h = 0)
  barplot(m4c, beside = TRUE, las = 2, col = c("#1F618D", "#C0392B"),
          border = NA, ylab = "Incident cases",
          main = "B  Incident cases")
  legend("topright", legend = c("Male", "Female"), fill = c("#1F618D", "#C0392B"),
         cex = 0.7, bty = "n")
  add_watermark(); dev.off()
  save_pdf(file.path(out_f, "Figure4.pdf"), mm, 0.60 * mm)
  par(mfrow = c(1, 2), mar = c(6.5, 4.4, 2.4, 1.0), cex.axis = 0.72, cex.lab = 0.9)
  barplot(m4r, beside = TRUE, las = 2, border = NA, col = c("#1F618D", "#C0392B"),
          main = "A", ylab = "Incidence per 100 000")
  barplot(m4c, beside = TRUE, las = 2, border = NA, col = c("#1F618D", "#C0392B"),
          main = "B", ylab = "Incident cases")
  add_watermark(); dev.off()
  cat("[fig] Figure4 written\n")
}

## ---------- Figure5：国际对比 ----------
f5 <- function() {
  i <- asr[asr$measure == "Incidence" & asr$sex == "Both" &
           asr$location %in% c("China", "Global", "High SDI"), ]
  i <- i[order(i$location, i$year), ]
  d <- asr[asr$measure == "Deaths" & asr$sex == "Both" &
           asr$location %in% c("China", "Global", "High SDI"), ]
  d <- d[order(d$location, d$year), ]
  cols <- c(China = "#C0392B", Global = "#1F618D", "High SDI" = "#229954")
  mm <- 180
  save_pub(file.path(out_f, "Figure5.png"), mm, 0.60 * mm)
  par(mfrow = c(1, 2), mar = c(4, 4.4, 2.4, 1.0), cex.axis = 0.85, cex.lab = 0.9)
  plot(range(YEARS), range(i$val) * c(0.9, 1.05), type = "n",
       xlab = "Year", ylab = "ASIR per 100 000", las = 1,
       main = "A  ASIR: China vs Global vs High SDI")
  for (lc in c("China", "Global", "High SDI")) {
    dd <- i[i$location == lc, ]
    lines(dd$year, dd$val, col = cols[[lc]], lwd = 2.2)
  }
  legend("topleft", legend = c("China", "Global", "High SDI"),
         col = cols, lwd = 2.2, cex = 0.8, bty = "n")
  plot(range(YEARS), range(d$val) * c(0.9, 1.05), type = "n",
       xlab = "Year", ylab = "ASDR per 100 000", las = 1,
       main = "B  ASDR: China vs Global vs High SDI")
  for (lc in c("China", "Global", "High SDI")) {
    dd <- d[d$location == lc, ]
    lines(dd$year, dd$val, col = cols[[lc]], lwd = 2.2)
  }
  legend("topright", legend = c("China", "Global", "High SDI"),
         col = cols, lwd = 2.2, cex = 0.8, bty = "n")
  add_watermark(); dev.off()
  save_pdf(file.path(out_f, "Figure5.pdf"), mm, 0.60 * mm)
  par(mfrow = c(1, 2), mar = c(4, 4.4, 2.4, 1.0), cex.axis = 0.85, cex.lab = 0.9)
  plot(range(YEARS), range(i$val) * c(0.9, 1.05), type = "n",
       xlab = "Year", ylab = "ASIR per 100 000", main = "A")
  for (lc in c("China", "Global", "High SDI")) {
    dd <- i[i$location == lc, ]
    lines(dd$year, dd$val, col = cols[[lc]], lwd = 2.2)
  }
  plot(range(YEARS), range(d$val) * c(0.9, 1.05), type = "n",
       xlab = "Year", ylab = "ASDR per 100 000", main = "B")
  for (lc in c("China", "Global", "High SDI")) {
    dd <- d[d$location == lc, ]
    lines(dd$year, dd$val, col = cols[[lc]], lwd = 2.2)
  }
  add_watermark(); dev.off()
  cat("[fig] Figure5 written\n")
}

## ---------- Table2：2023 年龄别新发感染（分性别） ----------
t2 <- function() {
  d23 <- agx[agx$location == "China" & agx$year == 2023 &
             agx$measure == "Incidence" & agx$sex != "Both" &
             agx$age %in% c(AGE_GROUPS, "All ages"), ]
  cnt <- dcast_stub <- reshape(d23[, c("age", "sex", "count", "rate")],
                               idvar = "age", timevar = "sex", direction = "wide")
  names(cnt) <- gsub("count\\.", "cases_", names(cnt))
  names(cnt) <- gsub("rate\\.", "rate_", names(cnt))
  cnt$age <- factor(cnt$age, levels = c(AGE_GROUPS, "All ages"))
  cnt <- cnt[order(cnt$age), ]
  write.csv(cnt, file.path(out_t, "Table2_age_sex_2023.csv"), row.names = FALSE)
  cat("[tab] Table2 written:", file.path(out_t, "Table2_age_sex_2023.csv"), "\n")
  print(cnt)
}

f3(); f4(); f5(); t2()
cat("\nExtra figures/tables done.\n")

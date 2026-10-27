## ============================================================
## 07_tables.R — Table 1（OA 版：1990/2023 负担 + EAPC）
## 行：Measure × Location(China, Global) × Sex(Both 为主)
## 列：cases(1990/2023, 由 age×sex 表求和) + ASR(95% UI) + EAPC(95% CI) + 趋势判定
## 输出：CSV（+XLSX，若 openxlsx 可用）
## ============================================================

fmt_num <- function(x, d = 1) formatC(x, format = "f", digits = d, big.mark = ",")
fmt_ui  <- function(v, l, u, d = 1) paste0(fmt_num(v, d), " (", fmt_num(l, d),
                                           "-", fmt_num(u, d), ")")

allage_counts <- function(d_agesex, measure, location, sex, year) {
  s <- d_agesex[d_agesex$measure == measure & d_agesex$location == location &
                d_agesex$sex == sex & d_agesex$year == year, ]
  sum(s$count, na.rm = TRUE)
}

make_table1 <- function(d_asr, d_agesex) {
  tr <- trend_stats(d_asr)
  tr$cls <- trend_class(tr$eapc_lo, tr$eapc_hi)
  locs <- c(FOCUS_LOC, REF_LOCS)
  rows <- list()
  for (loc in locs) for (m in MEASURES) for (sx in c("Both", "Male", "Female")) {
    t <- tr[tr$location == loc & tr$measure == m & tr$sex == sx, ]
    if (!nrow(t)) next
    c0 <- allage_counts(d_agesex, m, loc, sx, t$year0)
    c1 <- allage_counts(d_agesex, m, loc, sx, t$year1)
    rows[[length(rows) + 1]] <- data.frame(
      location = loc, measure = m, sex = sx,
      cases_1990 = round(c0), cases_2023 = round(c1),
      ASR_1990 = fmt_ui(t$value0, t$lower0, t$upper0),
      ASR_2023 = fmt_ui(t$value1, t$lower1, t$upper1),
      EAPC = fmt_ui(t$eapc, t$eapc_lo, t$eapc_hi, 2),
      trend = t$cls, stringsAsFactors = FALSE)
  }
  tab <- do.call(rbind, rows)
  p_csv <- file.path(OUT_TAB, paste0("Table1", TAG, ".csv"))
  write.csv(tab, p_csv, row.names = FALSE)
  cat("[tab] Table1 written:", p_csv, "\n")
  if (requireNamespace("openxlsx", quietly = TRUE)) {
    p_x <- sub("\\.csv$", ".xlsx", p_csv)
    openxlsx::write.xlsx(tab, p_x)
    cat("[tab] Table1 (xlsx) written:", p_x, "\n")
  }
  invisible(tab)
}

## —— 给稿件正文用的"可读数字卡"（Joinpoint 结果速览）——
save_joinpoint_tables <- function(jp) {
  out <- do.call(rbind, lapply(names(jp), function(m) {
    s <- jp[[m]]$summary
    data.frame(measure = m, s, stringsAsFactors = FALSE)
  }))
  p <- file.path(OUT_TAB, paste0("Joinpoint_summary", TAG, ".csv"))
  write.csv(out, p, row.names = FALSE)
  cat("[tab] Joinpoint segment table written:", p, "\n")
  invisible(out)
}

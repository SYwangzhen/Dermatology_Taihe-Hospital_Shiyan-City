## ============================================================
## 01_load_clean.R — 读入 GBD 下载 CSV（或触发 demo 造数）并清洗
## 兼容 IHME Results Tool 导出列名（measure_name/location_name/...）
## ============================================================

`%||%` <- function(a, b) if (is.null(a) || length(a) == 0 || all(is.na(a))) b else a

## ============ 中英双语值归一（IHME Results Tool 中文界面导出值为中文） ============
CN_EN <- function(x) {
  x <- trimws(as.character(x))
  map <- c("发病率"="Incidence", "患病率"="Prevalence", "死亡"="Deaths",
           "死亡人数"="Deaths", "伤残调整生命年"="DALYs", "伤残调整寿命年"="DALYs",
           "伤残调整健康生命年"="DALYs", "DALY"="DALYs",
           "DALYs (Disability-Adjusted Life Years)"="DALYs",
           "YLDs (Years Lived with Disability)"="YLDs", "YLLs (Years of Life Lost)"="YLLs",
           "中国"="China", "全球"="Global", "高SDI"="High SDI",
           "高社会人口指数"="High SDI", "高社会人口学指数"="High SDI",
           "合计"="Both", "男"="Male", "女"="Female",
           "年龄标准化"="Age-standardized", "年龄标化"="Age-standardized",
           "所有年龄"="All ages", "全部年龄"="All ages",
           "率"="Rate", "数"="Number", "数量"="Number")
  ifelse(x %in% names(map), unname(map[x]), x)
}
## 将指定候选列的值做中英归一（英文原值原样通过）
cn_en_col <- function(d, cands) {
  for (c in cands) {
    m <- grep(paste0("^", c, "$"), names(d), ignore.case = TRUE)
    if (length(m)) { j <- names(d)[m[1]]; d[[j]] <- CN_EN(d[[j]]); break }
  }
  d
}
## 年龄列专用归一：先过 CN_EN（'年龄标准化'/'所有年龄'），再把中文年龄组转英文组名
##   '5岁以下' -> '0-4'；'10-14岁' -> '10-14'；'>95岁'/'95岁以上' -> '95+'；英文组名原样
AGE_CN_EN <- function(x) {
  x <- CN_EN(x)
  x[x == "5岁以下"]  <- "0-4"
  x[x == ">95岁"]    <- "95+"
  x[x == "95岁以上"] <- "95+"
  x[x == "85岁及以上"] <- "85-89"
  ## GBD 2023 英文界面导出："<5 years" -> "0-4"；"10-14 years" -> "10-14"；"95+ years" -> "95+"
  x <- trimws(sub("years$", "", x))
  x[x == "<5"]  <- "0-4"
  sub("岁$", "", x)
}
cn_en_age_col <- function(d, cands) {
  for (c in cands) {
    m <- grep(paste0("^", c, "$"), names(d), ignore.case = TRUE)
    if (length(m)) { j <- names(d)[m[1]]; d[[j]] <- AGE_CN_EN(d[[j]]); break }
  }
  d
}

find_col <- function(df, cands) {
  ## 在 data.frame 列名中模糊匹配候选名
  hit <- NULL
  for (c in cands) {
    m <- grep(paste0("^", c, "$"), names(df), ignore.case = TRUE)
    if (length(m)) { hit <- names(df)[m[1]]; break }
  }
  if (is.null(hit)) stop("列未找到，候选: ", paste(cands, collapse = " / "),
                        "；实际列: ", paste(names(df), collapse = ", "))
  hit
}

tidy_asr_file <- function(path) {
  d <- read.csv(path, check.names = FALSE, stringsAsFactors = FALSE)
  d <- cn_en_col(d, c("measure", "measure_name"))
  d <- cn_en_col(d, c("location", "location_name"))
  d <- cn_en_col(d, c("sex", "sex_name"))
  d <- cn_en_age_col(d, c("age", "age_name"))
  d <- cn_en_col(d, c("metric", "metric_name"))
  c_m <- find_col(d, c("measure", "measure_name", "cause"))
  c_l <- find_col(d, c("location", "location_name"))
  c_s <- find_col(d, c("sex", "sex_name"))
  c_y <- find_col(d, c("year"))
  c_v <- find_col(d, c("val", "value"))
  has_ui <- any(grepl("^(upper|lower)$", names(d), ignore.case = TRUE))
  has_metric <- any(grepl("^metric", names(d), ignore.case = TRUE))
  out <- data.frame(
    measure  = d[[c_m]],
    location = d[[c_l]],
    sex      = d[[c_s]],
    year     = as.numeric(d[[c_y]]),
    val      = as.numeric(d[[c_v]]),
    stringsAsFactors = FALSE)
  if (has_ui) {
    out$lower <- as.numeric(d[[find_col(d, c("lower"))]])
    out$upper <- as.numeric(d[[find_col(d, c("upper"))]])
  } else { out$lower <- NA; out$upper <- NA }
  if (has_metric) {  ## 只要 Rate 行（ASR）；若文件只含 Number 则保留 val 原样并提示
    c_mt <- find_col(d, c("metric", "metric_name"))
    if ("Rate" %in% d[[c_mt]]) out <- out[d[[c_mt]] == "Rate", ]
  }
  out[!is.na(out$year) & out$year >= 1990, ]
}

tidy_agesex_file <- function(path) {
  d <- read.csv(path, check.names = FALSE, stringsAsFactors = FALSE)
  d <- cn_en_col(d, c("measure", "measure_name"))
  d <- cn_en_col(d, c("location", "location_name"))
  d <- cn_en_col(d, c("sex", "sex_name"))
  d <- cn_en_age_col(d, c("age", "age_name"))
  d <- cn_en_col(d, c("metric", "metric_name"))
  ## —— 本地/demo 格式：已有 count/rate 两列 ——
  if (any(grepl("^count$", names(d), ignore.case = TRUE))) {
    out <- data.frame(
      measure  = d[[find_col(d, c("measure", "measure_name"))]],
      location = d[[find_col(d, c("location", "location_name"))]],
      sex      = d[[find_col(d, c("sex", "sex_name"))]],
      age      = d[[find_col(d, c("age", "age_name"))]],
      year     = as.numeric(d[[find_col(d, c("year"))]]),
      count    = as.numeric(d[[find_col(d, c("count"))]]),
      rate     = as.numeric(d[[find_col(d, c("rate"))]]),
      stringsAsFactors = FALSE)
    out$pop <- ifelse(out$rate > 0, out$count / out$rate * 1e5, NA)
    out <- out[!is.na(out$year) & out$year >= 1990, ]
    return(out)
  }
  ## —— IHME 导出格式：val + metric(Number/Rate) ——
  c_m <- find_col(d, c("measure", "measure_name"))
  c_l <- find_col(d, c("location", "location_name"))
  c_s <- find_col(d, c("sex", "sex_name"))
  c_a <- find_col(d, c("age", "age_name"))
  c_y <- find_col(d, c("year"))
  c_v <- find_col(d, c("val", "value"))
  has_metric <- any(grepl("^metric", names(d), ignore.case = TRUE))
  if (has_metric) {
    c_mt <- find_col(d, c("metric", "metric_name"))
    num <- d[[c_mt]] == "Number"
    rat <- d[[c_mt]] == "Rate"
  } else { num <- rep(TRUE, nrow(d)); rat <- rep(FALSE, nrow(d)) }
  ## 同一行同时含 Number 与 Rate 的情况：分成宽表
  key <- paste(d[[c_m]], d[[c_l]], d[[c_s]], d[[c_a]], d[[c_y]], sep = "|")
  cnt <- tapply(ifelse(num, d[[c_v]], NA), key, sum, na.rm = TRUE)
  rte <- tapply(ifelse(rat, d[[c_v]], NA), key, sum, na.rm = TRUE)
  kk  <- strsplit(names(cnt), "\\|")
  out <- data.frame(
    measure  = sapply(kk, `[`, 1), location = sapply(kk, `[`, 2),
    sex      = sapply(kk, `[`, 3), age      = sapply(kk, `[`, 4),
    year     = as.numeric(sapply(kk, `[`, 5)),
    count    = as.numeric(cnt), rate = as.numeric(rte), stringsAsFactors = FALSE)
  out <- out[!is.na(out$count) & out$year >= 1990, ]
  ## 剔除 age-standardized 行：不属于年龄结构网格，混入会污染 all-age 计数与分解
  out <- out[out$age != "Age-standardized", ]
  ## 由 count/rate 反推年龄组人口（当 rate>0），供分解用
  out$pop <- ifelse(out$rate > 0, out$count / out$rate * 1e5, NA)
  ## 补全"零负担"年龄格（IHME 对部分年龄-测量组合不给 Number/Rate 行），
  ## 保证 20 年龄组 × 全网格完整，供 APC / 分解 / 计数使用
  full <- expand.grid(measure  = unique(out$measure),
                      location = unique(out$location),
                      sex      = unique(out$sex),
                      age      = AGE_GROUPS,
                      year     = sort(unique(out$year)),
                      KEEP.OUT.ATTRS = FALSE, stringsAsFactors = FALSE)
  mrg <- merge(full, out, all.x = TRUE,
               by = c("measure", "location", "sex", "age", "year"))
  mrg$count[is.na(mrg$count)] <- 0
  mrg$rate[is.na(mrg$rate)]   <- 0
  mrg$pop[is.na(mrg$pop)]     <- 0
  out <- mrg[order(match(mrg$measure, unique(out$measure)),
                   match(mrg$location, unique(out$location)),
                   match(mrg$sex, unique(out$sex)),
                   match(mrg$age, AGE_GROUPS), mrg$year), ]
  rownames(out) <- NULL
  out
}

load_data <- function() {
  if (DEMO_MODE) {
    cat("[load] demo mode: generating synthetic data into *_DEMO.csv (real downloads untouched).\n")
    source(file.path(R_DIR, "demo_data.R"))
    gen_demo_data()
    f_asr   <- sub("\\.csv$", "_DEMO.csv", FILE_ASR)
    f_ages  <- sub("\\.csv$", "_DEMO.csv", FILE_AGESEX)
  } else {
    if (!file.exists(FILE_ASR) || !file.exists(FILE_AGESEX))
      stop("real data not found: place A_ASR_1990_2023.csv / B_age_sex_1990_2023.csv under data/raw/, or run --demo first.")
    f_asr   <- FILE_ASR
    f_ages  <- FILE_AGESEX
  }
  d_asr   <- tidy_asr_file(f_asr)
  d_agesex<- tidy_agesex_file(f_ages)
  d_asr   <- d_asr[d_asr$sex %in% SEXES, ]
  d_agesex<- d_agesex[d_agesex$sex %in% SEXES, ]
  ## 剔除文件自带 Both(合计) 行：统一由 Male+Female 重算，
  ## 避免与下方汇总 Both 重复导致计数翻倍（IHME 导出含 Both 行；demo 数据无）
  d_agesex <- d_agesex[d_agesex$sex != "Both", ]
  ## age×sex 表补 Both 性别（Male+Female 汇总），供计数与分解使用
  agg <- d_agesex
  ## NaN/NA 人口归零，防 aggregate 公式法(na.action=na.omit)误删"零负担"年龄行
  agg$pop[!is.finite(agg$pop)]   <- 0
  agg$count[!is.finite(agg$count)] <- 0
  ag <- aggregate(cbind(count, pop) ~ measure + location + age + year,
                  data = agg, FUN = sum, na.rm = TRUE)
  ag$sex <- "Both"
  ag$rate <- ifelse(ag$pop > 0, ag$count / ag$pop * 1e5, NA)
  ag <- ag[, c("measure", "location", "sex", "age", "year",
               "count", "rate", "pop")]
  d_agesex <- rbind(d_agesex, ag)
  cat(sprintf("[load] ASR rows: %d ; age-sex rows: %d\n", nrow(d_asr), nrow(d_agesex)))
  list(asr = d_asr, agesex = d_agesex)
}

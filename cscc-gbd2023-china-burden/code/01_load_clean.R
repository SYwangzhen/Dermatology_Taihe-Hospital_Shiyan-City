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
  ## 复合年龄组（85岁及以上 等）不属于 GBD 5 岁分组网格，不得静默映射（如 85-89），
  ## 必须显式报错——否则会污染年龄结构与分解
  bad <- x %in% c("85岁及以上", "85+岁", "85+ years", "80+岁")
  if (any(bad)) stop("年龄组 '", paste(unique(x[bad]), collapse = "', '"),
                     "' 不属于 GBD 5 岁分组网格（0-4 ... 90-94, 95+），请核对下载参数。")
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
  c_a <- find_col(d, c("age", "age_name"))
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
  ## ASR 文件必须含 Age-standardized + Rate 行；仅保留该组合，
  ## 严禁 All-ages 粗率混入 EAPC 回归（防静默选错数据）
  if (has_metric) {
    c_mt <- find_col(d, c("metric", "metric_name"))
    keep <- d[[c_mt]] == "Rate" & d[[c_a]] == "Age-standardized"
    if (!any(keep)) stop("ASR 文件中未找到 Age-standardized + Rate 行: ", path)
    out <- out[keep, ]
  } else {
    ## 无 metric 列时必须全部为 Age-standardized 行，否则报错
    if (!all(d[[c_a]] == "Age-standardized"))
      stop("ASR 文件缺少 metric 列且存在非 Age-standardized 行，拒绝静默处理: ", path)
  }
  out <- out[!is.na(out$year) & out$year >= 1990, ]
  ## 唯一性断言：每个 地区×性别×指标×年份 恰好一行
  key <- paste(out$measure, out$location, out$sex, out$year, sep = "|")
  if (anyDuplicated(key))
    stop("ASR 文件存在重复键（地区×性别×指标×年份）: ",
         paste(unique(key[duplicated(key)]), collapse = "; "))
  out
}

## GBD 2023 人口（直接下载；解压后的 CSV）。人口一律取自本文件，
## 严禁用 count/rate 反推（正文与 eMethods 2 已废弃该流程）。
tidy_pop_file <- function(path) {
  d <- read.csv(path, check.names = FALSE, stringsAsFactors = FALSE)
  d <- cn_en_col(d, c("location", "location_name"))
  d <- cn_en_col(d, c("sex", "sex_name"))
  ## 人口文件年龄标签归一到 B 表网格："<5 years"->"0-4"，"95+ years"->"95+"，
  ## 其余 "10-14 years" -> "10-14"（与 AGE_CN_EN 后的 age×sex 网格一致）
  c_a0 <- find_col(d, c("age", "age_name"))
  a <- trimws(as.character(d[[c_a0]]))
  a[a == "<5 years"]  <- "0-4"
  a[a == "95+ years"] <- "95+"
  a <- sub(" years$", "", a)
  d[[c_a0]] <- a
  c_l <- find_col(d, c("location", "location_name"))
  c_s <- find_col(d, c("sex", "sex_name"))
  c_a <- find_col(d, c("age", "age_name"))
  c_y <- find_col(d, c("year"))
  c_v <- find_col(d, c("val", "value"))
  out <- data.frame(
    location = d[[c_l]], sex = d[[c_s]], age = d[[c_a]],
    year = as.numeric(d[[c_y]]), pop = as.numeric(d[[c_v]]),
    stringsAsFactors = FALSE)
  out <- out[out$age != "All ages", ]   # 全年龄行由各年龄组求和校验后另行生成
  key <- paste(out$location, out$sex, out$age, out$year, sep = "|")
  if (anyDuplicated(key)) stop("人口文件存在重复键: ", paste(unique(key[duplicated(key)]), collapse = "; "))
  if (any(!is.finite(out$pop) | out$pop < 0)) stop("人口文件含缺失或负值: ", path)
  out
}

tidy_agesex_file <- function(path, d_pop = NULL) {
  d <- read.csv(path, check.names = FALSE, stringsAsFactors = FALSE)
  d <- cn_en_col(d, c("measure", "measure_name"))
  d <- cn_en_col(d, c("location", "location_name"))
  d <- cn_en_col(d, c("sex", "sex_name"))
  d <- cn_en_age_col(d, c("age", "age_name"))
  d <- cn_en_col(d, c("metric", "metric_name"))
  ## —— 本地/demo 格式：已有 count/rate 两列（仅 demo 合成数据走此分支）——
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
    ## demo 专用：合成数据人口由 count/rate 反推（DEMO 数字不可引用）；
    ## 真实数据一律走下方 IHME 分支 + 直接人口表
    out$pop <- ifelse(out$rate > 0, out$count / out$rate * 1e5, NA)
    out <- out[!is.na(out$year) & out$year >= 1990, ]
    return(out)
  }
  ## —— IHME 导出格式：val + metric(Number/Rate)，人口取自直接下载表 ——
  c_m <- find_col(d, c("measure", "measure_name"))
  c_l <- find_col(d, c("location", "location_name"))
  c_s <- find_col(d, c("sex", "sex_name"))
  c_a <- find_col(d, c("age", "age_name"))
  c_y <- find_col(d, c("year"))
  c_v <- find_col(d, c("val", "value"))
  c_mt <- find_col(d, c("metric", "metric_name"))
  num <- d[[c_mt]] == "Number"
  rat <- d[[c_mt]] == "Rate"
  ## 同一行同时含 Number 与 Rate 的情况：分成宽表
  key <- paste(d[[c_m]], d[[c_l]], d[[c_s]], d[[c_a]], d[[c_y]], sep = "|")
  cnt <- tapply(ifelse(num, d[[c_v]], NA), key, function(z) {
    z <- z[!is.na(z)]
    if (length(z) == 0) return(NA_real_)
    if (length(z) > 1) stop("计数键重复，请核对下载参数")
    z })
  rte <- tapply(ifelse(rat, d[[c_v]], NA), key, function(z) {
    z <- z[!is.na(z)]
    if (length(z) == 0) return(NA_real_)
    if (length(z) > 1) stop("率键重复，请核对下载参数")
    z })
  kk  <- strsplit(names(cnt), "\\|")
  out <- data.frame(
    measure  = sapply(kk, `[`, 1), location = sapply(kk, `[`, 2),
    sex      = sapply(kk, `[`, 3), age      = sapply(kk, `[`, 4),
    year     = as.numeric(sapply(kk, `[`, 5)),
    count    = as.numeric(cnt), rate = as.numeric(rte), stringsAsFactors = FALSE)
  out <- out[!is.na(out$year) & out$year >= 1990, ]
  ## 剔除 age-standardized 行：不属于年龄结构网格，混入会污染 all-age 计数与分解
  out <- out[out$age != "Age-standardized", ]
  ## 人口：直接合并 GBD 2023 人口表（严禁 count/rate 反推）。
  ## 人口表仅覆盖中国（与下载参数一致）；非中国行保留计数、人口/率置 NA
  ## （Table 1 只用计数，分解/APC 仅限中国）。
  if (is.null(d_pop)) stop("tidy_agesex_file 需要直接下载人口表 d_pop（tidy_pop_file）。")
  out$pop <- d_pop$pop[match(paste(out$location, out$sex, out$age, out$year, sep = "|"),
                             paste(d_pop$location, d_pop$sex, d_pop$age, d_pop$year, sep = "|"))]
  ## "零负担"年龄格：仅计 数 置 0（IHME 对 <20 岁 SCC 死亡等无模型输出，
  ## 属预期缺失）；人口不得置 0，率由 count/pop 重算；其他缺失一律报错
  miss_cnt <- is.na(out$count)
  miss_pop <- is.na(out$pop) & !miss_cnt
  miss_focus <- miss_pop & out$location == FOCUS_LOC
  if (any(miss_focus))
    stop("人口表未覆盖（中国行计数存在但人口缺失）: ",
         paste(sprintf("%s|%s|%s|%s", out$measure[miss_focus], out$location[miss_focus],
                       out$sex[miss_focus], out$age[miss_focus]), collapse = "; "))
  out$count[miss_cnt] <- 0
  out$rate <- ifelse(is.finite(out$pop) & out$pop > 0, out$count / out$pop * 1e5, NA_real_)
  ## 中国：20 年龄组 × 全网格补全（缺失计数格=0；人口来自人口表）
  locs_pop <- unique(d_pop$location)
  out_f <- out[out$location %in% locs_pop, ]
  full <- expand.grid(measure  = unique(out_f$measure),
                      location = unique(out_f$location),
                      sex      = unique(out_f$sex),
                      age      = AGE_GROUPS,
                      year     = sort(unique(out_f$year)),
                      KEEP.OUT.ATTRS = FALSE, stringsAsFactors = FALSE)
  ## 人口铺满网格（按 sex×age×year），再合并计数
  full$pop <- d_pop$pop[match(paste(full$location, full$sex, full$age, full$year, sep = "|"),
                              paste(d_pop$location, d_pop$sex, d_pop$age, d_pop$year, sep = "|"))]
  if (any(is.na(full$pop)))
    stop("人口表未覆盖全部 sex×age×year 组合，缺 ",
         sum(is.na(full$pop)), " 格——请核对人口下载参数。")
  mrg <- merge(full, out_f[, c("measure", "location", "sex", "age", "year", "count")],
               all.x = TRUE, by = c("measure", "location", "sex", "age", "year"))
  mrg$count[is.na(mrg$count)] <- 0          # 仅计数置 0（无模型输出的可忽略负担年龄格）
  mrg$rate <- ifelse(mrg$pop > 0, mrg$count / mrg$pop * 1e5, NA_real_)
  out_cn <- mrg[, c("measure", "location", "sex", "age", "year", "count", "rate", "pop")]
  ## 非中国地区：仅保留计数（pop/rate = NA），供 Table 1 计数列
  out_non <- out[!out$location %in% locs_pop,
                 c("measure", "location", "sex", "age", "year", "count", "rate", "pop")]
  out <- rbind(out_cn, out_non)
  out <- out[order(match(out$measure, unique(out$measure)),
                   match(out$location, unique(out$location)),
                   match(out$sex, unique(out$sex)),
                   match(out$age, AGE_GROUPS), out$year), ]
  rownames(out) <- NULL
  out
}

load_data <- function() {
  if (DEMO_MODE || !file.exists(FILE_ASR) || !file.exists(FILE_AGESEX) || !file.exists(FILE_POP)) {
    if (!DEMO_MODE) stop("real data not found: download per 01_GBD2023下载参数快照.md ",
                         "(含人口表 C_Population_1990_2023.csv) and place under data/raw/, or run --demo first.")
    cat("[load] demo mode: (re)generating synthetic data.\n")
    source(file.path(R_DIR, "demo_data.R"))
    gen_demo_data()
  }
  d_asr   <- tidy_asr_file(FILE_ASR)
  d_asr   <- d_asr[d_asr$sex %in% SEXES, ]
  if (DEMO_MODE) {
    ## demo：合成数据无人口表，沿用 Male+Female 汇总（数字不可引用）
    d_agesex <- tidy_agesex_file(FILE_AGESEX)
    d_agesex <- d_agesex[d_agesex$sex %in% SEXES, ]
    agg <- d_agesex
    agg$pop[!is.finite(agg$pop)]     <- 0
    agg$count[!is.finite(agg$count)] <- 0
    ag <- aggregate(cbind(count, pop) ~ measure + location + age + year,
                    data = agg, FUN = sum, na.rm = TRUE)
    ag$sex <- "Both"
    ag$rate <- ifelse(ag$pop > 0, ag$count / ag$pop * 1e5, NA)
    ag <- ag[, c("measure", "location", "sex", "age", "year", "count", "rate", "pop")]
    d_agesex <- rbind(d_agesex, ag)
  } else {
    ## 真实数据：人口一律取自直接下载的 GBD 2023 人口表（eMethods 2）；
    ## 保留 GBD 自带 Both 行（不再删除重算），并断言与 Male+Female 一致
    d_pop    <- tidy_pop_file(FILE_POP)
    d_agesex <- tidy_agesex_file(FILE_AGESEX, d_pop = d_pop)
    d_agesex <- d_agesex[d_agesex$sex %in% SEXES, ]
    chk <- d_agesex[d_agesex$location == FOCUS_LOC & d_agesex$year %in% c(1990, 2023), ]
    agg_sex <- aggregate(count ~ measure + sex + year, data = chk[chk$sex != "Both", ], FUN = sum)
    agg_sex <- aggregate(count ~ measure + year, data = agg_sex, FUN = sum)  # Male+Female
    both    <- aggregate(count ~ measure + year, data = chk[chk$sex == "Both", ], FUN = sum)
    cmp <- merge(agg_sex, both, by = c("measure", "year"), suffixes = c("_mf", "_both"))
    rel <- abs(cmp$count_mf - cmp$count_both) / cmp$count_both
    if (max(rel) > 0.001)
      stop("GBD Both 行与 Male+Female 之和差异超过 0.1%（max ", sprintf("%.4f%%", max(rel) * 100),
           "），请核对数据下载参数。")
    ## 年份完整性：每个 地区×性别×指标 覆盖 1990-2023 全部 34 年
    cov <- tapply(d_agesex$year, paste(d_agesex$measure, d_agesex$location, d_agesex$sex),
                  function(y) length(unique(y)) == length(YEARS) && setequal(unique(y), YEARS))
    if (!all(cov))
      stop("年龄×性别表年份覆盖不完整: ", paste(names(cov)[!cov], collapse = "; "))
  }
  cat(sprintf("[load] ASR rows: %d ; age-sex rows: %d\n", nrow(d_asr), nrow(d_agesex)))
  list(asr = d_asr, agesex = d_agesex)
}

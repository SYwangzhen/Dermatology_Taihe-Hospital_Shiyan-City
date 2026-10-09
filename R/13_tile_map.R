## ============================================================
## 13_tile_map.R — Figure12：全球梅毒 ASIR 等面积方格地图（tile grid map）
## 合规设计：不绘制任何国界/领土多边形，每国一个等大小方格，
## 方格位置按国家质心经纬度吸附到 8 度网格（冲突时向最近空格移动）。
## 颜色 = 2023 ASIR；中国方格黑框突出。
## ============================================================
source("00_config.R")
DEMO_MODE <- FALSE
WATERMARK <- ""
source("01_load_clean.R")
source("06_figures.R")

out_f <- OUT_FIG

## ---- 数据 ----
dc <- read.csv(file.path(BASE, "data", "raw", "D_countries_2023.csv"), check.names = FALSE)
dc <- cn_en_col(dc, c("measure", "measure_name"))
d <- dc[dc$measure_name == "Incidence" & dc$metric_name == "Rate",
        c("location_id", "location_name", "val")]
names(d)[3] <- "ASIR"
cat("[tile] countries:", nrow(d), "\n")

## ---- 质心坐标 ----
cen <- read.csv(file.path(BASE, "data", "raw", "country_centroids.csv"), check.names = FALSE)
norm <- function(x) {
  x <- tolower(trimws(x)); x <- gsub("[^a-z0-9 ]", "", x); gsub("\\s+", " ", x)
}
alias <- c("bolivia plurinational state of" = "bolivia",
           "czechia" = "czech republic",
           "democratic peoples republic of korea" = "north korea",
           "democratic republic of the congo" = "congo drc",
           "iran islamic republic of" = "iran",
           "lao peoples democratic republic" = "laos",
           "micronesia federated states of" = "micronesia",
           "palestine" = "palestinian territory",
           "republic of korea" = "south korea",
           "republic of moldova" = "moldova",
           "syrian arab republic" = "syria",
           "trkiye" = "turkey",
           "united republic of tanzania" = "tanzania",
           "united states of america" = "united states",
           "united states virgin islands" = "us virgin islands",
           "venezuela bolivarian republic of" = "venezuela",
           "viet nam" = "vietnam")
cen$k <- norm(cen$COUNTRY)
d$k  <- norm(d$location_name)
d$k  <- ifelse(d$k %in% names(alias), alias[d$k], d$k)
m <- match(d$k, cen$k)
d$lon <- cen$longitude[m]; d$lat <- cen$latitude[m]
## 台湾不在质心文件中，手工补（不含任何边界含义，仅定位）
tw <- d$location_name == "Taiwan"
d$lon[tw] <- 121.0; d$lat[tw] <- 23.7
cat("[tile] no-centroid:", sum(is.na(d$lon)), "\n")
if (any(is.na(d$lon))) print(d$location_name[is.na(d$lon)])

## ---- 吸附 8 度网格 + 最近空格冲突消解 ----
STEP <- 8
d$gx <- round(d$lon / STEP)
d$gy <- round(d$lat / STEP)
occ <- list()   # key: "gx,gy" -> index
grab <- function(gx, gy) { k <- paste(gx, gy, sep = ","); if (is.null(occ[[k]])) TRUE else FALSE }
take <- function(gx, gy, i) { occ[[paste(gx, gy, sep = ",")]] <<- i }
ord <- order(-d$ASIR)   # 高负担优先占位，避免被小国挤走
for (i in ord) {
  gx <- d$gx[i]; gy <- d$gy[i]
  if (grab(gx, gy)) { take(gx, gy, i); next }
  ## BFS 最近空格（环状搜索，Manhattan 半径 1..15）
  placed <- FALSE
  for (r in 1:15) {
    cand <- expand.grid(dx = -r:r, dy = -r:r)
    cand <- cand[abs(cand$dx) == r | abs(cand$dy) == r, ]
    cand <- cand[order(abs(cand$dy), abs(cand$dx)), ]   # 优先同纬度平移
    for (j in seq_len(nrow(cand))) {
      nx <- gx + cand$dx[j]; ny <- gy + cand$dy[j]
      if (nx < -22 | nx > 23 | ny < -8 | ny > 10) next
      if (grab(nx, ny)) { take(nx, ny, i); d$gx[i] <- nx; d$gy[i] <- ny; placed <- TRUE; break }
    }
    if (placed) break
  }
}
d$row <- d$gy + 8   # 北在上（lat>0 -> gy>0 -> row 更大 -> 图中更高）
cat("[tile] grid cols:", min(d$gx), "..", max(d$gx), " rows:", min(d$row), "..", max(d$row), "\n")

## ---- 绘制 ----
pal <- colorRampPalette(c("#FDEDD0", "#F9C187", "#E8704A", "#B12A2E", "#67001F"))
brk <- pretty(c(0, max(d$ASIR)), n = 6)
lim <- c(0, max(brk))
d$colv <- pal(200)[pmin(199, pmax(1, floor((d$ASIR - lim[1]) / (lim[2] - lim[1]) * 199)) + 1)]

draw_map <- function() {
  par(mar = c(1.2, 0.4, 2.2, 0.4), xpd = TRUE)
  plot(NA, xlim = c(min(d$gx) - 0.8, max(d$gx) + 1.4),
       ylim = c(min(d$row) - 1.4, max(d$row) + 0.6),
       asp = 1, axes = FALSE, xlab = "", ylab = "",
       main = "Syphilis ASIR by country, 2023 (equal-area tile map)")
  for (i in seq_len(nrow(d))) {
    x0 <- d$gx[i] - 0.44; y0 <- d$row[i] - 0.44
    col_i <- if (!is.na(d$colv[i])) d$colv[i] else "grey88"
    rect(x0, y0, x0 + 0.88, y0 + 0.88, col = col_i, border = "white", lwd = 0.5)
  }
  ## 大洲锚点（灰色文字，不含任何边界含义）
  cont <- data.frame(x = c(-12, -7, 2, -2.2, 11, 17.5),
                     y = c(14.0, 7.0, 15.0, 8.0, 14.0, 5.0),
                     lab = c("North\nAmerica", "South\nAmerica", "Europe",
                             "Africa", "Asia", "Oceania"))
  for (j in seq_len(nrow(cont)))
    text(cont$x[j], cont$y[j], cont$lab[j], cex = 0.72, col = "grey45", font = 2)
  ## 中国黑框 + 标签
  ch <- d[d$location_name == "China", ]
  x0 <- ch$gx - 0.44; y0 <- ch$row - 0.44
  rect(x0, y0, x0 + 0.88, y0 + 0.88, col = NA, border = "black", lwd = 2.6)
  text(ch$gx, ch$row - 0.85, "China", cex = 0.95, font = 2)
  ## 最高负担国家标注
  tp <- d[which.max(d$ASIR), ]
  text(tp$gx - 0.2, tp$row - 0.95, "GNQ", cex = 0.7, col = "grey25")
  ## 水平色条图例
  lx <- min(d$gx); ly <- min(d$row) - 1.15; lw <- 22; lh <- 0.8
  for (j in 1:100) {
    rect(lx + (j - 1) / 100 * lw, ly, lx + j / 100 * lw, ly + lh,
         col = pal(100)[j], border = NA)
  }
  text(lx + c(0, 0.5, 1) * lw, ly - 0.5, labels = brk[c(1, length(brk) %/% 2 + 1, length(brk))],
       cex = 0.75, adj = c(0.5, 0.5))
  text(lx + lw / 2, ly + lh + 0.55, "ASIR per 100 000", cex = 0.85, font = 2)
  text(max(d$gx) + 1.4, ly - 0.5,
       "Each square = one country;\nposition approximates geography;\nno borders depicted.",
       cex = 0.62, col = "grey35", adj = c(1, 0.5))
}

mm <- 180
save_pub(file.path(out_f, "Figure12.png"), mm, 0.50 * mm)
draw_map(); add_watermark(); dev.off()
save_pdf(file.path(out_f, "Figure12.pdf"), mm, 0.50 * mm)
draw_map(); add_watermark(); dev.off()
cat("[fig] Figure12 written\n")

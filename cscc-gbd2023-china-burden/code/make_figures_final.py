# -*- coding: utf-8 -*-
"""make_figures_final.py — 最终版 Figures 2-4 一键重生成（管线输出驱动）。

与投稿版完全同款样式；数据不再内嵌，而是从管线输出读取并断言：
  Figure 2 (三因子分解 + 净变化菱形)  <- data/processed/reanalysis_v23/decomposition.csv
  Figure 3 (10 组年龄别发病演化)      <- data/raw/B_age_sex_1990_2023.csv
  Figure 4 (GBD 2021 vs 2023 跨周期)  <- data/processed/reanalysis_v23/crosscycle.csv

输出：
  output/figures/Figure{2,3,4}.{pdf,png}
  并同步 JEADV/04_Figure2.pdf、09_Figure3.pdf、10_Figure4.pdf

Figure 1 由 R 管线 06_figures.R 的 fig1_main() 生成（中国两面板 + 95% UI 带
+ 2011-2016 阴影），不在本脚本范围内。
"""
import csv
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# BASE 解析：兼容两种布局——脚本位于工程根（本地开发）或 code/ 子目录（投稿 zip 解压后）
def _resolve_base():
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (here, os.path.dirname(here)):
        if os.path.isdir(os.path.join(cand, "data", "raw")):
            return cand
    return os.path.dirname(here)

BASE = _resolve_base()
REAN = os.path.join(BASE, "data", "processed", "reanalysis_v23")
OUTFIG = os.path.join(BASE, "output", "figures")
JEADV = os.path.join(BASE, "JEADV")
os.makedirs(OUTFIG, exist_ok=True)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})

# ============================================================
# Figure 2 — 三因子分解（堆叠柱 + 净变化黑菱形）
# ============================================================
EXPECT_INC = [("1990-1995", 967, 663, 1214, -910), ("1995-2000", 2234, 293, 1517, 423),
              ("2000-2005", 4022, 512, 2017, 1493), ("2005-2010", 11269, 927, 3142, 7199),
              ("2010-2015", 59084, 1865, 8493, 48725), ("2015-2020", -49497, 2094, 9119, -60710),
              ("2020-2023", 2658, 192, 3347, -882)]
EXPECT_DEA = [("1990-1995", 475, 271, 563, -359), ("1995-2000", 1039, 122, 770, 148),
              ("2000-2005", 1368, 210, 1003, 154), ("2005-2010", 2607, 342, 1481, 783),
              ("2010-2015", 1404, 366, 2102, -1064), ("2015-2020", 8, 383, 2056, -2431),
              ("2020-2023", 2369, 61, 1483, 825)]

with open(os.path.join(REAN, "decomposition.csv"), encoding="utf-8-sig") as f:
    dec = list(csv.DictReader(f))

def dec_rows(measure):
    rs = [r for r in dec if r["measure"] == measure]
    rs.sort(key=lambda r: r["interval"])
    return [(r["interval"], round(float(r["net"])), round(float(r["growth"])),
             round(float(r["aging"])), round(float(r["epi"]))) for r in rs]

inc_rows, dea_rows = dec_rows("incidence"), dec_rows("deaths")
# 断言：与稿件 eTable 3 / 正文的四舍五入值一致（容差 1 例）
for got, exp, tag in [(inc_rows, EXPECT_INC, "incidence"), (dea_rows, EXPECT_DEA, "deaths")]:
    assert [g[0] for g in got] == [e[0] for e in exp], tag + " interval mismatch"
    for g, e in zip(got, exp):
        for gv, ev in zip(g[1:], e[1:]):
            assert abs(gv - ev) <= 1, f"{tag} {g[0]}: {gv} vs {e[0]} expected {ev}"
print("[assert] Figure 2 data == eTable 3 (7 intervals x 2 measures, tol 1 case)")

labels = [iv.replace("-", "\u2013") for iv in [r[0] for r in inc_rows]]
C_G, C_A, C_E = "#4472C4", "#FFC000", "#C00000"
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2), dpi=300)
for ax, data, title in [(axes[0], inc_rows, "A  Incident cases"),
                        (axes[1], dea_rows, "B  Deaths")]:
    x = np.arange(len(labels))
    growth = np.array([d[2] for d in data], float)
    aging = np.array([d[3] for d in data], float)
    epi = np.array([d[4] for d in data], float)
    net = np.array([d[1] for d in data], float)
    bottoms_p = np.zeros(len(x)); bottoms_n = np.zeros(len(x))
    for series, color in [(growth, C_G), (aging, C_A), (epi, C_E)]:
        posv = np.where(series > 0, series, 0); negv = np.where(series < 0, series, 0)
        ax.bar(x, posv, bottom=bottoms_p, color=color, width=0.62,
               edgecolor="white", linewidth=0.3)
        ax.bar(x, negv, bottom=bottoms_n, color=color, width=0.62,
               edgecolor="white", linewidth=0.3)
        bottoms_p += posv; bottoms_n += negv
    ax.plot(x, net, "D", color="black", markersize=4, label="Net change")
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=6.5)
    ax.set_title(title, fontsize=8.5, loc="left")
    ax.set_ylabel("Contribution (cases)" if title.startswith("A") else "Contribution (deaths)",
                  fontsize=8)
    ax.tick_params(labelsize=7)
# 三因素 + 净变化统一图例（蓝=人口增长 / 黄=人口老龄化 / 红=流行病学变化）
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
handles = [Patch(fc=C_G, label="Population growth"),
           Patch(fc=C_A, label="Population aging"),
           Patch(fc=C_E, label="Epidemiological change"),
           Line2D([0], [0], marker="D", color="black", linestyle="none",
                  markersize=4.5, label="Net change")]
axes[0].legend(handles=handles, loc="upper left", fontsize=6, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(OUTFIG, "Figure2.pdf"))
fig.savefig(os.path.join(OUTFIG, "Figure2.png"), dpi=300)
plt.close(fig)
if os.path.isdir(JEADV):  # 仅本地工程存在该目录时同步；投稿 zip 环境跳过
    shutil.copy2(os.path.join(OUTFIG, "Figure2.pdf"), os.path.join(JEADV, "04_Figure2.pdf"))
print("Figure2 done (stacked bars + net-change diamonds)")

# ============================================================
# Figure 3 — 10 组年龄别发病演化（图例含 1990→2023 相对变化 %）
# ============================================================
with open(os.path.join(BASE, "data", "raw", "B_age_sex_1990_2023.csv"), encoding="utf-8-sig") as f:
    rows = [r for r in csv.DictReader(f)
            if r["location_name"] == "中国" and r["measure_name"] == "发病率"
            and r["metric_name"] == "率" and r["sex_name"] == "合计"]
d = {(r["age_name"], int(r["year"])): float(r["val"]) for r in rows}
years = sorted(set(int(r["year"]) for r in rows))

GROUPS = ["25-29岁", "35-39岁", "45-49岁", "50-54岁", "55-59岁",
          "60-64岁", "65-69岁", "75-79岁", "85-89岁", ">95岁"]
GLAB = ["25\u201329", "35\u201339", "45\u201349", "50\u201354", "55\u201359",
        "60\u201364", "65\u201369", "75\u201379", "85\u201389", "\u226595"]
REL = {g: 100 * (d[(g, 2023)] / d[(g, 1990)] - 1) for g in GROUPS}
# 断言：与正文一致 — 最大相对增幅在 55–59 岁（+60%），60–64 岁 +51%
imax = max(REL, key=REL.get)
assert imax == "55-59岁" and round(REL[imax]) == 60, REL[imax]
assert round(REL["60-64岁"]) == 51, REL["60-64岁"]
print("[assert] Fig3 largest relative increase: 55-59 (+%.0f%%); 60-64 (+%.0f%%)"
      % (REL[imax], REL["60-64岁"]))

colors = plt.cm.YlOrRd(np.linspace(0.30, 0.95, len(GROUPS)))
fig, ax = plt.subplots(figsize=(5.8, 3.6), dpi=300)
for lab, col, g in zip(GLAB, colors, GROUPS):
    ys = [d[(g, y)] for y in years]
    sign = "+" if REL[g] >= 0 else "\u2212"
    ax.plot(years, ys, color=col, lw=1.4, label=f"{lab} ({sign}{abs(REL[g]):.0f}%)")
ax.set_xlabel("Year")
ax.set_ylabel("Incidence rate per 100,000")
ax.set_xlim(1990, 2023)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, fontsize=6.5, handlelength=1.6, loc="upper left",
          title="Age group, years (change 1990\u20132023)", title_fontsize=6.5)
ax.text(0.02, 0.02, "China, both sexes", transform=ax.transAxes, fontsize=7, style="italic")
fig.tight_layout()
fig.savefig(os.path.join(OUTFIG, "Figure3.pdf"))
fig.savefig(os.path.join(OUTFIG, "Figure3.png"), dpi=300)
plt.close(fig)
if os.path.isdir(JEADV):  # 仅本地工程存在该目录时同步；投稿 zip 环境跳过
    shutil.copy2(os.path.join(OUTFIG, "Figure3.pdf"), os.path.join(JEADV, "09_Figure3.pdf"))
print("Figure3 done (10 age groups, rel% legend)")

# ============================================================
# Figure 4 — GBD 2021 vs GBD 2023 跨周期（5 个共同报告年）
# ============================================================
with open(os.path.join(REAN, "crosscycle.csv"), encoding="utf-8-sig") as f:
    cc = list(csv.DictReader(f))

def series(measure):
    rs = sorted([r for r in cc if r["measure"] == measure], key=lambda r: int(r["year"]))
    return ([int(r["year"]) for r in rs],
            [float(r["rate2021"]) for r in rs],
            [float(r["rate2023"]) for r in rs])

C21, C23 = "#4472C4", "#C00000"
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2), dpi=300)
for ax, meas, title in [(axes[0], "Incidence", "A  Incidence"),
                        (axes[1], "Prevalence", "B  Prevalence")]:
    yrs, s21, s23 = series(meas)
    assert yrs == [1990, 2010, 2015, 2019, 2021], yrs   # 五个共同报告年份
    ax.axvspan(2011, 2016, color="#D9D9D9", alpha=0.45, lw=0, zorder=0)
    ax.plot(yrs, s21, color=C21, lw=1.4, marker="o", ms=3.5, label="GBD 2021 cycle")
    ax.plot(yrs, s23, color=C23, lw=1.4, marker="s", ms=3.5, label="GBD 2023 cycle")
    ax.set_title(title, loc="left", fontsize=8)
    ax.set_xlabel("Year")
    ax.set_ylabel("Crude rate per 100,000")
    ax.set_xticks(yrs)
    ax.set_xticklabels([str(y) for y in yrs], fontsize=7, rotation=40, ha="right")
    ax.spines[["top", "right"]].set_visible(False)
axes[0].text(2013.5, axes[0].get_ylim()[1] * 0.94, "2011\u20132016", ha="center", va="top",
             fontsize=6.5, color="#595959")
axes[0].legend(frameon=False, fontsize=7, loc="upper left")
fig.tight_layout()
fig.savefig(os.path.join(OUTFIG, "Figure4.pdf"))
fig.savefig(os.path.join(OUTFIG, "Figure4.png"), dpi=300)
plt.close(fig)
if os.path.isdir(JEADV):  # 仅本地工程存在该目录时同步；投稿 zip 环境跳过
    shutil.copy2(os.path.join(OUTFIG, "Figure4.pdf"), os.path.join(JEADV, "10_Figure4.pdf"))
print("Figure4 done (GBD 2021 vs 2023, five common reporting years)")

print("make_figures_final.py: all final figures regenerated")

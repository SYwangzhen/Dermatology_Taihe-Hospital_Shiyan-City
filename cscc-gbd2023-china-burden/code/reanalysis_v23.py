# -*- coding: utf-8 -*-
"""Re-analysis v2.3: direct-population decomposition, cross-cycle table, YLL/YLD split, stats."""
import zipfile, csv, io, os, json, math

# BASE 解析：兼容两种布局——脚本位于工程根（本地开发）或 code/ 子目录（投稿 zip 解压后）
def _resolve_base():
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (here, os.path.dirname(here)):
        if os.path.isdir(os.path.join(cand, "data", "raw")):
            return cand
    return os.path.dirname(here)

BASE = _resolve_base()
RAW = os.path.join(BASE, "data", "raw")
OUT = os.path.join(BASE, "data", "processed", "reanalysis_v23")
os.makedirs(OUT, exist_ok=True)

def load(z):
    zf = zipfile.ZipFile(os.path.join(RAW, z))
    with zf.open(zf.namelist()[0]) as fh:
        return list(csv.DictReader(io.TextIOWrapper(fh, "utf-8")))

cnt  = load("IHME-GBD_2023_DATA-fc1ffd6d-1.zip")   # counts+rates by age, Chinese labels
pop  = load("IHME-GBD_2023_DATA-670c8efe-1.zip")   # population
g21  = load("IHME-GBD_2021_DATA-9f7ebc48-1.zip")   # GBD2021 SCC
yll  = load("IHME-GBD_2023_DATA-71a8ec3f-1.zip")   # YLL/YLD
asr  = load("IHME-GBD_2023_DATA-cbf696fc-1.zip")   # ASR by sex

# ---- age label map (Chinese -> English) ----
zh_groups = sorted(set(r["age_name"] for r in cnt) - {"年龄标准化"})
def zh2en(z):
    if z == "5岁以下": return "<5 years"
    if z.startswith("<"): return "<5 years"
    if z.startswith(">") or z == "95+岁": return "95+ years"
    return z.replace("岁", "") + " years"
AGE_MAP = {z: zh2en(z) for z in zh_groups}
assert all(AGE_MAP.values()), AGE_MAP
def sort_key(z):
    e = AGE_MAP[z]
    if e == "<5 years": return 0
    if e == "95+ years": return 100
    return int(e.split("-")[0])
AGES = [AGE_MAP[z] for z in sorted(zh_groups, key=sort_key)]
YEARS = list(range(1990, 2024))
INTERVALS = [(1990, 1995), (1995, 2000), (2000, 2005), (2005, 2010), (2010, 2015), (2015, 2020), (2020, 2023)]

# ---- quick accessors (完整筛选 + 唯一性断言，不依赖文件行序) ----
def unique_val(rows, **filters):
    """按全部给定字段精确筛选，断言恰好一条匹配后返回 val（防静默取错行）。"""
    hits = [r for r in rows
            if all((r[k] == v if not isinstance(v, (list, tuple, set))
                    else r[k] in v) for k, v in filters.items())]
    assert len(hits) == 1, f"expected exactly 1 row for {filters}, got {len(hits)}"
    return float(hits[0]["val"])

def get_cnt(meas_zh, sex, year):
    d = {}
    for r in cnt:
        if (r["location_name"] == "中国" and r["measure_name"] == meas_zh
            and r["sex_name"] == sex and r["metric_name"] == "数量"
            and int(r["year"]) == year and r["age_name"] in AGE_MAP):
            key = AGE_MAP[r["age_name"]]
            assert key not in d, f"duplicate count row: {meas_zh} {sex} {year} {key}"
            d[key] = float(r["val"])
    return d

def get_pop(sex, year):
    d = {}
    for r in pop:
        if (r["location_name"] == "China" and r["sex_name"] == sex
                and int(r["year"]) == year and r["age_name"] != "All ages"):
            key = r["age_name"]
            assert key not in d, f"duplicate population row: {sex} {year} {key}"
            d[key] = float(r["val"])
    return d

def das_gupta(N0a, N1a, C0a, C1a):
    """3-factor Das Gupta: N (pop), s (age share), r (age-specific rate). Exact pair decomposition."""
    ages = [a for a in N0a if N0a.get(a, 0) > 0 and N1a.get(a, 0) > 0]
    N0, N1 = sum(N0a[a] for a in ages), sum(N1a[a] for a in ages)
    s0 = {a: N0a[a] / N0 for a in ages}; s1 = {a: N1a[a] / N1 for a in ages}
    r0 = {a: C0a.get(a, 0.0) / N0a[a] for a in ages}
    r1 = {a: C1a.get(a, 0.0) / N1a[a] for a in ages}
    M0, M1 = sum(s0[a] * r0[a] for a in ages), sum(s1[a] * r1[a] for a in ages)
    M01 = sum(s0[a] * r1[a] for a in ages); M10 = sum(s1[a] * r0[a] for a in ages)
    X0, X1 = N0 * M0, N1 * M1
    eN = (N1 - N0) / 6 * (2 * M0 + M01 + M10 + 2 * M1)
    eS = sum((s1[a] - s0[a]) / 6 * (2 * N0 * r0[a] + N0 * r1[a] + N1 * r0[a] + 2 * N1 * r1[a]) for a in ages)
    eR = sum((r1[a] - r0[a]) / 6 * (2 * N0 * s0[a] + N0 * s1[a] + N1 * s0[a] + 2 * N1 * s1[a]) for a in ages)
    return {"net": X1 - X0, "growth": eN, "aging": eS, "epi": eR,
            "check": (eN + eS + eR) - (X1 - X0)}

results = {}
# ---- 1) decomposition: incidence & deaths, China, Both sexes ----
for meas_zh, key in [("发病率", "incidence"), ("死亡", "deaths")]:
    total = {"net": 0, "growth": 0, "aging": 0, "epi": 0}
    rows = []
    for t0, t1 in INTERVALS:
        g = das_gupta(get_pop("Both", t0), get_pop("Both", t1),
                      get_cnt(meas_zh, "合计", t0), get_cnt(meas_zh, "合计", t1))
        rows.append(g)
        for k in total: total[k] += g[k]
    # direct 1990->2023
    direct = das_gupta(get_pop("Both", 1990), get_pop("Both", 2023),
                       get_cnt(meas_zh, "合计", 1990), get_cnt(meas_zh, "合计", 2023))
    results[key] = {"intervals": rows, "sum": total, "direct_1990_2023": direct}
    print(f"== {key} 分解（直接人口，7区间求和 vs 直接1990-2023）")
    print("  区间求和: net=%+.0f growth=%+.0f aging=%+.0f epi=%+.0f (残差 %.2e)" %
          (total["net"], total["growth"], total["aging"], total["epi"], total["net"] - total["growth"] - total["aging"] - total["epi"]))
    print("  直接分解: net=%+.0f growth=%+.0f aging=%+.0f epi=%+.0f" %
          (direct["net"], direct["growth"], direct["aging"], direct["epi"]))
    for (t0, t1), g in zip(INTERVALS, rows):
        print(f"    {t0}-{t1}: net={g['net']:+9.0f} growth={g['growth']:+9.0f} aging={g['aging']:+9.0f} epi={g['epi']:+9.0f}")

# ---- 2) cross-cycle: GBD2021 vs GBD2023, China, All ages, Both, crude rate ----
def crude_2023(meas_zh, year):
    ca = get_cnt(meas_zh, "合计", year)
    pa = get_pop("Both", year)
    N = sum(pa.values())
    C = sum(ca.values())
    return C, C / N * 1e5
print("\n== 跨周期对照（中国，全年龄，男女合计，粗率/10万）")
print(f"{'年份':>6} {'指标':<12} {'GBD2021数':>12} {'GBD2023数':>12} {'数差%':>7} {'GBD2021率':>9} {'GBD2023率':>9} {'率差%':>7}")
xrows = []
for meas_zh, meas_en in [("发病率", "Incidence"), ("患病率", "Prevalence"), ("死亡", "Deaths"), ("伤残调整生命年", "DALYs")]:
    g21m = [m for m in ["Incidence", "Prevalence", "Deaths", "DALYs (Disability-Adjusted Life Years)"] if m.startswith(meas_en.split(" ")[0])][0]
    for yr in [1990, 2010, 2015, 2019, 2021]:
        # GBD2021：显式限定 China × All ages × Both（Number 与 Rate 各取一条）
        v21 = unique_val(g21, location_name="China", sex_name="Both", age_name="All ages",
                         measure_name=g21m, metric_name="Number", year=str(yr))
        r21 = unique_val(g21, location_name="China", sex_name="Both", age_name="All ages",
                         measure_name=g21m, metric_name="Rate", year=str(yr))
        c23, r23 = crude_2023(meas_zh, yr)
        d = (c23 / v21 - 1) * 100 if v21 else float("nan")
        dr = (r23 / r21 - 1) * 100 if r21 else float("nan")
        xrows.append({"year": yr, "measure": meas_en, "n2021": v21, "n2023": c23, "n_diff_pct": d,
                      "rate2021": r21, "rate2023": r23, "rate_diff_pct": dr})
        print(f"{yr:>6} {meas_en:<12} {v21:>12,.0f} {c23:>12,.0f} {d:>+6.1f}% {r21:>9.3f} {r23:>9.3f} {dr:>+6.1f}%")

# hump check: yearly crude ASIR 2021 vs 2023
print("\n-- 发病粗率逐年比值（2023轮 / 2021轮）--")
hump = []
for yr in range(1990, 2022):
    v21 = unique_val(g21, location_name="China", sex_name="Both", age_name="All ages",
                     measure_name="Incidence", metric_name="Rate", year=str(yr))
    c23, r23 = crude_2023("发病率", yr)
    hump.append((yr, r23 / v21))
print(" ".join(f"{yr}:{ratio:.2f}" for yr, ratio in hump))

# ---- 3) YLL/YLD ----
print("\n== YLL/YLD 拆解（中国，男女合计）")
def ym(meas, metric, year):
    # 显式限定 China × Both × All ages，唯一匹配
    return unique_val(yll, location_name="China", sex_name="Both", age_name="All ages",
                      measure_name=meas, metric_name=metric, year=str(year))
yres = {}
for meas in ["YLLs (Years of Life Lost)", "YLDs (Years Lived with Disability)"]:
    n0, n1 = ym(meas, "Number", 1990), ym(meas, "Number", 2023)
    r0, r1 = ym(meas, "Rate", 1990), ym(meas, "Rate", 2023)
    # 端点对数年增长率（×100）：介于两点间的平均对数变化，非全期回归 EAPC，
    # 亦非标准 CAGR（标准端点 CAGR = 100*(exp(ln(r1/r0)/33)-1)，数值上与本式不同）
    endpoint_log_growth = (math.log(r1 / r0) / 33) * 100
    yres[meas.split(" ")[0]] = {"n1990": n0, "n2023": n1, "rate1990": r0, "rate2023": r1,
                                "endpoint_log_growth_pct": endpoint_log_growth}
    print(f"  {meas.split(' ')[0]}: 1990 n={n0:,.0f} rate={r0:.2f} -> 2023 n={n1:,.0f} rate={r1:.2f} "
          f"(端点对数年增长率 {endpoint_log_growth:+.2f}%)")
d_n = yres["YLLs"]["n2023"] - yres["YLLs"]["n1990"], yres["YLDs"]["n2023"] - yres["YLDs"]["n1990"]
net = d_n[0] + d_n[1]
print(f"  DALY(=YLL+YLD) 变化: YLL 贡献 {d_n[0]:,.0f} ({d_n[0]/net*100:.0f}%), YLD 贡献 {d_n[1]:,.0f} ({d_n[1]/net*100:.0f}%)")

# ---- 4) stats: sex EAPC z-test + DW ----
# 性别比较为近似探索性分析：由各自 95% CI 反推 SE 后求差值 z。
# 更严格的尺度是把 EAPC 转回对数斜率 beta = log(1 + EAPC/100) 再比较
# （两尺度 z 值接近，结论不变）；注意男女 GBD 序列非独立、此处默认
# 协方差为 0、且未校正残差自相关——正文相应表述限定为 exploratory。
def ztest(m1, lo1, hi1, m0, lo0, hi0):
    # β 尺度（log(1+EAPC/100)）：SE_beta = SE_eapc / (100 + EAPC)
    b1, b0 = math.log(1 + m1 / 100), math.log(1 + m0 / 100)
    se1 = (hi1 - lo1) / 3.92 / (100 + m1)
    se0 = (hi0 - lo0) / 3.92 / (100 + m0)
    se = math.sqrt(se1**2 + se0**2)
    z = (b1 - b0) / se
    from math import erf, sqrt
    p = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    return z, p
print("\n== 性别 EAPC 差异 z 检验（β=log(1+EAPC/100) 尺度，探索性）")
for lab, (m1, l1, h1), (m0, l0, h0) in [
    ("发病率 男vs女", (3.36, 1.91, 4.84), (1.87, 1.29, 2.45)),
    ("患病率 男vs女", (4.86, 3.06, 6.69), (2.65, 1.90, 3.41))]:
    z, p = ztest(m1, l1, h1, m0, l0, h0)
    print(f"  {lab}: Δ={m1-m0:+.2f} z={z:.2f} P={p:.3f}")

# DW on ln(ASIR) regression residuals, Both sexes（显式限定年龄标准化 + 唯一性）
asir = sorted((int(r["year"]), float(r["val"])) for r in asr
              if r["location_name"] == "中国" and r["measure_name"] == "发病率"
              and r["sex_name"] == "合计" and r["metric_name"] == "率"
              and r["age_name"] == "年龄标准化")
years_seen = [y for y, _ in asir]
assert len(years_seen) == len(set(years_seen)), "duplicate ASIR rows"
assert set(years_seen) == set(range(1990, 2024)), "incomplete ASIR series"
n = len(asir); xs = [y for y, _ in asir]; ys = [math.log(v) for _, v in asir]
mx, my = sum(xs) / n, sum(ys) / n
b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
eapc = (math.exp(b) - 1) * 100
resid = [y - (my + b * (x - mx)) for x, y in zip(xs, ys)]
dw = sum((resid[i] - resid[i-1])**2 for i in range(1, n)) / sum(r**2 for r in resid)
print(f"\n== 全周期 EAPC 复算: {eapc:+.2f}%/年 | Durbin-Watson = {dw:.3f}")

# save outputs
import csv as csvw
with open(os.path.join(OUT, "decomposition.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csvw.writer(f); w.writerow(["measure", "interval", "net", "growth", "aging", "epi"])
    for key in ["incidence", "deaths"]:
        for (t0, t1), g in zip(INTERVALS, results[key]["intervals"]):
            w.writerow([key, f"{t0}-{t1}", round(g["net"], 1), round(g["growth"], 1), round(g["aging"], 1), round(g["epi"], 1)])
with open(os.path.join(OUT, "crosscycle.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csvw.DictWriter(f, ["year", "measure", "n2021", "n2023", "n_diff_pct", "rate2021", "rate2023", "rate_diff_pct"]); w.writeheader()
    w.writerows(xrows)
with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
    json.dump({"decomposition": results, "yll_yld": yres, "eapc_check": eapc, "dw": dw}, f, indent=1)
print("\n输出已存:", OUT)

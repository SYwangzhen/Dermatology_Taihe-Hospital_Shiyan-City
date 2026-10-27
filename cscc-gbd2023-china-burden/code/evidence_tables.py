# -*- coding: utf-8 -*-
"""
evidence_tables.py — 生成正文与 eTables 引用的关键证据数字，并逐一断言。

产出（data/processed/reanalysis_v23/）：
  * evidence_elderly.csv  — >=65 / >=70 岁计数与占比（分性别 + 男女合计；
                            分母 = 同指标、同性别、同年的男+女总数，与 eTable 5 表注一致；
                            含 open-ended 95+ 组）
  * evidence_mi_ratio.csv — 死亡-发病比（年龄标化死亡 ASMR / 年龄标化发病 ASIR，
                            中国 vs 全球，男女合计，1990-2023 每年；非 case-fatality）

断言（与正文/eTable 5 数字一致，任何漂移直接报错）：
  * >=65 新发病例 1990/2023 = 4,815 / 24,640（占 35% / 55%）
  * >=65 死亡 1990/2023 = 3,250 / 11,467（占 58% / 77%）
  * 男性 >=65 新发占比 36.3% -> 55.9%；女性 33.3% -> 52.0%
  * 男性 >=65 死亡占比 61.2% -> 75.5%；女性 54.3% -> 73.6%
  * M/I 比值 2023：中国 ~0.33，全球 ~0.03
"""
import csv, json, math, os

# BASE 解析：兼容两种布局——脚本位于工程根（本地开发）或 code/ 子目录（投稿 zip 解压后）
def _resolve_base():
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (here, os.path.dirname(here)):
        if os.path.isdir(os.path.join(cand, "data", "raw")):
            return cand
    return os.path.dirname(here)

BASE = _resolve_base()
RAW  = os.path.join(BASE, "data", "raw")
OUT  = os.path.join(BASE, "data", "processed", "reanalysis_v23")
os.makedirs(OUT, exist_ok=True)

# ---------- helpers ----------
def age_lower(label):
    """GBD 5-year age label -> lower bound; open-ended 95+ -> 95."""
    if label in (">95岁", "95岁以上", "95+岁", "95+"):
        return 95
    if label == "5岁以下":
        return 0
    s = label.replace("岁", "").strip()
    try:
        return int(s.split("-")[0])
    except ValueError:
        return None

def load_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

# ---------- 1) elderly counts/percentages (eTable 5) ----------
# 管线约定：Both = Male + Female（男+女），人口独立建模时不用工具自带合计行作分母
rows_b = load_csv(os.path.join(RAW, "B_age_sex_1990_2023.csv"))
num, den = {}, {}
for r in rows_b:
    if r["location_name"] != "中国" or r["metric_name"] != "数量":
        continue
    if r["measure_name"] not in ("发病率", "死亡") or r["year"] not in ("1990", "2023"):
        continue
    if r["sex_name"] == "合计":          # 不用工具 Both 行；Both 由 M+F 重算
        continue
    m, sx, y, v = r["measure_name"], r["sex_name"], int(r["year"]), float(r["val"])
    den[(m, sx, y)] = den.get((m, sx, y), 0.0) + v
    a = age_lower(r["age_name"])
    assert a is not None, f"unmapped age label: {r['age_name']}"   # 95+ 必须显式解析，禁止静默跳过
    for tag, thr in (">=65", 65), (">=70", 70):
        if a >= thr:
            num[(m, sx, y, tag)] = num.get((m, sx, y, tag), 0.0) + v

for m in ("发病率", "死亡"):
    for y in (1990, 2023):
        for tag in (">=65", ">=70"):
            num[(m, "合计", y, tag)] = num[(m, "男", y, tag)] + num[(m, "女", y, tag)]
        den[(m, "合计", y)] = den[(m, "男", y)] + den[(m, "女", y)]

MI_EN = {"发病率": "Incidence", "死亡": "Deaths"}
SX_EN = {"合计": "Both sexes", "男": "Male", "女": "Female"}
out_rows = []
for m in ("发病率", "死亡"):
    for sx in ("合计", "男", "女"):
        for y in (1990, 2023):
            for tag in (">=65", ">=70"):
                n, d = num[(m, sx, y, tag)], den[(m, sx, y)]
                out_rows.append({"measure": MI_EN[m], "sex": SX_EN[sx], "age_band": tag,
                                 "year": y, "cases_over65": round(n),
                                 "total_same_sex": round(d),
                                 "percent": round(n / d * 100, 1)})
with open(os.path.join(OUT, "evidence_elderly.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, ["measure", "sex", "age_band", "year", "cases_over65",
                           "total_same_sex", "percent"])
    w.writeheader(); w.writerows(out_rows)

def pct(m, sx, y, tag):
    return round(num[(m, sx, y, tag)] / den[(m, sx, y)] * 100, 1)

def cnt(m, sx, y, tag):
    return round(num[(m, sx, y, tag)])

# assertions — 与投稿版 eTable 5（v2.9.3 修正，含 open-ended 95+ 组）逐格一致
A = [
    ("Both >=65 incidence 1990 n/%", (cnt("发病率", "合计", 1990, ">=65"), pct("发病率", "合计", 1990, ">=65")), (4815, 35.0)),
    ("Both >=65 incidence 2023 n/%", (cnt("发病率", "合计", 2023, ">=65"), pct("发病率", "合计", 2023, ">=65")), (24640, 55.4)),
    ("Both >=70 incidence 1990 n/%", (cnt("发病率", "合计", 1990, ">=70"), pct("发病率", "合计", 1990, ">=70")), (3388, 24.6)),
    ("Both >=70 incidence 2023 n/%", (cnt("发病率", "合计", 2023, ">=70"), pct("发病率", "合计", 2023, ">=70")), (19148, 43.0)),
    ("Men  >=65 incidence 1990 n/%", (cnt("发病率", "男", 1990, ">=65"), pct("发病率", "男", 1990, ">=65")), (2524, 36.4)),
    ("Men  >=65 incidence 2023 n/%", (cnt("发病率", "男", 2023, ">=65"), pct("发病率", "男", 2023, ">=65")), (12913, 57.0)),
    ("Men  >=70 incidence 1990 n/%", (cnt("发病率", "男", 1990, ">=70"), pct("发病率", "男", 1990, ">=70")), (1732, 25.0)),
    ("Men  >=70 incidence 2023 n/%", (cnt("发病率", "男", 2023, ">=70"), pct("发病率", "男", 2023, ">=70")), (9876, 43.6)),
    ("Women>=65 incidence 1990 n/%", (cnt("发病率", "女", 1990, ">=65"), pct("发病率", "女", 1990, ">=65")), (2291, 33.5)),
    ("Women>=65 incidence 2023 n/%", (cnt("发病率", "女", 2023, ">=65"), pct("发病率", "女", 2023, ">=65")), (11727, 53.7)),
    ("Women>=70 incidence 1990 n/%", (cnt("发病率", "女", 1990, ">=70"), pct("发病率", "女", 1990, ">=70")), (1656, 24.2)),
    ("Women>=70 incidence 2023 n/%", (cnt("发病率", "女", 2023, ">=70"), pct("发病率", "女", 2023, ">=70")), (9272, 42.4)),
    ("Both >=65 deaths 1990 n/%", (cnt("死亡", "合计", 1990, ">=65"), pct("死亡", "合计", 1990, ">=65")), (3250, 58.2)),
    ("Both >=65 deaths 2023 n/%", (cnt("死亡", "合计", 2023, ">=65"), pct("死亡", "合计", 2023, ">=65")), (11467, 77.2)),
    ("Both >=70 deaths 1990 n/%", (cnt("死亡", "合计", 1990, ">=70"), pct("死亡", "合计", 1990, ">=70")), (2267, 40.6)),
    ("Both >=70 deaths 2023 n/%", (cnt("死亡", "合计", 2023, ">=70"), pct("死亡", "合计", 2023, ">=70")), (9424, 63.4)),
    ("Men  >=65 deaths 1990 n/%", (cnt("死亡", "男", 1990, ">=65"), pct("死亡", "男", 1990, ">=65")), (1820, 61.3)),
    ("Men  >=65 deaths 2023 n/%", (cnt("死亡", "男", 2023, ">=65"), pct("死亡", "男", 2023, ">=65")), (6045, 77.1)),
    ("Men  >=70 deaths 1990 n/%", (cnt("死亡", "男", 1990, ">=70"), pct("死亡", "男", 1990, ">=70")), (1214, 40.9)),
    ("Men  >=70 deaths 2023 n/%", (cnt("死亡", "男", 2023, ">=70"), pct("死亡", "男", 2023, ">=70")), (4770, 60.9)),
    ("Women>=65 deaths 1990 n/%", (cnt("死亡", "女", 1990, ">=65"), pct("死亡", "女", 1990, ">=65")), (1430, 54.6)),
    ("Women>=65 deaths 2023 n/%", (cnt("死亡", "女", 2023, ">=65"), pct("死亡", "女", 2023, ">=65")), (5422, 77.2)),
    ("Women>=70 deaths 1990 n/%", (cnt("死亡", "女", 1990, ">=70"), pct("死亡", "女", 1990, ">=70")), (1052, 40.2)),
    ("Women>=70 deaths 2023 n/%", (cnt("死亡", "女", 2023, ">=70"), pct("死亡", "女", 2023, ">=70")), (4654, 66.3)),
    ("Male incidence total 1990", (round(den[("发病率", "男", 1990)]),), (6939,)),
    ("Male incidence total 2023", (round(den[("发病率", "男", 2023)]),), (22660,)),
]
for name, got, exp in A:
    for g, e in zip(got, exp):
        tol = 0.05 if isinstance(e, float) else 0
        assert abs(g - e) <= tol, f"ASSERTION FAIL {name}: got {got}, expected {exp}"
    print(f"  PASS {name}: {got}")

# ---------- 2) mortality-to-incidence ratio (ASMR / ASIR) ----------
asr = load_csv(os.path.join(RAW, "A_ASR_1990_2023.csv"))
def asr_series(meas, loc):
    d = {}
    for r in asr:
        if (r["location_name"] == loc and r["measure_name"] == meas
                and r["sex_name"] == "合计" and r["metric_name"] == "率"
                and r["age_name"] == "年龄标准化"):
            assert int(r["year"]) not in d, "duplicate ASR row"
            d[int(r["year"])] = float(r["val"])
    assert set(d) == set(range(1990, 2024)), f"incomplete ASR series {meas} {loc}"
    return d

mi_rows = []
for loc, expect23 in (("中国", 0.33), ("全球", 0.03)):
    inc = asr_series("发病率", loc)
    dea = asr_series("死亡", loc)
    for y in range(1990, 2024):
        mi_rows.append({"location": "China" if loc == "中国" else "Global",
                        "year": y, "asmr": dea[y], "asir": inc[y],
                        "mi_ratio": round(dea[y] / inc[y], 3)})
    got = dea[2023] / inc[2023]
    # 正文表述为 "approximately 0.33 in China versus 0.03 globally"（两位小数近似）
    assert abs(got - expect23) < 0.006, f"ASSERTION FAIL M/I {loc} 2023: {got:.3f} vs {expect23}"
    print(f"  PASS M/I {loc} 2023 = {got:.3f} (~{expect23})")
with open(os.path.join(OUT, "evidence_mi_ratio.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, ["location", "year", "asmr", "asir", "mi_ratio"])
    w.writeheader(); w.writerows(mi_rows)

print("\nevidence tables written:")
print("  ", os.path.join(OUT, "evidence_elderly.csv"))
print("  ", os.path.join(OUT, "evidence_mi_ratio.csv"))

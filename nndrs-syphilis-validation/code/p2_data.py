# -*- coding: utf-8 -*-
"""
P2 数据底座：
  1) 从 GBD 2023 原始导出抽取中国 1990–2023 发病数 / ASIR / 死亡 / DALY（含 <5 岁）
  2) 由 NNDRS-A 系列（报告发病率）反推历年人口，补齐 2018（线性内插），用于分型率计算
  3) 组装跨系统比值序列（GBD ÷ NNDRS-A / B1 / B2；B1÷A；B2÷B1）
  4) 分段（joinpoint）回归：对数线性、断点整数年、BIC 选 0/1/2 个断点、每段≥3 点

输入：../data/raw/A_ASR_1990_2023.csv, ../data/raw/B_age_sex_1990_2023.csv,
      raw/NNDRS_syphilis_annual.csv
输出：processed/gbd_incidence_series.csv, processed/china_population_derived.csv,
      processed/p2_ratio_series.csv, processed/joinpoint_p2.csv
"""
import csv, os, math, itertools, sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, 'raw')
PROC = os.path.join(BASE, 'processed')
D_RAW = os.path.join(BASE, 'raw')     # GBD 2023 extracts, downloaded (not redistributed)
os.makedirs(PROC, exist_ok=True)

# ───────────────────────────────────────────────────────────────
# 1. GBD 抽取
# ───────────────────────────────────────────────────────────────
for _f in ('A_ASR_1990_2023.csv', 'B_age_sex_1990_2023.csv'):
    if not os.path.exists(os.path.join(D_RAW, _f)):
        sys.exit('Missing GBD 2023 extract raw/%s.\n'
                 'Download it from the GBD Results Tool (see docs/gbd_query.md) and place '
                 'it in raw/.\nThe shipped data/, raw/, processed/ and tables/ files do not '
                 'need this step.' % _f)

asr = pd.read_csv(os.path.join(D_RAW, 'A_ASR_1990_2023.csv'))
num = pd.read_csv(os.path.join(D_RAW, 'B_age_sex_1990_2023.csv'))

def pick_num(measure, sex, age='All ages', year=None):
    q = num[(num.location_name == 'China') & (num.measure_name == measure) &
            (num.sex_name == sex) & (num.age_name == age) & (num.metric_name == 'Number')]
    if year is not None:
        q = q[q.year == year]
    return q.set_index('year')['val']

def pick_rate(measure, sex):
    q = asr[(asr.location_name == 'China') & (asr.measure_name == measure) &
            (asr.sex_name == sex) & (asr.age_name == 'Age-standardized')]
    return q.set_index('year')['val']

rows = []
for y in range(1990, 2024):
    rows.append({
        'year': y,
        'gbd_cases_both': pick_num('Incidence', 'Both', year=y).get(y),
        'gbd_cases_male': pick_num('Incidence', 'Male', year=y).get(y),
        'gbd_cases_female': pick_num('Incidence', 'Female', year=y).get(y),
        'gbd_asir_both': pick_rate('Incidence', 'Both').get(y),
        'gbd_asir_male': pick_rate('Incidence', 'Male').get(y),
        'gbd_asir_female': pick_rate('Incidence', 'Female').get(y),
        'gbd_prev_cases_both': pick_num('Prevalence', 'Both', year=y).get(y),
        'gbd_deaths_both': pick_num('Deaths', 'Both', year=y).get(y),
        'gbd_daly_both': pick_num('DALYs (Disability-Adjusted Life Years)', 'Both', year=y).get(y),
        'gbd_u5_deaths_both': pick_num('Deaths', 'Both', age='<5 years', year=y).get(y),
        'gbd_u5_daly_both': pick_num('DALYs (Disability-Adjusted Life Years)', 'Both', age='<5 years', year=y).get(y),
    })
gbd = pd.DataFrame(rows)
# 一致性断言：明细年龄组合计 == All ages（Both）
_chk = num[(num.location_name == 'China') & (num.measure_name == 'Incidence') &
           (num.metric_name == 'Number') & (num.sex_name == 'Both') & (num.year == 2023)]
_detail = _chk[_chk.age_name != 'All ages'].val.sum()
_all = _chk[_chk.age_name == 'All ages'].val.iloc[0]
assert abs(_detail - _all) / _all < 0.005, f'GBD 年龄明细与 All ages 不一致: {_detail} vs {_all}'
gbd.to_csv(os.path.join(PROC, 'gbd_incidence_series.csv'), index=False, encoding='utf-8-sig')
print('GBD 序列 ->', gbd.shape, '| 2023 both =', round(gbd.loc[gbd.year == 2023, 'gbd_cases_both'].iloc[0]))

# ───────────────────────────────────────────────────────────────
# 2. NNDRS 年度序列（A / B1 / B2）
# ───────────────────────────────────────────────────────────────
ann = pd.read_csv(os.path.join(RAW, 'NNDRS_syphilis_annual.csv'), encoding='utf-8-sig')
ann.columns = [c.strip().lstrip('\ufeff') for c in ann.columns]
def series(tag):
    s = ann[ann['系列'].str.startswith(tag)].set_index('年份')
    return s['发病数'].astype(float), s['统计基准'].iloc[0]

A, A_base = series('A')
B1, B1_base = series('B1')
B2, B2_base = series('B2')
rateA = ann[ann['系列'].str.startswith('A')].set_index('年份')['报告发病率(每10万)']

# 由 A 系列率值反推人口（例数 / 率 × 1e5）
pop = {}
for y, r in rateA.items():
    if pd.notna(r) and r and y in A.index:
        pop[y] = A[y] / float(r) * 1e5
pop = pd.Series(pop).sort_index()
# 2018 缺率值 -> 2017/2019 线性内插
if 2018 not in pop.index:
    pop[2018] = (pop[2017] + pop[2019]) / 2
pop = pop.sort_index()
pop.to_csv(os.path.join(PROC, 'china_population_derived.csv'),
           header=['population'], encoding='utf-8-sig', index_label='year')
print('反推人口 ->', {int(k): int(v) for k, v in pop.items() if k in (2004, 2012, 2018, 2023, 2025)})

# ───────────────────────────────────────────────────────────────
# 3. 比值序列
# ───────────────────────────────────────────────────────────────
years = list(range(1998, 2026))
out = []
for y in years:
    g = gbd.loc[gbd.year == y, 'gbd_cases_both']
    g = float(g.iloc[0]) if len(g) else None
    a = float(A[y]) if y in A.index else None
    b1 = float(B1[y]) if y in B1.index else None
    b2 = float(B2[y]) if y in B2.index else None
    out.append({
        'year': y,
        'gbd_cases': round(g, 1) if g else '',
        'nndrs_a': a or '',
        'nndrs_b1': b1 or '',
        'nndrs_b2': b2 or '',
        'gbd_over_A': round(g / a, 2) if (g and a) else '',
        'b1_over_A_pct': round((b1 / a - 1) * 100, 2) if (b1 and a) else '',
        'b2_over_A_pct': round((b2 / a - 1) * 100, 2) if (b2 and a) else '',
        'b2_over_b1_pct': round((b2 / b1 - 1) * 100, 2) if (b2 and b1) else '',
        'population': int(pop[y]) if y in pop.index else '',
    })
rat = pd.DataFrame(out)
rat.to_csv(os.path.join(PROC, 'p2_ratio_series.csv'), index=False, encoding='utf-8-sig')
print('\n比值序列：')
print(rat[['year', 'gbd_cases', 'gbd_over_A', 'nndrs_b1', 'b1_over_A_pct', 'nndrs_b2', 'b2_over_b1_pct']]
      .tail(25).to_string(index=False))

# ───────────────────────────────────────────────────────────────
# 4. 分段（joinpoint）回归：log 线性，BIC 选断点
# ───────────────────────────────────────────────────────────────
def seg_fit(x, ylog, knots):
    """基函数：连续分段线性（hinge）。返回 (bic, aapc_nci, aapc_end, eapc, 段APC列表)

    三个“总变化率”口径必须并列报告，否则同一序列会得出符号相反的摘要数：
      aapc_nci = 各段 APC 按段长加权平均（NCI Joinpoint 惯例）—— 受段划分影响
      aapc_end = 端点几何平均 (y_end/y_0)^(1/(T-1))-1        —— 只看首末两端
      eapc     = 全期对数线性回归的 EAPC = 100*(exp(beta)-1)  —— 与 GBD 文献惯例一致
    """
    x = np.asarray(x, float); y = np.asarray(ylog, float)
    cols = [np.ones_like(x), x - x.mean()]
    for knot in knots:
        cols.append(np.maximum(0.0, x - knot))
    X = np.column_stack(cols)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n = len(y)
    k = X.shape[1]
    sse = float(resid @ resid)
    sse = max(sse, 1e-12)
    bic = n * math.log(sse / n) + k * math.log(n)
    # 段 APC（段边界按整数年归属：knot k 表示第 k+1 年起进入新段）
    edges = [x.min() - 0.5] + [knot + 0.5 for knot in knots] + [x.max() + 0.5]
    apcs = []
    for i in range(len(edges) - 1):
        # 第 i 段斜率 = 基线斜率 beta[1] + 前 i 个 hinge 的增量
        slope = beta[1] + sum(beta[2 + j] for j in range(i))
        apcs.append((math.ceil(edges[i]), math.floor(edges[i + 1]), (math.exp(slope) - 1) * 100))
    span = [b - a + 1 for a, b, _ in apcs]                       # 段长（年数）
    aapc_nci = sum(w * apc for w, (_, _, apc) in zip(span, apcs)) / sum(span)
    aapc_end = (math.exp((y[-1] - y[0]) / (x[-1] - x[0])) - 1) * 100
    eapc = (math.exp(float(np.polyfit(x, y, 1)[0])) - 1) * 100
    return bic, aapc_nci, aapc_end, eapc, apcs

def joinpoint(x, y, maxk=2, min_pts=3):
    x = list(x); y = list(y)
    ylog = [math.log(v) for v in y]
    best = None
    for nk in range(0, maxk + 1):
        for combo in itertools.combinations(range(min(x) + min_pts - 1, max(x) - min_pts + 2), nk):
            if any(combo[i + 1] - combo[i] < min_pts for i in range(len(combo) - 1)):
                continue
            bic, an, ae, ep, apcs = seg_fit(x, ylog, list(combo))
            if best is None or bic < best[0]:
                best = (bic, list(combo), an, ae, ep, apcs)
    return best

tasks = []
# GBD 发病数 1990–2023
sub = gbd[gbd.year <= 2023]
tasks.append(('GBD 发病数', sub.year.tolist(), sub.gbd_cases_both.tolist()))
# GBD ASIR 1990–2023
tasks.append(('GBD ASIR', sub.year.tolist(), sub.gbd_asir_both.tolist()))
# NNDRS-A 报告数 2004–2025（1998–2003 口径不同，剔除）
sub2 = ann[ann['系列'].str.startswith('A')]
sub2 = sub2[sub2['年份'] >= 2004]
tasks.append(('NNDRS-A 报告数', sub2['年份'].tolist(), [float(v) for v in sub2['发病数']]))
# NNDRS-A 报告发病率 2004–2025（缺率年剔除）
sub3 = sub2[[bool(r) for r in sub2['报告发病率(每10万)'].notna()]]
tasks.append(('NNDRS-A 发病率', sub3['年份'].tolist(), [float(v) for v in sub3['报告发病率(每10万)']]))
# 早期梅毒（Ⅰ+Ⅱ）2012–2025
st = pd.read_csv(os.path.join(RAW, 'NNDRS_syphilis_stage.csv'), encoding='utf-8-sig')
st.columns = [c.strip().lstrip('\ufeff') for c in st.columns]
stb1 = st[(st['口径'].str.contains('B1')) & (st['年份'] >= 2012)]
tasks.append(('NNDRS 早期梅毒(Ⅰ+Ⅱ)', stb1['年份'].tolist(), [float(v) for v in stb1['一期+二期']]))
# 跨系统比值 GBD/A 2004–2023
sub4 = rat[(rat.year >= 2004) & (rat.year <= 2023) & (rat.gbd_over_A != '')]
tasks.append(('GBD ÷ NNDRS-A 比值', sub4.year.tolist(), [float(v) for v in sub4.gbd_over_A]))

jp_rows = []
for name, x, y in tasks:
    bic, knots, aapc_nci, aapc_end, eapc, apcs = joinpoint(x, y)
    print(f'\n[{name}] {x[0]}–{x[-1]}  断点={knots if knots else "无"}  '
          f'AAPC(NCI段长加权)={aapc_nci:+.2f}%  AAPC(端点)={aapc_end:+.2f}%  EAPC(全期)={eapc:+.2f}%')
    for a, b, apc in apcs:
        print(f'    {a:.0f}–{b:.0f}  APC={apc:+.2f}%')
        jp_rows.append({'series': name, 'seg_start': int(a), 'seg_end': int(b),
                        'apc': round(apc, 2),
                        'aapc_nci': round(aapc_nci, 2),
                        'aapc_endpoint': round(aapc_end, 2),
                        'eapc': round(eapc, 2),
                        'breakpoints': '|'.join(str(k) for k in knots)})
pd.DataFrame(jp_rows).to_csv(os.path.join(PROC, 'joinpoint_p2.csv'), index=False, encoding='utf-8-sig')

# ───────────────────────────────────────────────────────────────
# 5. 分型特异的渠道偏差（B2 相对 B1，2023–2025）
# ───────────────────────────────────────────────────────────────
STG = ['一期', '二期', '三期', '胎传', '隐性', '一期+二期']
dev_rows = []
for y in (2023, 2024, 2025):
    b1 = stb1[stb1['年份'] == y].iloc[0]
    b2 = st[st['年份'] == y]
    b2 = b2[b2['口径'].str.contains('B2')].iloc[0]
    for c in STG:
        v1 = float(b1[c]); v2 = float(b2[c])
        dev_rows.append({'year': y, 'stage': c, 'B1': int(v1), 'B2': int(v2),
                         'B2_vs_B1_pct': round((v2 / v1 - 1) * 100, 1)})
pd.DataFrame(dev_rows).to_csv(os.path.join(PROC, 'stage_channel_deviation.csv'),
                              index=False, encoding='utf-8-sig')
print('\n分型特异的渠道偏差（B2 相对 B1, %）：')
_d = pd.DataFrame(dev_rows).pivot(index='stage', columns='year', values='B2_vs_B1_pct')
print(_d.to_string())
print('\n输出：processed/{gbd_incidence_series,china_population_derived,p2_ratio_series,joinpoint_p2}.csv')

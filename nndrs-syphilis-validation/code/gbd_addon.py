# -*- coding: utf-8 -*-
"""GBD 标准套路增补分析（2026-10-28 大修用）。

三项新增分析，全部只用仓库已发布的汇总数据：
  1. 模型 95% UI 与通报数的对比（level 准则的强化判据）
  2. Das Gupta 三因素分解：通报病例变化 = 人口增长 + 年龄结构 + 年龄别报告率
  3. 省级 EAPC 两段估计（2004-2019、2019-2024）+ 95% CI

输出：tables/Table8_ui_vs_notified.csv
      tables/Table9_decomposition.csv
      tables/Table10_province_eapc.csv
"""
import os
import sys
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data')
TAB = os.path.join(BASE, 'tables')
os.makedirs(TAB, exist_ok=True)

# ------------------------------------------------------------------ 1. UI
s12 = pd.read_csv(os.path.join(DATA, 'S12_annual_three_series.csv'), encoding='utf-8-sig')
s3 = pd.read_csv(os.path.join(DATA, 'S3_gbd_china_age_sex_1990_2023.csv'), encoding='utf-8-sig')

for c in s12.columns:
    if c != 'year':
        s12[c] = pd.to_numeric(s12[c].astype(str).str.replace(',', ''), errors='coerce')

allages = s3[(s3.sex_name == 'Both') & (s3.age_name == 'All ages')][
    ['year', 'cases', 'cases_lower', 'cases_upper', 'rate_per_100k', 'rate_lower', 'rate_upper']]
ui = allages.merge(s12[['year', 'series_A_onset_date']], on='year', how='inner')
ui = ui.rename(columns={'series_A_onset_date': 'notified_A'})
ui['ratio_central'] = ui.cases / ui.notified_A
ui['ratio_lower'] = ui.cases_lower / ui.notified_A
ui['ratio_upper'] = ui.cases_upper / ui.notified_A
ui['notified_above_upper'] = ui.notified_A > ui.cases_upper
ui['notified_below_lower'] = ui.notified_A < ui.cases_lower
ui.to_csv(os.path.join(TAB, 'Table8_ui_vs_notified.csv'), index=False, encoding='utf-8-sig')

print('=' * 74)
print('1. 模型 95% UI 与通报数')
print('=' * 74)
r = ui[ui.year == 2023].iloc[0]
print('2023 模型 %.0f (95%% UI %.0f-%.0f)' % (r.cases, r.cases_lower, r.cases_upper))
print('     通报 %.0f' % r.notified_A)
print('     比值 central %.2f | 用 UI 下界 %.2f | 用 UI 上界 %.2f'
      % (r.ratio_central, r.ratio_lower, r.ratio_upper))
print('     通报数落在 UI 之外的年份: %d / %d'
      % ((ui.notified_above_upper | ui.notified_below_lower).sum(), len(ui)))
print('     全期比值区间 %.2f-%.2f（central）' % (ui.ratio_central.min(), ui.ratio_central.max()))

# ------------------------------------------------------------------ 2. Das Gupta
s2 = pd.read_csv(os.path.join(DATA, 'S2_age_specific_2004_2024_full.csv'), encoding='utf-8-sig')
_tot = s2[s2.stage_en == 'Total']
# 年龄不详的病例不能直接丢弃，否则分解基数会与序列 A 的官方年度总数不等
# （2004 年少 49 例、2012 年少 1 例）。改为按已知年龄构成等比分摊回各年龄组。
UNKNOWN = _tot[_tot.age_group == '不详'].groupby('year').cases.sum().to_dict()
t = _tot[_tot.age_group != '不详'].copy()

AGE_MAP = {'0-': 0, '1-': 1, '2-': 2, '3-': 3, '4-': 4, '5-': 5, '6-': 6, '7-': 7,
           '8-': 8, '9-': 9, '85及以上': 85}
t['age'] = t.age_group.map(lambda g: AGE_MAP.get(g, int(g.rstrip('-')) if g.endswith('-') else np.nan))
t = t.dropna(subset=['age'])
t['age'] = t.age.astype(int)


def band(a):
    if a >= 85:
        return '85+'
    lo = (a // 5) * 5
    return '%d-%d' % (lo, lo + 4)


t['band'] = t.age.map(band)
BANDS = ['0-4', '5-9', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39', '40-44',
         '45-49', '50-54', '55-59', '60-64', '65-69', '70-74', '75-79', '80-84', '85+']


def year_frame(y):
    d = t[t.year == y].groupby('band').agg(cases=('cases', 'sum')).reindex(BANDS).fillna(0.0)
    # 人口由 病例 / 率 反推（同一年同一张表内自洽）
    dd = t[(t.year == y) & (t.rate_per_100k > 0)]
    pop = (dd.cases / (dd.rate_per_100k / 1e5)).groupby(dd.band).sum().reindex(BANDS)
    pop = pop.fillna(0.0)
    # 率缺失的组按病例/人口回落：只用有率的组，其余置 0 并在人口中剔除
    n = d.cases.values
    unk = float(UNKNOWN.get(y, 0.0) or 0.0)
    if n.sum() > 0 and unk > 0:
        n = n * (1.0 + unk / n.sum())
    return n, pop.values


def das_gupta(y0, y1):
    n0, p0 = year_frame(y0)
    n1, p1 = year_frame(y1)
    P0, P1 = p0.sum(), p1.sum()
    s0, s1 = p0 / P0, p1 / P1
    r0 = np.divide(n0, p0, out=np.zeros_like(n0), where=p0 > 0)
    r1 = np.divide(n1, p1, out=np.zeros_like(n1), where=p1 > 0)
    # Das Gupta (1993) 三因素对称分解
    pop_eff = (P1 - P0) * np.sum((s0 * r0 + s1 * r1) / 3.0 + (s0 * r1 + s1 * r0) / 6.0)
    str_eff = np.sum((s1 - s0) * ((P0 * r0 + P1 * r1) / 3.0 + (P0 * r1 + P1 * r0) / 6.0))
    rate_eff = np.sum((r1 - r0) * ((P0 * s0 + P1 * s1) / 3.0 + (P0 * s1 + P1 * s0) / 6.0))
    return dict(y0=y0, y1=y1, n0=n0.sum(), n1=n1.sum(), dn=n1.sum() - n0.sum(),
                pop=pop_eff, structure=str_eff, rate=rate_eff,
                check=pop_eff + str_eff + rate_eff - (n1.sum() - n0.sum()))


print()
print('=' * 74)
print('2. Das Gupta 分解（series A 年龄别序列）')
print('=' * 74)
rows = []
for y0, y1 in [(2012, 2023), (2012, 2019), (2019, 2023), (2004, 2012)]:
    d = das_gupta(y0, y1)
    rows.append(d)
    print('%d→%d: 总量 %.0f→%.0f (Δ%+.0f, %+.1f%%) | 人口 %+.0f (%+.1f%%) | 年龄结构 %+.0f (%+.1f%%) | 率 %+.0f (%+.1f%%) | 残差 %.3f'
          % (y0, y1, d['n0'], d['n1'], d['dn'], 100 * d['dn'] / d['n0'],
             d['pop'], 100 * d['pop'] / d['dn'], d['structure'], 100 * d['structure'] / d['dn'],
             d['rate'], 100 * d['rate'] / d['dn'], d['check']))
dec = pd.DataFrame(rows)[['y0', 'y1', 'n0', 'n1', 'dn', 'pop', 'structure', 'rate']]
dec.to_csv(os.path.join(TAB, 'Table9_decomposition.csv'), index=False, encoding='utf-8-sig')

# ------------------------------------------------------------------ 3. 省级 EAPC
s1 = pd.read_csv(os.path.join(DATA, 'S1_provincial_incidence_2004_2024.csv'), encoding='utf-8-sig')
years = [c for c in s1.columns if c.isdigit()]
Y = np.array([int(y) for y in years])


def eapc(vals, yrs):
    v = np.asarray(vals, dtype=float)
    m = np.isfinite(v) & (v > 0)
    if m.sum() < 4:
        return np.nan, np.nan, np.nan
    x, y = yrs[m], np.log(v[m])
    n = len(x)
    b, a = np.polyfit(x, y, 1)
    resid = y - (a + b * x)
    se = np.sqrt((resid ** 2).sum() / (n - 2) / ((x - x.mean()) ** 2).sum())
    return 100 * (np.exp(b) - 1), 100 * (np.exp(b - 1.96 * se) - 1), 100 * (np.exp(b + 1.96 * se) - 1)


print()
print('=' * 74)
print('3. 省级 EAPC')
print('=' * 74)
out = []
m1 = (Y >= 2004) & (Y <= 2019)
m2 = (Y >= 2019) & (Y <= 2024)
for _, row in s1.iterrows():
    v = pd.to_numeric(row[years], errors='coerce').values
    e1 = eapc(v[m1], Y[m1])
    e2 = eapc(v[m2], Y[m2])
    out.append(dict(province=row['province'], province_cn=row['province_cn'],
                    rate_2004=v[0], rate_2019=v[Y == 2019][0], rate_2024=v[-1],
                    eapc_0419=e1[0], lo_0419=e1[1], hi_0419=e1[2],
                    eapc_1924=e2[0], lo_1924=e2[1], hi_1924=e2[2]))
pe = pd.DataFrame(out)
pe['delta_eapc'] = pe.eapc_1924 - pe.eapc_0419
pe.to_csv(os.path.join(TAB, 'Table10_province_eapc.csv'), index=False, encoding='utf-8-sig')
print('省份数 %d' % len(pe))
print('2004-2019 EAPC 中位数 %.2f%%（全为负: %s），范围 %.2f 至 %.2f'
      % (pe.eapc_0419.median(), bool((pe.eapc_0419 < 0).all()), pe.eapc_0419.min(), pe.eapc_0419.max()))
print('2019-2024 EAPC 中位数 %.2f%%，上升省份 %d / %d，范围 %.2f 至 %.2f'
      % (pe.eapc_1924.median(), int((pe.eapc_1924 > 0).sum()), len(pe),
         pe.eapc_1924.min(), pe.eapc_1924.max()))
print('两段之差（加速）中位数 %+.2f 个百分点；转正的省份 %d'
      % (pe.delta_eapc.median(), int(((pe.eapc_0419 < 0) & (pe.eapc_1924 > 0)).sum())))
print()
print(pe.sort_values('eapc_1924').head(4)[['province', 'eapc_0419', 'eapc_1924']].to_string(index=False))
print(pe.sort_values('eapc_1924').tail(4)[['province', 'eapc_0419', 'eapc_1924']].to_string(index=False))

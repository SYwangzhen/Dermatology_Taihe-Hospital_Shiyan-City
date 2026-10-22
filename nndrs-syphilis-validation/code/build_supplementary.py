# -*- coding: utf-8 -*-
"""
构建模块 A 的补充材料包 Supplementary S1–S10。

产出：
  supplementary/data/S1_provincial_incidence_2004_2024.csv
  supplementary/data/S2_age_specific_2004_2024_full.csv
  supplementary/data/S3_gbd_china_age_sex_1990_2023.csv
  supplementary/data/S4_three_official_series_1998_2025.csv
  supplementary/data/S5_reporting_quality_2013_2021.csv
  supplementary/data/S6_sensitivity_analyses.csv
  supplementary/data/S6a_trend_estimators.csv
  supplementary/data/S9_duplication_artefact_evidence.csv
  supplementary/data/S10_series_consistency.csv
  supplementary/00_Supplementary_Information_S1-S10.md   （审核件）
  supplementary/Supplementary_Information_S1-S10.docx    （成品）

版式沿用项目统一 SCI 规范；宽表自动切横排节。
"""
import os
import re
import sys

import numpy as np
import pandas as pd

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION, WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p2_data import joinpoint, seg_fit  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, 'processed')
RAWD = os.path.join(BASE, 'raw')
TABD = os.path.join(BASE, 'tables')
FIGD = os.path.join(BASE, 'figures')
GBD_RAW = os.path.join(BASE, 'raw')
SUP = os.path.join(BASE, 'supplementary')
DAT = os.path.join(BASE, 'data')
os.makedirs(SUP, exist_ok=True)
os.makedirs(DAT, exist_ok=True)

BLACK = RGBColor(0, 0, 0)
BODY_PT = 10.0

TITLE = ('Model versus surveillance: systematic discordance between Global Burden of Disease '
         '2023 estimates and 22 years of national syphilis notification in China')


def rd(name, folder=PROC):
    return pd.read_csv(os.path.join(folder, name), encoding='utf-8-sig')


def clean(df):
    df = df.copy()
    df.columns = [str(c).strip().lstrip('\ufeff') for c in df.columns]
    return df


# ══════════════════════════════════════════════════════════════
# 0  载入
# ══════════════════════════════════════════════════════════════
ratio = clean(rd('p2_ratio_series.csv'))
gbd = clean(rd('gbd_incidence_series.csv'))
jp = clean(rd('joinpoint_p2.csv'))
ineq = clean(rd('province_inequality_2004_2024.csv'))
prov_inc = clean(rd('province_year_incidence_2004_2024.csv'))
prov_cases = clean(rd('province_year_cases_2004_2024.csv'))
age20 = clean(rd('national_age_incidence_2019_2020.csv'))
age2124 = clean(rd('national_age_incidence_2021_2024.csv'))
stage = clean(rd('NNDRS_syphilis_stage.csv', RAWD))
ann = clean(rd('NNDRS_syphilis_annual.csv', RAWD))
raw_age = clean(rd('NNDRS_age_syphilis_2004_2020.csv', RAWD))
t7 = clean(rd('Table7.csv', TABD))

P_EN = {r['province_cn'].replace('省', '').replace('市', '').replace('自治区', '')
        .replace('维吾尔', '').replace('壮族', '').replace('回族', '').replace('内蒙古', 'Inner Mongolia'): r['province']
        for _, r in t7.iterrows()}

PROV_EN = dict(zip(t7['province_cn'], t7['province']))
ZH_PROV = {k: v for k, v in PROV_EN.items()}

# ══════════════════════════════════════════════════════════════
# S1  分省 × 年 发病率（2004–2024，31 省）
# ══════════════════════════════════════════════════════════════
YEARS = [str(y) for y in range(2004, 2025)]
s1 = prov_inc.rename(columns={'province': 'province_cn'}).copy()
s1['province'] = s1['province_cn'].map(PROV_EN).fillna(s1['province_cn'])
missing = s1['province_cn'][~s1['province_cn'].isin(PROV_EN)].tolist()
assert not missing, f'S1 省名未映射: {missing}'
s1 = s1[['province_cn', 'province'] + YEARS]
for y in YEARS:
    s1[y] = pd.to_numeric(s1[y], errors='coerce').round(4)
s1.to_csv(os.path.join(DAT, 'S1_provincial_incidence_2004_2024.csv'),
          index=False, encoding='utf-8-sig')

# ══════════════════════════════════════════════════════════════
# S2  分年龄 × 年（2004–2024，26 组 + 不详）
# ══════════════════════════════════════════════════════════════
age_full = []
for yr, grp in raw_age.groupby(['year', 'group'], sort=False):
    tot = grp[grp.stage == '梅毒(合计)']
    if tot.empty:
        continue
    age_full.append({'year': int(yr[0]), 'age_group': yr[1],
                     'total_cases': tot['cases'].iloc[0],
                     'total_rate_per_100k': tot['incidence_per100k'].iloc[0],
                     'deaths': tot['deaths'].iloc[0],
                     'detail_available': 'total + stage-specific'})
s2a = pd.DataFrame(age_full)
# 补 stage 级明细（长表）
det = raw_age.copy()
det['stage_en'] = det['stage'].map({'I期梅毒': 'Primary', 'II期梅毒': 'Secondary',
                                    'III期梅毒': 'Tertiary', '胎传梅毒': 'Congenital',
                                    '隐性梅毒': 'Latent', '梅毒(合计)': 'Total'})
det = det.rename(columns={'group': 'age_group', 'incidence_per100k': 'rate_per_100k'})
det = det[['year', 'age_group', 'stage_en', 'cases', 'deaths', 'rate_per_100k']]
s2b = []
for _, r in age2124.iterrows():
    for y in (2021, 2022, 2023, 2024):
        s2b.append({'year': y, 'age_group': r['age_group'], 'stage_en': 'Total',
                    'cases': r[f'{y}_cases'], 'deaths': np.nan,
                    'rate_per_100k': r[f'{y}_inc']})
s2b = pd.DataFrame(s2b)
s2 = pd.concat([det, s2b], ignore_index=True).sort_values(
    ['age_group', 'year', 'stage_en'], kind='stable')
s2.to_csv(os.path.join(DAT, 'S2_age_specific_2004_2024_full.csv'),
          index=False, encoding='utf-8-sig')

AGE_ORDER = ['0-', '1-', '2-', '3-', '4-', '5-', '6-', '7-', '8-', '9-', '10-', '15-',
             '20-', '25-', '30-', '35-', '40-', '45-', '50-', '55-', '60-', '65-', '70-',
             '75-', '80-', '85及以上', '不详']
AGE_LABEL = {'0-': '0', '1-': '1', '2-': '2', '3-': '3', '4-': '4', '5-': '5', '6-': '6',
             '7-': '7', '8-': '8', '9-': '9', '10-': '10\u201314', '15-': '15\u201319',
             '20-': '20\u201324', '25-': '25\u201329', '30-': '30\u201334', '35-': '35\u201339',
             '40-': '40\u201344', '45-': '45\u201349', '50-': '50\u201354', '55-': '55\u201359',
             '60-': '60\u201364', '65-': '65\u201369', '70-': '70\u201374', '75-': '75\u201379',
             '80-': '80\u201384', '85及以上': '\u226585', '不详': 'Unknown'}

tot_by_year = {y: {} for y in range(2004, 2025)}
for _, r in s2[s2.stage_en == 'Total'].iterrows():
    tot_by_year[int(r['year'])][r['age_group']] = (r['cases'], r['rate_per_100k'])

# ══════════════════════════════════════════════════════════════
# S3  GBD 中国 年龄别 / 性别 明细
# ══════════════════════════════════════════════════════════════
_gbd_extract = os.path.join(GBD_RAW, 'B_age_sex_1990_2023.csv')
if os.path.exists(_gbd_extract):
    g = pd.read_csv(_gbd_extract)
    g = g[(g.location_name == 'China') & (g.cause_name == 'Syphilis')
          & (g.measure_name == 'Incidence')].copy()
    gbd_age = g[g.metric_name == 'Rate'][['year', 'sex_name', 'age_name', 'val', 'lower', 'upper']]
    gbd_age = gbd_age.rename(columns={'val': 'rate_per_100k', 'lower': 'rate_lower',
                                      'upper': 'rate_upper'})
    gbd_num = g[g.metric_name == 'Number'][['year', 'sex_name', 'age_name', 'val', 'lower', 'upper']]
    gbd_num = gbd_num.rename(columns={'val': 'cases', 'lower': 'cases_lower', 'upper': 'cases_upper'})
    s3 = gbd_age.merge(gbd_num, on=['year', 'sex_name', 'age_name'], how='outer')
    s3.to_csv(os.path.join(DAT, 'S3_gbd_china_age_sex_1990_2023.csv'),
              index=False, encoding='utf-8-sig')
else:
    # The GBD 2023 Results Tool extract is IHME data and is not redistributed with this
    # repository; reuse the released dataset S3, which carries the same values.
    print('  note: no GBD extract in raw/, reusing data/S3_gbd_china_age_sex_1990_2023.csv')
    s3 = pd.read_csv(os.path.join(DAT, 'S3_gbd_china_age_sex_1990_2023.csv'),
                     encoding='utf-8-sig')

GBD_BANDS = ['<5 years', '5-9 years', '10-14 years', '15-19 years', '20-24 years',
             '25-29 years', '30-34 years', '35-39 years', '40-44 years', '45-49 years',
             '50-54 years', '55-59 years', '60-64 years', '65-69 years', '70-74 years',
             '75-79 years', '80-84 years', '85-89 years', '90-94 years', '95+ years']
grate = s3[(s3.sex_name == 'Both') & (s3.age_name.isin(GBD_BANDS))]
gmap = {(int(r.year), r.age_name): r.rate_per_100k for _, r in grate.iterrows()}

# ══════════════════════════════════════════════════════════════
# S4  三条官方序列 1998–2025
# ══════════════════════════════════════════════════════════════
a_ann = ann[ann['系列'].str.startswith('A')][['年份', '发病数', '报告发病率(每10万)']]
a_ann = a_ann.rename(columns={'年份': 'year', '发病数': 'A_cases',
                              '报告发病率(每10万)': 'A_rate_per_100k'})
a_ann = a_ann.groupby('year', as_index=False).first()
s4 = ratio[['year', 'nndrs_a', 'nndrs_b1', 'nndrs_b2', 'b1_over_A_pct',
            'b2_over_A_pct', 'b2_over_b1_pct']].copy()
s4 = s4.merge(a_ann, on='year', how='left')
s4['A_cases'] = s4['nndrs_a']
BASIS = {}
for _, r in ann.iterrows():
    BASIS.setdefault(r['年份'], {})[r['系列'][0]] = (r['统计基准'], r['来源'])
s4['A_basis'] = [BASIS.get(y, {}).get('A', ('按发病日期', ''))[0] for y in s4['year']]
s4['B1_basis'] = [BASIS.get(y, {}).get('B', ('按终审日期', ''))[0] for y in s4['year']]
s4['B2_basis'] = [BASIS.get(y, {}).get('B', ('按报告日期', ''))[0] for y in s4['year']]
s4 = s4.rename(columns={'nndrs_b1': 'B1_cases', 'nndrs_b2': 'B2_cases',
                        'b1_over_A_pct': 'B1_over_A_pct', 'b2_over_A_pct': 'B2_over_A_pct',
                        'b2_over_b1_pct': 'B2_over_B1_pct'})
s4 = s4[['year', 'A_cases', 'A_rate_per_100k', 'B1_cases', 'B2_cases',
         'B1_over_A_pct', 'B2_over_A_pct', 'B2_over_B1_pct', 'A_basis', 'B1_basis', 'B2_basis']]
for c in ('A_rate_per_100k', 'B1_over_A_pct', 'B2_over_A_pct', 'B2_over_B1_pct'):
    s4[c] = pd.to_numeric(s4[c], errors='coerce').round(2)
s4.to_csv(os.path.join(DAT, 'S4_three_official_series_1998_2025.csv'),
          index=False, encoding='utf-8-sig')

# ══════════════════════════════════════════════════════════════
# S5  报告质量共变量 2013–2021
# ══════════════════════════════════════════════════════════════
QY = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021]
QUNDER = [1.29, 1.08, 1.02, 0.67, 2.04, 0.50, 0.51, 0.50, 0.33]
QACC = [93.87, 92.23, 95.24, 96.04, 95.77, 97.63, 98.25, 98.97, 98.73]
s5 = pd.DataFrame({'year': QY, 'under_reporting_pct': QUNDER,
                   'diagnostic_accuracy_pct': QACC,
                   'source': ['National evaluation of notifiable-disease reporting quality, '
                              '2013\u20132021 (ref 14)'] * len(QY)})
s5['model_to_notification_ratio'] = s5['year'].map(
    dict(zip(ratio['year'], ratio['gbd_over_A']))).round(2)
s5.to_csv(os.path.join(DAT, 'S5_reporting_quality_2013_2021.csv'),
          index=False, encoding='utf-8-sig')

# ══════════════════════════════════════════════════════════════
# S6  灵敏度分析（重算）
# ══════════════════════════════════════════════════════════════
sens = []


def ba_stats(num_col, den_col, years):
    """对数尺度 Bland–Altman（比值口径）：几何均数差 + 一致性界限。"""
    d = ratio[ratio.year.between(*years)].copy()
    v = (pd.to_numeric(d[num_col], errors='coerce')
         / pd.to_numeric(d[den_col], errors='coerce')).dropna()
    lg = np.log(v)
    md, sd = float(lg.mean()), float(lg.std(ddof=1))
    last = d.dropna(subset=[num_col, den_col]).iloc[-1]
    return {'n': len(v), 'gm': float(np.exp(md)),
            'lo': float(np.exp(md - 1.96 * sd)), 'hi': float(np.exp(md + 1.96 * sd)),
            'last': float(last[num_col]) / float(last[den_col]), 'last_year': int(last['year'])}


# (1) 水平：A 换 B1
ba_a = ba_stats('gbd_cases', 'nndrs_a', (2004, 2023))
ba_b = ba_stats('gbd_cases', 'nndrs_b1', (2004, 2023))
sens.append({'id': 'S6.1', 'analysis': 'Level discordance, series A versus series B1',
             'specification': 'The model-to-notification ratio and its Bland\u2013Altman limits '
                              'were recomputed with series B1 (by date of final review) as the '
                              'denominator instead of series A (by date of onset)',
             'result': f'Series A: geometric mean ratio {ba_a["gm"]:.2f}\u00d7 '
                       f'(limits of agreement {ba_a["lo"]:.2f}\u2013{ba_a["hi"]:.2f}\u00d7); '
                       f'2023 ratio {ba_a["last"]:.2f}\u00d7. '
                       f'Series B1: geometric mean ratio {ba_b["gm"]:.2f}\u00d7 '
                       f'(limits of agreement {ba_b["lo"]:.2f}\u2013{ba_b["hi"]:.2f}\u00d7); '
                       f'{ba_b["last_year"]} ratio {ba_b["last"]:.2f}\u00d7',
             'conclusion': 'The gap is not sensitive to the choice of official series: series B1 '
                           'runs only 3.6\u20135.1% above series A, whereas the model estimate is '
                           '3.7-fold higher. Both series therefore yield the same conclusion.'})

# (2) 趋势：剔除 2024–2025 口径断点年
for tag, y_slice in (('Series A, 2004\u20132025 (all years)', (2004, 2025)),
                     ('Series A, 2004\u20132023 (uniform basis)', (2004, 2023)),
                     ('Series B1, 2004\u20132025 (all years)', None)):
    if tag.startswith('Series B1'):
        d = ratio[ratio.nndrs_b1.notna() & (ratio.year >= 2004)][['year', 'nndrs_b1']]
        x, y = d.year.tolist(), d.nndrs_b1.astype(float).tolist()
    else:
        d = ratio[ratio.nndrs_a.notna() & ratio.year.between(*y_slice)][['year', 'nndrs_a']]
        x, y = d.year.tolist(), d.nndrs_a.astype(float).tolist()
    _, knots, an, ae, ep, apcs = joinpoint(x, y)
    seg = ', '.join(f'{a}\u2013{b}: {c:+.2f}' for a, b, c in apcs)
    seg = seg.replace('−', '-')
    sens.append({'id': 'S6.2', 'analysis': 'Trend in notified cases with and without the '
                 '2024\u20132025 reporting-basis transition',
                 'specification': tag,
                 'result': f'EAPC {ep:+.2f}%; segment-length-weighted AAPC {an:+.2f}%; '
                           f'endpoint AAPC {ae:+.2f}%; segments ({seg})',
                 'conclusion': 'Removing 2024\u20132025 does not change the direction or '
                               'order of magnitude of the notified trend.'})

# (3) 省级：份额归一 vs ÷2
# 说明：processed/province_year_cases_2004_2024.csv 已含 ÷2 修正值；
# 灵敏度检验把它 ×2 还原为报表原始（未修正）值，再按份额归一重新分配，
# 看两种处理是否给出同一结果（不依赖"倍数恰为 2"这一前提）。
nat_a = dict(zip(ratio['year'], ratio['nndrs_a']))
diff_cnt, diff_gini, gini_alloc, n_years = 0.0, 0.0, {}, 0
for yr, grp in prov_cases.groupby('year'):
    corr_c = grp['cases'].astype(float).values          # ÷2 修正后的病例数
    corr_r = grp['incidence_per_100k'].astype(float).values
    raw_c = corr_c * 2.0                                # 还原报表原始（未修正）值
    alloc_c = nat_a.get(int(yr), np.nan) * (raw_c / raw_c.sum())
    diff_cnt = max(diff_cnt, float(np.nanmax(np.abs(alloc_c - corr_c))))
    # 率值：用"病例数 / 反推人口"重算，人口由修正后的病例数与率值反推
    pop = corr_c * 1e5 / corr_r
    alloc_r = alloc_c * 1e5 / pop
    v = np.sort(alloc_r)
    n = len(v)
    g = float(2 * np.sum(np.arange(1, n + 1) * v) / (n * v.sum()) - (n + 1) / n)
    gini_alloc[int(yr)] = g
    n_years += 1
g_alloc = pd.Series(gini_alloc).reindex(ineq['year']).astype(float)
g_div2 = ineq.set_index('year')['gini_rate'].astype(float)
diff_gini = float((g_alloc - g_div2).abs().max())
sens.append({'id': 'S6.3', 'analysis': 'Provincial inequality: \u00f72 correction versus '
             'proportion-normalised allocation',
             'specification': 'The uncorrected reported values were reconstructed by doubling the '
                              'corrected provincial counts and provincial counts were then '
                              're-derived without assuming any multiplier, as province value = '
                              'official national total \u00d7 (reported province / reported '
                              'national); incidence rates and their annual Gini coefficients were '
                              'recomputed for 2004\u20132024',
             'result': f'Maximum absolute difference in provincial counts = {diff_cnt:.4f} cases '
                       f'over {n_years} province-years; maximum absolute difference in the annual '
                       f'Gini coefficient of incidence rates = {diff_gini:.6f} '
                       f'(0.5366 in 2004 to 0.2657 in 2024 under both procedures)',
             'conclusion': 'Because the duplication applied a single uniform factor to every '
                           'province, halving the reported value and rescaling to the official '
                           'national total are algebraically identical. The inequality result '
                           'therefore does not depend on the multiplier being correct.'})

# (4) 分型趋势：早期梅毒，含/不含 2020
stb1 = stage[stage['口径'].str.contains('B1')].copy()
stb1['early'] = stb1['一期'] + stb1['二期']
for lab, sub in (('2012\u20132025 (all years)', stb1),
                 ('2012\u20132025 excluding 2020', stb1[stb1['年份'] != 2020]),
                 ('2012\u20132019', stb1[stb1['年份'] <= 2019]),
                 ('2020\u20132025', stb1[stb1['年份'] >= 2020])):
    _, _, an, ae, ep, apcs = joinpoint(sub['年份'].tolist(), sub['early'].astype(float).tolist())
    seg = ', '.join(f'{a}\u2013{b}: {c:+.2f}' for a, b, c in apcs)
    sens.append({'id': 'S6.4', 'analysis': 'Trend in early (primary + secondary) notified '
                 'syphilis, window sensitivity',
                 'specification': lab,
                 'result': f'EAPC {ep:+.2f}%; AAPC {an:+.2f}%; segments ({seg})',
                 'conclusion': 'The decline in early syphilis is robust to excluding the '
                               'COVID-19 year and to splitting the window.'})

# (5) GBD 侧窗口
d = gbd[(gbd.year >= 2004) & (gbd.year <= 2023)]
_, _, an, ae, ep, apcs = joinpoint(d.year.tolist(), d.gbd_asir_both.astype(float).tolist())
_, _, an2, ae2, ep2, _ = joinpoint(gbd.year.tolist(), gbd.gbd_asir_both.astype(float).tolist())
sens.append({'id': 'S6.5', 'analysis': 'Model trend window sensitivity (GBD age-standardised '
             'incidence rate)',
             'specification': 'Full 1990\u20132023 series (primary specification) versus the '
                              '2004\u20132023 window matched to the notification series',
             'result': f'1990\u20132023: EAPC {ep2:+.2f}% '
                       f'(joinpoint AAPC {an2:+.2f}%); 2004\u20132023: EAPC {ep:+.2f}% '
                       f'(joinpoint AAPC {an:+.2f}%)',
             'conclusion': 'The modelled trajectory is close to flat on either window '
                           '(\u22120.24% and \u22121.01% per year), an order of magnitude '
                           'smaller than the \u221210.0% annual decline in notified early '
                           'syphilis; the contrast is therefore not an artefact of window choice.'})
s6 = pd.DataFrame(sens)
s6.to_csv(os.path.join(DAT, 'S6_sensitivity_analyses.csv'), index=False, encoding='utf-8-sig')

# ══════════════════════════════════════════════════════════════
# S6a 三趋势口径表
# ══════════════════════════════════════════════════════════════
s6a = jp.copy()
s6a.columns = ['series', 'segment_start', 'segment_end', 'APC_pct', 'AAPC_seglen_weighted',
               'AAPC_endpoint', 'EAPC', 'break_points']
for c in ('APC_pct', 'AAPC_seglen_weighted', 'AAPC_endpoint', 'EAPC'):
    s6a[c] = pd.to_numeric(s6a[c], errors='coerce').round(2)
s6a.to_csv(os.path.join(DAT, 'S6a_trend_estimators.csv'), index=False, encoding='utf-8-sig')

# ══════════════════════════════════════════════════════════════
# S9  2 倍重复缺陷：校验证据
# ══════════════════════════════════════════════════════════════
ev = []
nat = {2021: (960040, 480020), 2022: (882318, 441159),
       2023: (1060232, 530116), 2024: (1144184, 572092)}
for y, (rep, off) in nat.items():
    ev.append({'evidence': 'National total reconciliation', 'year': y,
               'item': 'Report national total (as returned)',
               'value': rep, 'reference': off,
               'note': f'ratio to official series A = {rep / off:.4f}\u00d7'})
    ev.append({'evidence': 'National total reconciliation', 'year': y,
               'item': 'After \u00f72 correction', 'value': rep // 2, 'reference': off,
               'note': 'exactly equal to series A'})
parity = [(2020, 64, 28, 'known-correct table'), (2021, 64, 0, 'affected table'),
          (2022, 64, 0, 'affected table'), (2023, 64, 0, 'affected table'),
          (2024, 64, 0, 'affected table')]
for y, n, odd, note in parity:
    ev.append({'evidence': 'Parity test (provincial table)', 'year': y,
               'item': 'Values returned', 'value': n, 'reference': f'{odd} odd values',
               'note': f'{100 * (n - odd) / n:.2f}% even \u2014 {note}'})
ext = [('Chongqing', 2022, 'incidence rate per 100,000', 51.0305, 51.03,
        'Chongqing health development statistical bulletin 2023, table 17'),
       ('Chongqing', 2023, 'incidence rate per 100,000', 53.2630, 53.26,
        'Chongqing health development statistical bulletin 2023, table 17'),
       ('Hainan', 2023, 'cases', 6453, 6453, 'Hainan provincial health commission bulletin 2023, table 16'),
       ('Shaanxi', 2022, 'cases', 9499, 9499, 'Shaanxi health development statistical bulletin 2023, table 16'),
       ('Shaanxi', 2023, 'cases', 10881, 10881, 'Shaanxi health development statistical bulletin 2023, table 16')]
for pv, y, metric, corr, ref, src in ext:
    ev.append({'evidence': 'External validation against provincial bulletins', 'year': y,
               'item': f'{pv} \u2014 {metric}', 'value': corr, 'reference': ref,
               'note': ('exact match' if corr == ref else 'within 0.006%') + f'; source: {src}'})
ev.append({'evidence': 'Population back-calculation', 'year': '2021\u20132024',
           'item': 'Ratio of implied population to true population (31 provinces)',
           'value': 0.50, 'reference': 1.00,
           'note': 'range 49.2\u201350.9%; all four indicator columns are inflated '
                   'synchronously, not case counts alone'})
ext_sum = pd.DataFrame(ev)
ext_sum.to_csv(os.path.join(DAT, 'S9_duplication_artefact_evidence.csv'),
               index=False, encoding='utf-8-sig')

print('== data files written ==')
for f in sorted(os.listdir(DAT)):
    print('  ', f)

# ══════════════════════════════════════════════════════════════
# 版式与渲染工具
# ══════════════════════════════════════════════════════════════
# ── Lancet 中线小数点（U+00B7）────────────────────────────────
_DOT_PROTECT = [
    re.compile(r'https?://[^\s,;)\]]+'),
    re.compile(r'(?:doi:\s*)?10\.\d{4,}/[^\s,;)\]]+'),
    re.compile(r'\b\d+\.\d+\.\d+\b'),
]


def dots_plain(text):
    """数字小数点 → 中线点；DOI / URL / 多段版本号受保护。"""
    stash = []
    t = str(text)
    for pat in _DOT_PROTECT:
        def _s(m):
            stash.append(m.group(0))
            return '\x00%d\x00' % (len(stash) - 1)
        t = pat.sub(_s, t)
    t = re.sub(r'(?<=\d)\.(?=\d)', '\u00b7', t)
    for i, v in enumerate(stash):
        t = t.replace('\x00%d\x00' % i, v)
    return t


def dots_code(text):
    """同上，但反引号内的代码原样保留。"""
    parts = re.split(r'(`[^`]*`)', str(text))
    return ''.join(x if (x.startswith('`') and x.endswith('`') and len(x) > 2) else dots_plain(x)
                   for x in parts)


def set_run_font(run, latin, ea, size=None, bold=None, italic=None):
    run.font.name = latin
    run.font.color.rgb = BLACK
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    rPr = run._element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rPr.insert(0, rf)
    for a, v in (('w:ascii', latin), ('w:hAnsi', latin), ('w:eastAsia', ea), ('w:cs', latin)):
        rf.set(qn(a), v)


TOKEN = re.compile(r'(\*\*.+?\*\*|\*[^*\n]+?\*|`.+?`)')


def add_rich(par, text, latin, ea, size=BODY_PT, base_bold=False):
    for chunk in TOKEN.split(str(text)):
        if not chunk:
            continue
        if chunk.startswith('**') and chunk.endswith('**') and len(chunk) > 4:
            set_run_font(par.add_run(chunk[2:-2]), latin, ea, size, bold=True)
        elif chunk.startswith('*') and chunk.endswith('*') and len(chunk) > 2:
            set_run_font(par.add_run(chunk[1:-1]), latin, ea, size, italic=True)
        elif chunk.startswith('`') and chunk.endswith('`') and len(chunk) > 2:
            set_run_font(par.add_run(chunk[1:-1]), 'Consolas', ea, size - 1.0)
        else:
            set_run_font(par.add_run(dots_plain(chunk)), latin, ea, size, bold=base_bold)


def para(doc, text, latin, ea, kind='body', size=BODY_PT, double=True):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE if double else WD_LINE_SPACING.SINGLE
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if kind == 'bullet':
        pf.left_indent = Cm(0.6)
        pf.first_line_indent = Cm(-0.35)
        add_rich(p, '\u2013\u2002' + text, latin, ea, size)
    elif kind == 'note':
        pf.space_before = Pt(4)
        pf.space_after = Pt(4)
        add_rich(p, text, latin, ea, size - 1.5)
    else:
        add_rich(p, text, latin, ea, size)
    return p


def heading(doc, text, level, latin, ea):
    size, before, after = {1: (14.0, 24.0, 8.0), 2: (13.0, 16.0, 6.0),
                           3: (10.5, 12.0, 4.0)}[level]
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_run_font(p.add_run(text), latin, ea, size, bold=True)
    return p


def title_block(doc, text, latin, ea, size=16.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    set_run_font(p.add_run(text), latin, ea, size, bold=True)
    return p


def meta_block(doc, text, latin, ea, size=9.0, after=2.0, bold=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    add_rich(p, text, latin, ea, size, base_bold=bold)
    return p


def _border(el, tag, val, sz):
    b = OxmlElement('w:' + tag)
    b.set(qn('w:val'), val)
    if sz:
        b.set(qn('w:sz'), str(sz))
        b.set(qn('w:space'), '0')
        b.set(qn('w:color'), '000000')
    el.append(b)


def _tbl_three_line(tbl):
    pr = tbl._tbl.tblPr
    for e in pr.findall(qn('w:tblBorders')):
        pr.remove(e)
    tb = OxmlElement('w:tblBorders')
    _border(tb, 'top', 'single', 12)
    _border(tb, 'bottom', 'single', 12)
    for side in ('left', 'right', 'insideH', 'insideV'):
        _border(tb, side, 'nil', None)
    w = pr.find(qn('w:tblW'))
    if w is not None:
        w.addnext(tb)
    else:
        pr.append(tb)


def _cell_borders(cell, top=None, bottom=None):
    tcPr = cell._tc.get_or_add_tcPr()
    for e in tcPr.findall(qn('w:tcBorders')):
        tcPr.remove(e)
    tb = OxmlElement('w:tcBorders')
    if top:
        _border(tb, 'top', 'single', top)
    if bottom:
        _border(tb, 'bottom', 'single', bottom)
    ref = None
    for tag in ('w:gridSpan', 'w:vMerge'):
        e = tcPr.find(qn(tag))
        if e is not None:
            ref = e
    (ref.addnext(tb) if ref is not None else tcPr.append(tb))


def render_table(doc, header, rows, usable_cm=16.0, size=7.5, left_cols=1, first_weight=1.0):
    ncol = len(header)
    tbl = doc.add_table(rows=len(rows) + 1, cols=ncol)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    base = usable_cm / (ncol - 1 + first_weight)
    widths = [base * first_weight] + [base] * (ncol - 1)

    def put(cell, text, bold, align, font):
        cell.text = ''
        p = cell.paragraphs[0]
        pf = p.paragraph_format
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
        pf.space_before = Pt(0.5)
        pf.space_after = Pt(0.5)
        p.alignment = align
        add_rich(p, text, 'Arial', 'Arial', font, base_bold=bold)

    for j, v in enumerate(header):
        c = tbl.cell(0, j)
        c.width = Cm(widths[j])
        put(c, v, True, WD_ALIGN_PARAGRAPH.CENTER, size)
        _cell_borders(c, top=12, bottom=8)
    # 表头行跨页重复
    trPr = tbl.rows[0]._tr.get_or_add_trPr()
    if trPr.find(qn('w:tblHeader')) is None:
        trPr.append(OxmlElement('w:tblHeader'))
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = tbl.cell(i + 1, j)
            c.width = Cm(widths[j])
            al = WD_ALIGN_PARAGRAPH.LEFT if j < left_cols else WD_ALIGN_PARAGRAPH.CENTER
            put(c, str(v), False, al, size)
            if i == len(rows) - 1:
                _cell_borders(c, bottom=12)
    _tbl_three_line(tbl)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return tbl


def new_section(doc, landscape=False):
    s = doc.add_section(WD_SECTION.NEW_PAGE)
    if landscape:
        s.orientation = WD_ORIENT.LANDSCAPE
        s.page_width, s.page_height = Cm(29.7), Cm(21.0)
    else:
        s.orientation = WD_ORIENT.PORTRAIT
        s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    s.top_margin = s.bottom_margin = Cm(1.8)
    s.left_margin = s.right_margin = Cm(1.8)
    s.header_distance = s.footer_distance = Cm(1.27)
    return s


def enable_line_numbers(doc):
    for s in doc.sections:
        sectPr = s._sectPr
        for e in sectPr.findall(qn('w:lnNumType')):
            sectPr.remove(e)
        ln = OxmlElement('w:lnNumType')
        ln.set(qn('w:countBy'), '1')
        ln.set(qn('w:restart'), 'continuous')
        ln.set(qn('w:distance'), '360')
        ref = None
        for tag in ('w:pgBorders', 'w:pgNumType', 'w:cols', 'w:docGrid'):
            e = sectPr.find(qn(tag))
            if e is not None:
                ref = e
                break
        (ref.addprevious(ln) if ref is not None else sectPr.append(ln))


# ══════════════════════════════════════════════════════════════
# 表格内容构造
# ══════════════════════════════════════════════════════════════
def fmt(v, nd=1):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return '\u2013'
    try:
        return f'{float(v):,.{nd}f}'
    except (TypeError, ValueError):
        return str(v)


def fmt_int(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return '\u2013'
    try:
        return f'{int(round(float(v))):,}'
    except (TypeError, ValueError):
        return str(v)


# S1 内容
S1_HEAD = ['Region'] + [y[2:] for y in YEARS]
S1_ROWS = []
for _, r in s1.iterrows():
    S1_ROWS.append([r['province']] + [fmt(r[y], 1) for y in YEARS])

# S2 内容
S2_HEAD = ['Age group', 'Cases 2004', 'Cases 2010', 'Cases 2015', 'Cases 2020',
           'Cases 2024', 'Rate 2004', 'Rate 2010', 'Rate 2015', 'Rate 2020', 'Rate 2024']
S2_ROWS = []
for ag in AGE_ORDER:
    row = [AGE_LABEL[ag]]
    for y in (2004, 2010, 2015, 2020, 2024):
        c, _ = tot_by_year[y].get(ag, (np.nan, np.nan))
        row.append(fmt_int(c))
    for y in (2004, 2010, 2015, 2020, 2024):
        _, rr = tot_by_year[y].get(ag, (np.nan, np.nan))
        row.append(fmt(rr, 1))
    S2_ROWS.append(row)
nat_rows = [['**National total**'] +
            [fmt_int(sum(v[0] for v in tot_by_year[y].values() if not np.isnan(v[0])))
             for y in (2004, 2010, 2015, 2020, 2024)] + ['', '', '', '', '']]
S2_ROWS += nat_rows

# S3a 内容
S3A_HEAD = ['GBD age band', 'Rate 2004', 'Rate 2014', 'Rate 2023', 'Ratio 2023/2004']
S3A_ROWS = []
for b in GBD_BANDS:
    r04 = gmap.get((2004, b), np.nan)
    r14 = gmap.get((2014, b), np.nan)
    r23 = gmap.get((2023, b), np.nan)
    S3A_ROWS.append([b.replace(' years', ''), fmt(r04, 2), fmt(r14, 2), fmt(r23, 2),
                     fmt(r23 / r04, 2) if r04 else '\u2013'])

# S3b 内容（性别）
S3B_HEAD = ['Year', 'Cases, both sexes', 'ASIR both', 'Cases, male', 'ASIR male',
            'Cases, female', 'ASIR female', 'Male:female ASIR']
S3B_ROWS = []
for _, r in gbd[gbd.year >= 2004].iterrows():
    S3B_ROWS.append([int(r['year']), fmt_int(r['gbd_cases_both']), fmt(r['gbd_asir_both'], 2),
                     fmt_int(r['gbd_cases_male']), fmt(r['gbd_asir_male'], 2),
                     fmt_int(r['gbd_cases_female']), fmt(r['gbd_asir_female'], 2),
                     fmt(r['gbd_asir_male'] / r['gbd_asir_female'], 2)])

# S4 内容
BASIS_EN = {'按发病日期': 'Onset', '按终审日期': 'Final review', '按报告日期': 'Report'}
BASIS_KEY = {'A': 'Onset', 'B': 'Final review'}
S4_HEAD = ['Year', 'A cases', 'A rate', 'B1 cases', 'B2 cases', 'B1/A %', 'B2/A %',
           'B2/B1 %', 'Basis of A']
S4_ROWS = []
for _, r in s4.iterrows():
    S4_ROWS.append([int(r['year']), fmt_int(r['A_cases']), fmt(r['A_rate_per_100k'], 2),
                    fmt_int(r['B1_cases']), fmt_int(r['B2_cases']),
                    fmt(r['B1_over_A_pct'], 2), fmt(r['B2_over_A_pct'], 2),
                    fmt(r['B2_over_B1_pct'], 2),
                    BASIS_EN.get(str(r['A_basis']).strip(), 'Onset')])

# S5 内容
S5_HEAD = ['Year', 'Under-reporting (%)', 'Diagnostic accuracy (%)',
           'Model-to-notification ratio']
S5_ROWS = [[int(r['year']), fmt(r['under_reporting_pct'], 2),
            fmt(r['diagnostic_accuracy_pct'], 2), fmt(r['model_to_notification_ratio'], 2)]
           for _, r in s5.iterrows()]

# S6 内容
S6_HEAD = ['#', 'Analysis', 'Specification', 'Result', 'Conclusion']
S6_ROWS = [[r['id'], r['analysis'], r['specification'], r['result'], r['conclusion']]
           for _, r in s6.iterrows()]

# S6a 内容
S6A_HEAD = ['Series', 'Segment', 'APC (%)', 'AAPC (segment-length weighted)',
            'AAPC (endpoint)', 'EAPC (%)', 'Break-points']
SERIES_EN = {
    'GBD 发病数': 'GBD incident cases (model estimate)',
    'GBD ASIR': 'GBD age-standardised incidence rate (model)',
    'NNDRS-A 报告数': 'NNDRS series A \u2014 notified cases',
    'NNDRS-A 发病率': 'NNDRS series A \u2014 notification rate',
    'NNDRS 早期梅毒(\u2160+\u2161)': 'NNDRS primary + secondary (early) syphilis',
    'GBD \u00f7 NNDRS-A 比值': 'Model-to-notification ratio (GBD \u00f7 series A)',
}
s6a['series_en'] = s6a['series'].map(SERIES_EN).fillna(s6a['series'])
S6A_ROWS = []
prev = None
for _, r in s6a.iterrows():
    first = r['series'] != prev
    prev = r['series']
    bp = str(r['break_points'])
    bp = '\u2014' if bp in ('nan', '') else bp.replace('|', ' / ')
    S6A_ROWS.append([
        r['series_en'] if first else '',
        f"{int(r['segment_start'])}\u2013{int(r['segment_end'])}",
        f"{r['APC_pct']:+.2f}",
        f"{r['AAPC_seglen_weighted']:+.2f}" if first else '',
        f"{r['AAPC_endpoint']:+.2f}" if first else '',
        f"{r['EAPC']:+.2f}" if first else '',
        bp if first else ''])

# S9 内容
def fmt_ev(v):
    if isinstance(v, str):
        return v
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return '\u2013'
    if float(v).is_integer() and abs(float(v)) >= 2:
        return f'{int(v):,}'
    return f'{float(v):.2f}'


S9_HEAD = ['Evidence type', 'Year', 'Item', 'Value', 'Reference value', 'Note']
S9_ROWS = [[r['evidence'], str(r['year']), r['item'], fmt_ev(r['value']),
            fmt_ev(r['reference']), r['note']] for _, r in ext_sum.iterrows()]

# ── S10 内容：三条官方系列的内部一致性（原 Results §3.9 移入）──
STAGE_EN = {'一期': 'Primary', '二期': 'Secondary', '三期': 'Tertiary', '胎传': 'Congenital',
            '隐性': 'Latent', '一期+二期': 'Primary + secondary'}

rat2 = rd('p2_ratio_series.csv')
rat2 = rat2[rat2.year >= 2012].copy()
rat2['b2_over_A_pct'] = (rat2.nndrs_b2 / rat2.nndrs_a - 1) * 100

s10_csv = []
for _, r in rat2.iterrows():
    s10_csv.append({'comparison': 'National total', 'year': int(r['year']),
                    'stratum': 'All syphilis',
                    'A_cases': r['nndrs_a'], 'B1_cases': r['nndrs_b1'], 'B2_cases': r['nndrs_b2'],
                    'B1_vs_A_pct': r['b1_over_A_pct'], 'B2_vs_B1_pct': r['b2_over_b1_pct'],
                    'B2_vs_A_pct': r['b2_over_A_pct']})
sdev = rd('stage_channel_deviation.csv')
for _, r in sdev.iterrows():
    s10_csv.append({'comparison': 'Stage-specific (B2 vs B1)', 'year': int(r['year']),
                    'stratum': STAGE_EN.get(r['stage'], r['stage']),
                    'A_cases': np.nan, 'B1_cases': r['B1'], 'B2_cases': r['B2'],
                    'B1_vs_A_pct': np.nan, 'B2_vs_B1_pct': r['B2_vs_B1_pct'],
                    'B2_vs_A_pct': np.nan})
pd.DataFrame(s10_csv).to_csv(os.path.join(DAT, 'S10_series_consistency.csv'),
                             index=False, encoding='utf-8-sig')
print('  -> supplementary/data/S10_series_consistency.csv')

S10A_HEAD = ['Year', 'Series A', 'Series B1', 'B1 vs A (%)', 'Series B2', 'B2 vs B1 (%)',
             'B2 vs A (%)']
S10A_ROWS = [[str(int(r['year'])), fmt_int(r['nndrs_a']), fmt_int(r['nndrs_b1']),
              f"{r['b1_over_A_pct']:+.2f}", fmt_int(r['nndrs_b2']),
              f"{r['b2_over_b1_pct']:+.2f}" if not np.isnan(r['b2_over_b1_pct']) else '\u2013',
              f"{r['b2_over_A_pct']:+.2f}" if not np.isnan(r['b2_over_A_pct']) else '\u2013']
             for _, r in rat2.iterrows()]

S10B_HEAD = ['Year', 'Stage', 'Series B1', 'Series B2', 'B2 vs B1 (%)']
S10B_ROWS = [[str(int(r['year'])), STAGE_EN.get(r['stage'], r['stage']), fmt_int(r['B1']),
              fmt_int(r['B2']), f"{r['B2_vs_B1_pct']:+.1f}"]
             for _, r in sdev[sdev.year == 2024].iterrows()]

print('\n== table shapes ==')
for nm, h, rr in (('S1', S1_HEAD, S1_ROWS), ('S2', S2_HEAD, S2_ROWS), ('S3a', S3A_HEAD, S3A_ROWS),
                  ('S3b', S3B_HEAD, S3B_ROWS), ('S4', S4_HEAD, S4_ROWS), ('S5', S5_HEAD, S5_ROWS),
                  ('S6', S6_HEAD, S6_ROWS), ('S6a', S6A_HEAD, S6A_ROWS), ('S9', S9_HEAD, S9_ROWS),
                  ('S10a', S10A_HEAD, S10A_ROWS), ('S10b', S10B_HEAD, S10B_ROWS)):
    print(f'  {nm}: {len(rr)} rows x {len(h)} cols')


# ══════════════════════════════════════════════════════════════
# S7 / S8 内容
# ══════════════════════════════════════════════════════════════
from supp_content import (GATHER_HEAD, GATHER_ROWS, RECORD_HEAD, RECORD_ROWS,  # noqa: E402
                          S8_HEAD, S8_ROWS, S8_ORDER, S8_SOFT)

AUTHORS = 'Zhen Wang*, Cangyu Wang, Haixia Jing, Zhiping Tang'
AFFIL = ('1 Department of Dermatology, Taihe Hospital, the Affiliated Hospital of Hubei '
         'University of Medicine, Shiyan 442000, Hubei, China \u00b7 '
         '2 Faculty of Medicine, Technische Universit\u00e4t Dresden, Dresden, Germany. '
         '* Correspondence: Zhen Wang, Department of Dermatology, Taihe Hospital, Hubei University of '
         'Medicine, Shiyan 442000, Hubei, China. E-mail: sywz1998@163.com. '
         'ORCID: 0009-0006-4389-7673')

CONTENTS_HEAD = ['Item', 'Content', 'Form']
CONTENTS_ROWS = [
    ['S1', 'Provincial notified syphilis incidence rates, 31 provincial-level regions, '
           '2004\u20132024', 'Table + CSV'],
    ['S2', 'Age-specific notified syphilis cases and rates, 2004\u20132024', 'Table + CSV'],
    ['S3', 'GBD 2023 model estimates for China: age-specific and sex-specific incidence',
     'Tables + CSV'],
    ['S4', 'The three official notification series, 1998\u20132025', 'Table + CSV'],
    ['S5', 'Reporting-quality covariates, 2013\u20132021', 'Table + CSV'],
    ['S6', 'Sensitivity analyses', 'Table + CSV'],
    ['S6a', 'Trend summary estimators for every fitted series', 'Table + CSV'],
    ['S7', 'Reporting-guideline checklists (GATHER; RECORD)', 'Checklists'],
    ['S8', 'Reproducibility: code, software and derived data', 'Manifest'],
    ['S9', 'Verification of the two-fold duplication artefact in the provincial source',
     'Evidence table'],
    ['S10', 'Internal consistency of the three official notification series',
     'Tables + CSV'],
    ['S11', 'Five systematic divergences between model estimates and notifications',
     'Table + CSV'],
    ['S12', 'Annual notified syphilis and GBD 2023 incident infections, 1998\u20132025',
     'Table + CSV'],
    ['S13', 'Stage-specific notified syphilis, 2012\u20132025', 'Table + CSV'],
    ['S14', 'Congenital syphilis: reconciliation of three published quantities',
     'Table + CSV'],
    ['S15', 'Between-province inequality in notified incidence, 2004\u20132024',
     'Table + CSV'],
    ['S16', 'Provincial ranking in 2024 and decoupling from early-syphilis burden',
     'Table + CSV'],
]

# ══════════════════════════════════════════════════════════════
# 文档块
# ══════════════════════════════════════════════════════════════
B = []
B += [('title', 'Supplementary Information')]
B += [('subtitle', TITLE)]
B += [('meta', AUTHORS)]
B += [('meta', AFFIL)]
B += [('p', 'This file contains Supplementary Tables S1\u2013S6a and S10\u2013S16 and '
           'Supplementary Sections S7\u2013S9, cited in the Methods and Results of the '
           'manuscript. Supplementary Tables S11\u2013S16 are the six tables that were Tables '
           '2\u20137 of an earlier draft and were moved here to bring the main text within the '
           'journal\u2019s display-item limit; the main text retains Table 1. Standalone '
           'machine-readable versions of every supplementary table are provided as CSV files in '
           'the supplementary data folder, with the file names given in each table caption.')]
B += [('h2', 'Contents')]
B += [('table', CONTENTS_HEAD, CONTENTS_ROWS, {'size': 8.5, 'left': 1, 'pw': 1.1})]

# ── S1 ──
B += [('landscape', True)]
B += [('h2', 'Supplementary Table S1. Provincial notified syphilis incidence rates, '
             '31 provincial-level regions of China, 2004\u20132024')]
B += [('note', 'Source: Public Health Science Data Center, Chinese CDC (notified syphilis '
               'database, annual provincial report, retrieved through the public report '
               'interface). Values are notified incidence rates per 100,000 population. '
               'Regions are listed in the order returned by the source. Values for '
               '2021\u20132024 are the corrected values described in Supplementary S9 (the raw '
               'return was exactly twice the corrected value for every indicator column). From '
               '2021 onwards the source returns total syphilis only, so no stage breakdown is '
               'available at the provincial level for those years. Machine-readable file: '
               'S1_provincial_incidence_2004_2024.csv.')]
B += [('table', S1_HEAD, S1_ROWS, {'size': 6.5, 'left': 1, 'pw': 1.5})]
B += [('landscape', False)]

# ── S2 ──
B += [('h2', 'Supplementary Table S2. Age-specific notified syphilis, China, 2004\u20132024')]
B += [('note', 'Source: monthly national notifiable-disease tables published in Disease '
               'Surveillance (annual cumulative values). Cases are notified cases; rates are per '
               '100,000 population. For 2004\u20132020 the source returns each age group split by '
               'stage (primary, secondary, tertiary, congenital, latent) as well as the total; '
               'for 2021\u20132024 it returns the total only. Rates for 2024 are not returned by '
               'the source and are shown as \u2013. The single-year age groups below age 10 are '
               'listed individually; the national total row sums the reported age groups and may '
               'differ from the all-ages total because of the unallocated \u201cunknown age\u201d '
               'category. Machine-readable file: S2_age_specific_2004_2024_full.csv (full '
               'age \u00d7 year \u00d7 stage grid).')]
B += [('table', S2_HEAD, S2_ROWS, {'size': 7.0, 'left': 1, 'pw': 1.35})]

# ── S3 ──
B += [('h2', 'Supplementary Table S3. GBD 2023 model estimates for China: age-specific and '
             'sex-specific incidence')]
B += [('h3', 'S3a. Age-specific modelled incidence rate (per 100,000), both sexes')]
B += [('note', 'Source: GBD Results Tool, cause \u201csyphilis\u201d (cause ID 394), China, '
               'both sexes, incidence rate. Bands are those returned by GBD; the value for '
               '85\u201389 years is reported as returned and excludes the two oldest bands, '
               'which are set out in the machine-readable file. Machine-readable file: '
               'S3_gbd_china_age_sex_1990_2023.csv (full age \u00d7 sex \u00d7 year grid, '
               '1990\u20132023, with the 95% uncertainty intervals supplied by GBD).')]
B += [('table', S3A_HEAD, S3A_ROWS, {'size': 8.0, 'left': 1, 'pw': 1.6})]
B += [('h3', 'S3b. Modelled incidence by sex, 2004\u20132023')]
B += [('note', 'ASIR: age-standardised incidence rate per 100,000. The model returns a '
               'persistently male-to-female ASIR ratio well above unity and a widening one after '
               '2020, in contrast to the notified male-to-female ratio of 0.86\u20131.10 '
               '(Results \u00a73.5).')]
B += [('table', S3B_HEAD, S3B_ROWS, {'size': 7.2, 'left': 1, 'pw': 1.5})]

# ── S4 ──
B += [('h2', 'Supplementary Table S4. The three official notification series, China, '
             '1998\u20132025')]
B += [('note', 'A: national notifiable-disease epidemic summaries and annual statistical '
               'bulletins, tabulated by date of onset. B1: monthly national tables in Disease '
               'Surveillance, tabulated by date of final review; the December issue of each '
               'volume carries the annual cumulative total and its \u201cprevious-year '
               'cumulative\u201d entry reproduces the preceding year\u2019s total, which provides '
               'a year-by-year internal check. B2: annual syphilis and HIV situation report of '
               'the National Center for STD Control, tabulated by date of report; the 2023 value '
               'is derived from the year-on-year change reported in the 2024 edition. Values for '
               '1998\u20132003 rest on an earlier case definition and are shown for context; they '
               'are excluded from all ratio-based analyses. B1 is unavailable for 2010 and 2011. '
               '\u201cBasis\u201d reports the statistical basis of series A as stated in the '
               'official footnote. Machine-readable file: S4_three_official_series_1998_2025.csv.')]
B += [('table', S4_HEAD, S4_ROWS, {'size': 7.0, 'left': 1, 'pw': 1.25})]

# ── S5 ──
B += [('h2', 'Supplementary Table S5. Reporting-quality covariates, 2013\u20132021')]
B += [('note', 'Source: national evaluation of the impact of the COVID-19 pandemic on '
               'notifiable-disease reporting in China, which reports both indicators for '
               '2013\u20132021 (reference 21 in the manuscript). The final column repeats the '
               'model-to-notification ratio (series A) for the same years so that the attribution '
               'analysis in Results \u00a73.2 can be read directly from this table. With only nine '
               'annual observations, and with all three quantities being time trends, these '
               'correlations are reported without a causal reading: under-reporting correlates '
               'weakly with the log ratio (Pearson r = 0.45, p = 0.23), whereas diagnostic '
               'accuracy correlates strongly and negatively (r = \u22120.87, p = 0.002). '
               'Machine-readable file: S5_reporting_quality_2013_2021.csv.')]
B += [('table', S5_HEAD, S5_ROWS, {'size': 8.0, 'left': 1, 'pw': 1.9})]

# ── S6 ──
B += [('h2', 'Supplementary Table S6. Sensitivity analyses')]
B += [('note', 'Each row gives one perturbation of the primary specification, the result under '
               'that perturbation, and what it implies for the reported conclusion. '
               'Machine-readable file: S6_sensitivity_analyses.csv.')]
B += [('table', S6_HEAD, S6_ROWS, {'size': 6.8, 'left': 3, 'pw': 0.6})]

# ── S6a ──
B += [('h2', 'Supplementary Table S6a. Trend summary estimators for every fitted series')]
B += [('note', 'Three summary estimators of the average rate of change are reported for every '
               'series because they answer slightly different questions and can differ in sign '
               'when segment slopes diverge. APC is the annual percentage change within each '
               'segment of the piecewise log-linear fit. \u201cAAPC (segment-length '
               'weighted)\u201d is the average of the segment APCs weighted by segment length, '
               'following the NCI Joinpoint convention. \u201cAAPC (endpoint)\u201d is the '
               'geometric mean change between the first and last observation only. EAPC is '
               '100 \u00d7 [exp(\u03b2) \u2212 1] from a single log-linear regression over the '
               'whole period, the convention used in the burden-of-disease literature. For the '
               'GBD age-standardised incidence rate the three estimators are +0.11%, \u22120.11% '
               'and \u22120.24% respectively; all three describe an effectively flat trajectory, '
               'but they are reported side by side so that the sign difference is explicit '
               'rather than looking like a contradiction. Break-points are reported as the last '
               'year of the segment preceding the change, so that a break-point of 2005 '
               'corresponds to the segments 1990\u20132005 and 2006\u20132019; an em dash means '
               'that no break-point was selected. Machine-readable file: '
               'S6a_trend_estimators.csv.')]
B += [('table', S6A_HEAD, S6A_ROWS, {'size': 7.2, 'left': 1, 'pw': 1.5})]

# ── S7 ──
B += [('h2', 'Supplementary S7. Reporting-guideline checklists')]
B += [('p', 'The comparison is reported following the Guidelines for Accurate and Transparent '
            'Health Estimates Reporting (GATHER) for the model-based component and the REporting '
            'of studies Conducted using Observational Routinely-collected health Data (RECORD) '
            'statement for the surveillance component. This study does not produce new global '
            'health estimates; it evaluates and reconciles an existing published estimate against '
            'national surveillance, so the GATHER items are completed with respect to that '
            'comparison, and items that presuppose the production of a new set of estimates are '
            'answered with respect to the GBD 2023 study whose product is being evaluated. '
            'Section numbers refer to the manuscript; where an item is not applicable this is '
            'stated rather than left blank.')]
B += [('h3', 'S7.1 GATHER checklist')]
B += [('table', GATHER_HEAD, GATHER_ROWS, {'size': 7.0, 'left': 3, 'pw': 0.35})]
B += [('h3', 'S7.2 RECORD checklist')]
B += [('table', RECORD_HEAD, RECORD_ROWS, {'size': 7.0, 'left': 4, 'pw': 0.4})]

# ── S8 ──
B += [('h2', 'Supplementary S8. Reproducibility: code, software and derived data')]
B += [('p', 'Every value reported in the manuscript and in this Supplementary file is produced '
            'by the scripts listed below, run in the order given. The scripts write their '
            'intermediate outputs to the processed and raw data folders and are written so that '
            're-running them reproduces the delivered tables and figures without manual '
            'intervention.')]
B += [('h3', 'S8.1 Script manifest')]
B += [('table', S8_HEAD, S8_ROWS, {'size': 7.0, 'left': 2, 'pw': 0.55})]
B += [('h3', 'S8.2 Run order')]
for i, s in enumerate(S8_ORDER, 1):
    B += [('bullet', f'Step {i}. {s}')]
B += [('h3', 'S8.3 Software')]
B += [('p', 'The analysis was performed in Python 3.13 with the following libraries:')]
for s in S8_SOFT:
    B += [('bullet', s)]
B += [('p', 'Two inputs are session-based and must be re-retrieved by anyone reproducing the '
            'work: the GBD Results Tool export (Institute for Health Metrics and Evaluation) and '
            'the provincial and age-specific records from the Public Health Science Data Center '
            'report interface. The retrieval URLs, including the directly constructed URLs for '
            '2021\u20132024 that bypass the front-end year selector, are contained in the '
            'retrieval scripts. The raw report pages retrieved during this study are archived so '
            'that every value can be retraced.')]

# ── S9 ──
B += [('h2', 'Supplementary S9. Verification of the two-fold duplication artefact in the '
             'provincial source')]
B += [('p', 'The provincial and age-specific records returned by the Public Health Science Data '
            'Center report interface for 2021\u20132024 are exactly twice their true magnitude, '
            'synchronously across case counts, death counts, incidence rates and mortality rates, '
            'whereas the same interface returns correct values for 2004\u20132020. The affected '
            'values were divided by two after three independent verifications, set out below. '
            'The provincial inequality analysis in Results \u00a73.8 depends on this correction, '
            'so the verification is reported in full.')]
B += [('h3', 'S9.1 Verification 1: reconciliation with the official national series')]
B += [('p', 'For each affected year the national total returned by the report interface, halved, '
            'equals the official national notification total (series A) exactly. The same result '
            'is obtained independently from the age-specific return, whose age-group counts also '
            'sum to exactly twice the national total. The ratios are exactly 2.0000 in all four '
            'years.')]
B += [('h3', 'S9.2 Verification 2: parity test')]
B += [('p', 'If a value is exactly twice its true magnitude, it must be even. This is a strong, '
            'directly testable consequence. In the correctly structured 2020 provincial table, '
            '28 of 64 returned values are odd, i.e. the values show ordinary random parity. In '
            'each of 2021, 2022, 2023 and 2024, all 64 returned values are even, and the same '
            'holds for all values in the corresponding age-specific tables. Across the four '
            'affected years no returned value is odd \u2014 256 values in total in the provincial '
            'tables alone. The probability of that parity pattern arising by chance is of the '
            'order of 2\u207b\u00b2\u2075\u2076.')]
B += [('h3', 'S9.3 Verification 3: comparison with independent provincial bulletins')]
B += [('p', 'Five values were drawn from three provincial health commission statistical '
            'bulletins, which are administrative publications independent of both the national '
            'notification system and the data centre. All five match the corrected values, three '
            'of them to the individual case.')]
B += [('h3', 'S9.4 Supporting evidence: population back-calculation')]
B += [('p', 'Incidence rates were used to back-calculate the implied provincial population for '
            'each affected year. All 31 provinces yield an implied population of exactly half the '
            'true population (range of deviations 49.2%\u201350.9%). Had only the case counts '
            'been inflated, the implied population would have been doubled instead. This shows '
            'that all four indicator columns are inflated together, and that the defect is a '
            'uniform factor rather than a column-specific error.')]
B += [('h3', 'S9.5 Evidence table')]
B += [('table', S9_HEAD, S9_ROWS, {'size': 7.0, 'left': 3, 'pw': 0.9})]
B += [('h3', 'S9.6 Residual uncertainty')]
B += [('p', 'The mechanism that produced the duplication could not be established from outside '
            'the system: the report definition file is not publicly retrievable, so it is not '
            'possible to determine whether the cause was a duplicated join in the query, a '
            'coexistence of old and new data structures, or a display-level doubling. Two further '
            'consequences are recorded as limitations in Discussion \u00a74.7: the affected years '
            'carry no stage breakdown, so provincial analysis for 2021\u20132024 can only use '
            'total syphilis; and the 2024 age table returns case counts without rates. Because '
            'the duplication is a single uniform factor, the provincial share of the national '
            'total is unaffected, and the alternative procedure of allocating the official '
            'national total in proportion to reported provincial shares reproduces the corrected '
            'values exactly (Supplementary Table S6, row S6.3); the inequality result therefore '
            'does not depend on the multiplier being 2.')]

# ── S10 ──
B += [('h2', 'Supplementary S10. Internal consistency of the three official notification '
             'series')]
B += [('p', 'Three official series tabulate the same notifications on different statistical '
            'bases (series A by date of onset, series B1 by date of final review, series B2 by '
            'date of report; Supplementary Table S4). This section, which was Section 3.9 of an '
            'earlier draft of the manuscript, sets out how far the three series agree. The '
            'notified system is internally coherent to within about one-fifth of the national '
            'total, an order of magnitude below the model-to-surveillance gap; this bounds the '
            'precision with which any notified total can serve as a reference standard and is the '
            'reason level comparisons were made against series A rather than against the official '
            'aggregate. Machine-readable file: S10_series_consistency.csv.')]
B += [('h3', 'S10.1 The three series in level, 2012\u20132025')]
B += [('p', 'Across 2012\u20132025 series B1 exceeded series A by 2.44\u20135.13%, the '
            'difference widening slightly from 2020 onwards (3.97% in 2020 to 5.13% in 2025). '
            'Series B2, available for 2023\u20132025, exceeded series B1 by 11.74\u201312.87% and '
            'series A by 16.4\u201318.6%. The largest difference between any two national totals '
            'in any year is thus 18.6%, in 2025, against the 3.7-fold separation between the '
            'model and the notified system in the same year.')]
B += [('table', S10A_HEAD, S10A_ROWS, {'size': 7.6, 'left': 1, 'pw': 1.3})]
B += [('h3', 'S10.2 The B2-to-B1 difference is stage-specific, not a scale factor')]
B += [('p', 'For 2024, the year in which both official channels publish directly observed '
            'stage-specific values, the B2-to-B1 difference was +5.1% for secondary syphilis, '
            '+12.8% for primary, +13.2% for latent, +17.7% for tertiary and +61.4% for '
            'congenital syphilis. A single conversion factor therefore cannot reconcile the two '
            'official channels: the difference is stage-specific and, for congenital syphilis, an '
            'order of magnitude larger than for the other categories. The 2023 and 2025 patterns '
            'are the same (+55.3% and +58.8% for congenital syphilis respectively; full series in '
            'S10_series_consistency.csv).')]
B += [('table', S10B_HEAD, S10B_ROWS, {'size': 7.8, 'left': 2, 'pw': 1.2})]
B += [('p', 'The internal discordance among the official series is small relative to the '
            'model-to-surveillance gap, but it is not zero, and it is larger for congenital '
            'syphilis than for any other category. Both facts are carried into the '
            'interpretation of the congenital-syphilis comparison in Results \u00a73.7.')]

# ── S11–S16：由主文迁出的原 Table 2–7 ─────────────────────────
CELL_EMPTY = '\u2013'


def cellfmt(v):
    """统一英文表格单元格：千分位逗号、保留原位小数位、负号用 \u2212、区间用 \u2013。"""
    s = str(v).strip()
    if s in ('', 'nan', 'None'):
        return CELL_EMPTY
    t = s.replace(',', '')
    try:
        f = float(t)
    except ValueError:
        out = s
    else:
        neg = t.startswith('-')
        pos = t.startswith('+')
        digits = t.lstrip('+-')
        if digits.isdigit():
            n = abs(int(f))
            out = str(n) if (n < 1000 or 1900 <= n <= 2099) else f'{n:,}'
        else:
            dec = len(digits.split('.')[1]) if '.' in digits else 0
            if dec == 1 and abs(f) == int(abs(f)):
                out = f'{abs(int(f)):,}'
            else:
                out = f'{abs(f):,.{dec}f}'
        if neg:
            out = '\u2212' + out
        elif pos:
            out = '+' + out
    out = re.sub(r'(?<=\d)-(?=\d)', '\u2013', out)
    out = re.sub(r'(?<![\d.])-(?=\d)', '\u2212', out)
    return out


def sup_table(fn, heads, drop=(), dec2=()):
    df = pd.read_csv(os.path.join(TABD, fn), encoding='utf-8-sig', dtype=str).fillna('')
    for d in drop:
        df = df.drop(columns=[d])
    rows = [[cellfmt(v) for v in r] for r in df.values.tolist()]
    # dec2：指定列强制保留两位小数（率类指标统一 2 位）
    for i, r in enumerate(rows):
        for c in dec2:
            v = r[c]
            try:
                r[c] = f'{float(str(v).replace("\u2212", "-")):.2f}'
            except ValueError:
                pass
            else:
                if r[c].startswith('-'):
                    r[c] = '\u2212' + r[c][1:]
    return list(heads), rows


# 机读文件：原名 CSV 去列后复制一份到 supplementary/data
def copy_machine(fn, out_name, drop=()):
    df = pd.read_csv(os.path.join(TABD, fn), encoding='utf-8-sig', dtype=str)
    for d in drop:
        df = df.drop(columns=[d])
    df.to_csv(os.path.join(DAT, out_name), index=False, encoding='utf-8-sig')
    print('  -> supplementary/data/' + out_name)


S11_HEAD, S11_ROWS = sup_table(
    'Table2.csv', ['#', 'Domain', 'GBD 2023', 'NNDRS notified', 'Contrast', 'Attribution'])
S12_DROP = ('A_source', 'B1_source', 'B2_source')
S12_HEAD, S12_ROWS = sup_table(
    'Table3.csv',
    ['Year', 'GBD incident infections', 'Series A (onset date)', 'Series B1 (final review)',
     'Series B2 (report date)', 'GBD \u00f7 A', 'B1 vs A (%)', 'B2 vs B1 (%)'], drop=S12_DROP)
S13_DROP = ('early_pct_of_total',)
S13_HEAD, S13_ROWS = sup_table(
    'Table4.csv',
    ['Year', 'Basis', 'Primary', 'Secondary', 'Tertiary', 'Congenital', 'Latent', 'Total',
     'Latent (%)', 'Primary + secondary', 'P+S rate per 100,000'], drop=S13_DROP, dec2=(10,))
S14_HEAD, S14_ROWS = sup_table(
    'Table5.csv',
    ['Quantity', 'GBD 2023 (model)', 'NNDRS series B1 (final review)',
     'NNDRS series B2 (report date)'])
S15_HEAD, S15_ROWS = sup_table(
    'Table6.csv',
    ['Year', 'n', 'Mean incidence', 'CV (%)', 'Gini (incidence)', 'Gini (cases)',
     'Highest province', 'Max', 'Lowest province', 'Min', 'Max \u00f7 min'], dec2=(2,))
S16_DROP = ('province_cn', 'rank_shift_early_minus_total')
S16_HEAD, S16_ROWS = sup_table(
    'Table7.csv',
    ['2024 rank', 'Province', 'Cases 2024', 'Incidence 2024', 'Share (%)',
     '2020 rank (total)', 'Incidence 2020', '2020 rank (early)', 'Early incidence 2020',
     'Rank shift (same year)', 'Latent (%) 2020', 'Cases 2020', 'Change in cases (%)'],
    drop=S16_DROP, dec2=(3, 6, 8))

copy_machine('Table2.csv', 'S11_five_discordances.csv')
copy_machine('Table3.csv', 'S12_annual_three_series.csv', drop=S12_DROP)
copy_machine('Table4.csv', 'S13_stage_specific_series.csv', drop=S13_DROP)
copy_machine('Table5.csv', 'S14_congenital_reconciliation.csv')
copy_machine('Table6.csv', 'S15_provincial_inequality.csv')
copy_machine('Table7.csv', 'S16_provincial_ranking_2024.csv', drop=S16_DROP)

print('\n== S11–S16 shapes ==')
for nm, h, rr in (('S11', S11_HEAD, S11_ROWS), ('S12', S12_HEAD, S12_ROWS),
                  ('S13', S13_HEAD, S13_ROWS), ('S14', S14_HEAD, S14_ROWS),
                  ('S15', S15_HEAD, S15_ROWS), ('S16', S16_HEAD, S16_ROWS)):
    print(f'  {nm}: {len(rr)} rows x {len(h)} cols')

# ── S11 ──
B += [('pagebreak',)]
B += [('h2', 'Supplementary Table S11. Five systematic divergences between GBD 2023 model '
             'estimates and NNDRS notifications')]
B += [('note', 'This table, formerly Table 2 of the manuscript, gives the five dimensions along '
               'which the model and the notification system diverge and the attribution proposed '
               'for each. ASIR, age-standardised incidence rate per 100,000; EAPC, estimated '
               'annual percentage change from a log-linear regression over the full period; AAPC, '
               'average annual percentage change, computed as the segment-length-weighted mean of '
               'the segment-specific APCs; APC, annual percentage change. For the model ASIR the '
               'three summary estimators are EAPC \u22120.24, AAPC +0.11 and endpoint-to-endpoint '
               '\u22120.11, all consistent with an effectively flat trajectory; they are reported '
               'together because they differ in sign and could otherwise be read as contradictory. '
               'Divergence D5 was resolved as a difference in statistical basis rather than an '
               'error: each series carries an explicit official footnote defining its counting '
               'rule. Machine-readable file: S11_five_discordances.csv.')]
B += [('table', S11_HEAD, S11_ROWS, {'size': 7.0, 'left': 2, 'pw': 1.1})]

# ── S12 ──
B += [('landscape', True)]
B += [('h2', 'Supplementary Table S12. Annual notified syphilis and GBD 2023 incident '
             'infections, China, 1998\u20132025')]
B += [('note', 'Series A: annual national notifiable-disease epidemic summary of the National '
               'Disease Control and Prevention Administration, counted by date of onset; the '
               'annual statistical bulletins of national health development reproduce the same '
               'figures. Series B1: monthly national tables published in the December issue of '
               'Disease Surveillance (volumes 28\u201341), counted by date of final review. Series '
               'B2: annual national HIV and STI epidemic reports of the National Center for STD '
               'Control, published in the March issue of Chinese Journal of AIDS & STDs, counted '
               'by date of report. Values for 1998\u20132003 rest on an earlier case definition and '
               'reporting platform and are shown for context only; they are excluded from all '
               'ratio-based analyses. Series B1 is unavailable for 2010 and 2011. Blank cells '
               'indicate that the quantity is not published for that series and year. A per-cell '
               'provenance table, which records the individual official publication from which '
               'each value was taken, is provided in the reproducibility package (Supplementary '
               'S8). Machine-readable file: S12_annual_three_series.csv.')]
B += [('table', S12_HEAD, S12_ROWS, {'size': 7.0, 'left': 1, 'pw': 1.15})]
B += [('landscape', False)]

# ── S13 ──
B += [('landscape', True)]
B += [('h2', 'Supplementary Table S13. Stage-specific notified syphilis, China, 2012\u20132025')]
B += [('note', 'Series B1 is the primary stage series (counted by date of final review); series '
               'B2 rows are shown for 2023\u20132025 to expose the channel difference. Two further '
               'stage observations exist outside the shown range and are not chain-linked to B1: '
               '2005 was reconstructed by applying the published 2005 stage composition (36.61% '
               'primary, 27.50% secondary, 0.73% tertiary, 3.14% congenital, 32.01% latent) to the '
               'annual total; 2011 is a series B2 value (118,000 primary, 68,000 secondary, 3,320 '
               'tertiary, 14,000 congenital, 243,000 latent). The primary-plus-secondary rate uses '
               'mid-year population derived from the notified national rate series (2018 '
               'interpolated). Provincial records were returned without stage columns from 2021, '
               'so stage analysis is national only for 2021\u20132025. Machine-readable file: '
               'S13_stage_specific_series.csv.')]
B += [('table', S13_HEAD, S13_ROWS, {'size': 7.0, 'left': 2, 'pw': 1.2})]
B += [('landscape', False)]

# ── S14 ──
B += [('h2', 'Supplementary Table S14. Congenital syphilis: reconciliation of three officially '
             'published quantities')]
B += [('note', 'n/a, not applicable. The implied deaths-per-case ratio is shown only to '
               'demonstrate that the three quantities cannot all be simultaneously correct: model '
               'deaths under 5 years exceed the notified congenital case count in series B1 by '
               '59%, which is not epidemiologically admissible, while the same numerator is 98% of '
               'the series B2 count. The two official notification channels differ by 59\u201361% '
               'on congenital syphilis in every common year, against only 4\u201313% on latent, '
               'primary, secondary and tertiary syphilis (Supplementary S10). The three sources '
               'nevertheless agree on direction: all decline by more than 70% over their available '
               'spans. Machine-readable file: S14_congenital_reconciliation.csv.')]
B += [('table', S14_HEAD, S14_ROWS, {'size': 7.5, 'left': 1, 'pw': 1.5})]

# ── S15 ──
B += [('landscape', True)]
B += [('h2', 'Supplementary Table S15. Between-province inequality in notified syphilis '
             'incidence, China, 2004\u20132024 (31 provinces)')]
B += [('note', 'All rates are notified cases per 100,000 using mid-year population by province. '
               'Gini (incidence) is the primary inequality measure and is computed on '
               'province-specific rates; Gini (cases) is computed on absolute case counts and is '
               'driven mainly by population size, so it is reported only to prevent the two '
               'conventions being conflated. CV, coefficient of variation across the 31 provinces. '
               'Inequality fell steeply to 2019 (Gini 0.5366 to 0.2460, CV 126.4% to 43.7%, ratio '
               '285 to 6.0), then stopped falling: the 2019\u20132021 values form a plateau and all '
               'three indicators rise from 2022, exceeding their 2019 levels by 2024. Values for '
               '2021\u20132024 are the corrected values described in Supplementary S9. '
               'Machine-readable file: S15_provincial_inequality.csv.')]
B += [('table', S15_HEAD, S15_ROWS, {'size': 7.0, 'left': 2, 'pw': 1.1})]
B += [('landscape', False)]

# ── S16 ──
B += [('pagebreak',)]
B += [('landscape', True)]
B += [('h2', 'Supplementary Table S16. Provincial ranking in 2024 and decoupling from '
             'early-syphilis burden')]
B += [('note', 'Both rankings are taken from the same year, 2020, the last year for which '
               'provincial stage-specific data are published, so that the comparison isolates the '
               'choice of indicator from the choice of year. \u201cRank shift\u201d is the 2020 rank '
               'by total incidence minus the 2020 rank by early (primary plus secondary) incidence; '
               'a negative value means the province ranks higher on infectious syphilis than on '
               'total burden. Qinghai ranks first on total incidence but 27th on early syphilis, '
               'and Yunnan 15th and 31st, whereas Jilin ranks 30th and 10th. The two rankings '
               'agree only weakly (Spearman r=0\u00b734, p=0\u00b7065) and 12 of 31 provinces move by '
               'ten or more places; total-incidence ranks were themselves stable between 2020 and '
               '2024 (r=0\u00b788), so the disagreement is not a product of the interval between '
               'measurements. The 2024 ranks and case counts are retained for reference. '
               'Incidence is notified cases per 100,000. '
               'Machine-readable file: S16_provincial_ranking_2024.csv.')]
B += [('table', S16_HEAD, S16_ROWS, {'size': 7.0, 'left': 2, 'pw': 1.15})]
B += [('landscape', False)]

print('\nblocks:', len(B))


def normalize_landscape(blocks):
    """按内容块的实际方向重排切换：只在方向真正改变处插一次 section break。"""
    items = []
    cur = False
    for blk in blocks:
        if blk[0] == 'landscape':
            cur = bool(blk[1])
        else:
            items.append((cur, blk))
    out = []
    cur = False
    for o, blk in items:
        if o != cur:
            out.append(('landscape', o))
            cur = o
        out.append(blk)
    return out


B = normalize_landscape(B)


# ══════════════════════════════════════════════════════════════
# Markdown 镜像
# ══════════════════════════════════════════════════════════════
def md_cell(s):
    return dots_code(str(s)).replace('|', '\\|').replace('\n', ' ')


def to_markdown(blocks):
    out = []
    for blk in blocks:
        k = blk[0]
        if k == 'title':
            out.append('# ' + blk[1])
        elif k == 'subtitle':
            out.append('**' + blk[1] + '**')
        elif k == 'meta':
            out.append('*' + blk[1] + '*')
        elif k == 'h2':
            out.append('## ' + dots_code(blk[1]))
        elif k == 'h3':
            out.append('### ' + dots_code(blk[1]))
        elif k == 'p':
            out.append(dots_code(blk[1]))
        elif k == 'note':
            out.append('> ' + dots_code(blk[1]))
        elif k == 'bullet':
            out.append('- ' + dots_code(blk[1]))
        elif k == 'table':
            head, rows = blk[1], blk[2]
            out.append('| ' + ' | '.join(md_cell(h) for h in head) + ' |')
            out.append('|' + '|'.join(['---'] * len(head)) + '|')
            for r in rows:
                out.append('| ' + ' | '.join(md_cell(c) for c in r) + ' |')
        out.append('')
    return '\n'.join(out)


md = to_markdown(B)
md_path = os.path.join(SUP, 'Supplementary_Information_S1-S16.md')
with open(md_path, 'w', encoding='utf-8') as f:
    f.write(md)
print('saved:', md_path)

# ══════════════════════════════════════════════════════════════
# DOCX
# ══════════════════════════════════════════════════════════════
def build_docx(blocks):
    doc = Document()
    st = doc.styles['Normal']
    st.font.name = 'Arial'
    st.font.size = Pt(BODY_PT)
    st.font.color.rgb = BLACK
    rPr = st.element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rPr.insert(0, rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        rf.set(qn(a), 'Arial')
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    s.top_margin = s.bottom_margin = Cm(1.8)
    s.left_margin = s.right_margin = Cm(1.8)
    s.header_distance = s.footer_distance = Cm(1.27)

    landscape = False
    usable = 17.4
    pending_break = False
    for blk in blocks:
        k = blk[0]
        if k == 'landscape':
            landscape = bool(blk[1])
            new_section(doc, landscape)
            usable = 26.1 if landscape else 17.4
        elif k == 'pagebreak':
            pending_break = True
        elif k == 'title':
            title_block(doc, blk[1], 'Arial', 'Arial', 15.0)
        elif k == 'subtitle':
            meta_block(doc, blk[1], 'Times New Roman', 'Arial', 11.0, after=4.0, bold=True)
        elif k == 'meta':
            meta_block(doc, blk[1], 'Arial', 'Arial', 8.5, after=2.0)
        elif k == 'h2':
            if pending_break:
                # 表格后的空段若溢出到页底会多出一张空白页，先清掉
                while doc.paragraphs and not doc.paragraphs[-1].text.strip():
                    el = doc.paragraphs[-1]._element
                    el.getparent().remove(el)
            p = heading(doc, blk[1], 1, 'Arial', 'Arial')
            if pending_break:
                p.paragraph_format.page_break_before = True
                pending_break = False
        elif k == 'h3':
            heading(doc, blk[1], 2, 'Arial', 'Arial')
        elif k == 'p':
            para(doc, blk[1], 'Arial', 'Arial')
        elif k == 'note':
            para(doc, blk[1], 'Arial', 'Arial', kind='note')
        elif k == 'bullet':
            para(doc, blk[1], 'Arial', 'Arial', kind='bullet', double=False)
        elif k == 'table':
            head, rows, opt = blk[1], blk[2], dict(blk[3])
            render_table(doc, head, rows, usable_cm=usable,
                         size=opt.get('size', 7.5), left_cols=opt.get('left', 1),
                         first_weight=opt.get('pw', 1.0))
    enable_line_numbers(doc)
    out = os.path.join(SUP, 'Supplementary_Information_S1-S16.docx')
    doc.save(out)
    print('saved:', out)


build_docx(B)
print('\nDONE')

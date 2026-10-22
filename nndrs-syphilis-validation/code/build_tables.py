# -*- coding: utf-8 -*-
"""
定稿 Table 1–7（CSV 数据层）
输出到 tables/Table1.csv ... Table7.csv
英文表头与内容（与英文投稿稿一致）；省份同时保留中文列 province_cn。
"""
import os, sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, 'raw')
PROC = os.path.join(BASE, 'processed')
TAB = os.path.join(BASE, 'tables')
os.makedirs(TAB, exist_ok=True)

PROV_EN = {
    '北京市': 'Beijing', '天津市': 'Tianjin', '河北省': 'Hebei', '山西省': 'Shanxi',
    '内蒙古自治区': 'Inner Mongolia', '辽宁省': 'Liaoning', '吉林省': 'Jilin',
    '黑龙江省': 'Heilongjiang', '上海市': 'Shanghai', '江苏省': 'Jiangsu',
    '浙江省': 'Zhejiang', '安徽省': 'Anhui', '福建省': 'Fujian', '江西省': 'Jiangxi',
    '山东省': 'Shandong', '河南省': 'Henan', '湖北省': 'Hubei', '湖南省': 'Hunan',
    '广东省': 'Guangdong', '广西': 'Guangxi', '海南省': 'Hainan', '重庆市': 'Chongqing',
    '四川省': 'Sichuan', '贵州省': 'Guizhou', '云南省': 'Yunnan', '西藏': 'Tibet',
    '陕西省': 'Shaanxi', '甘肃省': 'Gansu', '青海省': 'Qinghai', '宁夏': 'Ningxia',
    '新疆': 'Xinjiang',
}


def w(df, name):
    p = os.path.join(TAB, name)
    df.to_csv(p, index=False, encoding='utf-8-sig')
    print(f'  -> tables/{name}  ({df.shape[0]} x {df.shape[1]})')


def n(v, d=0):
    if v in ('', None) or (isinstance(v, float) and math.isnan(v)):
        return ''
    return f'{v:,.{d}f}'


import math

# ══════════════════════════════════════════════════════════════
# Table 1  构念与口径对照
# ══════════════════════════════════════════════════════════════
t1 = pd.DataFrame([
    ['Publisher', 'IHME, Global Burden of Disease 2023',
     'National Disease Control and Prevention Administration (NDCPA): annual national notifiable-disease summary',
     'NDCPA monthly statistics / China CDC, Disease Surveillance, December issue',
     'China CDC National Center for STD Control: annual national STD epidemic report'],
    ['Numerator construct', 'Modelled incident infections (symptomatic and asymptomatic)',
     'Clinically diagnosed and laboratory-confirmed notified cases',
     'Notified cases', 'Reported cases'],
    ['Statistical basis (official footnote)', 'Model-based estimate; not case-based',
     'Counted by date of onset', 'Counted by date of final review', 'Counted by date of report'],
    ['Unit', 'Cases; rate per 100,000 (age-standardised)',
     'Cases; rate per 100,000', 'Cases', 'Cases'],
    ['Temporal coverage', '1990-2023', '1998-2025', '2004-2025', '2011, 2023-2025'],
    ['Spatial resolution', 'National only',
     'National (provincial 2004-2024 via the Public Health Science Data Centre)',
     'National', 'National'],
    ['Stage resolution', 'None', 'Total (by stage at national level 2004-2020)',
     'Five stages, 2012-2025 (primary, secondary, tertiary, congenital, latent)',
     'Five stages, 2023-2025'],
    ['Age / sex resolution', '25 age groups \u00d7 2 sexes',
     'Age: 26 national groups; sex: literature series only',
     'Age: 26 national groups', 'Sex ratio reported'],
    ['Uncertainty', '95% uncertainty interval for every estimate', 'Not reported', 'Not reported', 'Not reported'],
    ['Congenital syphilis', 'Modelled deaths and DALYs under 5 years',
     'Notified congenital cases', 'Notified congenital cases', 'Notified congenital cases'],
], columns=['Attribute', 'GBD 2023 model estimate', 'NNDRS series A (onset date)',
            'NNDRS series B1 (final-review date)', 'NNDRS series B2 (report date)'])
w(t1, 'Table1.csv')

# ══════════════════════════════════════════════════════════════
# Table 2  五个背离
# ══════════════════════════════════════════════════════════════
t2 = pd.DataFrame([
    ['D1', 'Level', '1,957,724 incident infections (2023); ASIR 144.2 per 100,000',
     '530,116 notified cases (series A, 2023); 37.60 per 100,000',
     '3.69-fold in cases; 3.84-fold in rate',
     'Undiagnosed infections rather than under-reporting (under-reporting 1.29% to 0.33%)'],
    ['D2', 'Trend direction',
     'ASIR 149.4 (1990) to 144.2 (2023), effectively flat: EAPC -0.24, joinpoint AAPC +0.11 (segments +1.06, -1.52, +2.02); modelled incident cases -1.83% per year over 2010-2023',
     'Primary + secondary syphilis 176,291 (2012) to 42,669 (2025): -75.8%; single-segment APC -10.0',
     'Notified early syphilis falls 5.5-fold faster than modelled incident cases (APC -10.0 vs -1.83, 2010/2012-2023/2025); over 2006-2019 model incidence falls (-1.52 per year) while notified cases rise (+2.19 per year)',
     'Notified burden sustained by expanded detection of latent infection (stock-to-flow)'],
    ['D3', 'Sex structure', 'Male:female ASIR 3.44:1 (217.9 vs 63.3 per 100,000)',
     'Male:female notified ratio 0.86-0.96:1 (2014-2019, literature series); 1.04:1 (2024) and 1.10:1 (2025) from official reports',
     '3.6-fold divergence',
     'Antenatal screening preferentially detects latent infection in women'],
    ['D4', 'Congenital syphilis',
     '831 deaths under 5 years (2023), 85.7% of all syphilis deaths; 74,727 DALYs',
     '523 notified congenital cases (2024); 675 in 2023; 371 in 2025',
     'Implied fatality 159.0% (831/523) vs 98.5% against series B2 (844)',
     'Three-way definitional conflict; the two official channels differ by 59-61%'],
    ['D5', 'Internal consistency of the surveillance system', 'A single estimate per year',
     'Three parallel official series (A, B1, B2)',
     'B1 4.4% above A (2024); B2 12.8% above B1 (2025)',
     'Different statistical bases: onset date, final-review date, report date'],
], columns=['#', 'Domain', 'GBD 2023', 'NNDRS notified', 'Contrast', 'Attribution'])
w(t2, 'Table2.csv')

# ══════════════════════════════════════════════════════════════
# Table 3  年度三源序列
# ══════════════════════════════════════════════════════════════
ann = pd.read_csv(os.path.join(RAW, 'NNDRS_syphilis_annual.csv'), encoding='utf-8-sig')
ann.columns = [c.strip().lstrip('\ufeff') for c in ann.columns]
rat = pd.read_csv(os.path.join(PROC, 'p2_ratio_series.csv'), encoding='utf-8-sig')
gbd = pd.read_csv(os.path.join(PROC, 'gbd_incidence_series.csv'), encoding='utf-8-sig')

def src(tag):
    s = ann[ann['系列'].str.startswith(tag)].set_index('年份')['来源']
    return s.to_dict()

rows = []
for y in range(1998, 2026):
    g = gbd.loc[gbd.year == y, 'gbd_cases_both']
    r = rat[rat.year == y]
    rows.append({
        'year': y,
        'GBD_incident_infections': n(g.iloc[0]) if len(g) else '',
        'series_A_onset_date': n(r.nndrs_a.iloc[0]) if len(r) else '',
        'series_B1_final_review': n(r.nndrs_b1.iloc[0]) if len(r) else '',
        'series_B2_report_date': n(r.nndrs_b2.iloc[0]) if len(r) else '',
        'GBD_over_A': r.gbd_over_A.iloc[0] if len(r) else '',
        'B1_vs_A_pct': r.b1_over_A_pct.iloc[0] if len(r) else '',
        'B2_vs_B1_pct': r.b2_over_b1_pct.iloc[0] if len(r) else '',
        'A_source': src('A').get(y, ''),
        'B1_source': src('B1').get(y, ''),
        'B2_source': src('B2').get(y, ''),
    })
w(pd.DataFrame(rows), 'Table3.csv')

# ══════════════════════════════════════════════════════════════
# Table 4  分型序列
# ══════════════════════════════════════════════════════════════
st = pd.read_csv(os.path.join(RAW, 'NNDRS_syphilis_stage.csv'), encoding='utf-8-sig')
st.columns = [c.strip().lstrip('\ufeff') for c in st.columns]
pop = pd.read_csv(os.path.join(PROC, 'china_population_derived.csv'), encoding='utf-8-sig').set_index('year')['population']

rows = []
sel = st[(st['年份'] >= 2012) & (st['口径'].str.contains('B1'))].sort_values('年份')
b2 = st[st['口径'].str.contains('B2')].sort_values('年份')
for _, r in pd.concat([sel, b2]).iterrows():
    y = int(r['年份'])
    basis = 'B1 (final-review date)' if 'B1' in r['口径'] else 'B2 (report date)'
    tot = float(r['梅毒合计']); early = float(r['一期+二期'])
    p = pop.get(y, np.nan)
    rows.append({
        'year': y, 'basis': basis,
        'primary': n(r['一期']), 'secondary': n(r['二期']), 'tertiary': n(r['三期']),
        'congenital': n(r['胎传']), 'latent': n(r['隐性']), 'total': n(tot),
        'latent_pct': f"{float(r['隐性占比(%)']):.2f}",
        'primary_plus_secondary': n(early),
        'early_pct_of_total': f'{early / tot * 100:.2f}',
        'early_rate_per_100k': f'{early / p * 1e5:.2f}' if p == p else '',
    })
w(pd.DataFrame(rows), 'Table4.csv')

# ══════════════════════════════════════════════════════════════
# Table 5  先天梅毒三方对账
# ══════════════════════════════════════════════════════════════
gs = gbd.set_index('year')
b1 = {int(r['年份']): r for _, r in st[st['口径'].str.contains('B1')].iterrows()}
b2d = {int(r['年份']): r for _, r in st[st['口径'].str.contains('B2')].iterrows()}
t5 = pd.DataFrame([
    ['Notified congenital cases, 2023', 'Not modelled as cases',
     n(b1[2023]['胎传']), n(b2d[2023]['胎传'])],
    ['Notified congenital cases, 2024', 'Not modelled as cases',
     n(b1[2024]['胎传']), n(b2d[2024]['胎传'])],
    ['Notified congenital cases, 2025', 'Not modelled as cases',
     n(b1[2025]['胎传']), n(b2d[2025]['胎传'])],
    ['Deaths under 5 years, 2023', n(gs.loc[2023, 'gbd_u5_deaths_both']),
     'Not reported', 'Not reported'],
    ['DALYs under 5 years, 2023', n(gs.loc[2023, 'gbd_u5_daly_both']),
     'Not reported', 'Not reported'],
    ['Share of all syphilis deaths, 2023', f"{gs.loc[2023, 'gbd_u5_deaths_both'] / gs.loc[2023, 'gbd_deaths_both'] * 100:.1f}%",
     'n/a', 'n/a'],
    ['Implied deaths per notified case, 2024',
     'n/a',
     f"{gs.loc[2023, 'gbd_u5_deaths_both'] / float(b1[2024]['胎传']) * 100:.1f}%",
     f"{gs.loc[2023, 'gbd_u5_deaths_both'] / float(b2d[2024]['胎传']) * 100:.1f}%"],
    ['B2 relative to B1, 2024', 'n/a', 'reference',
     f"+{(float(b2d[2024]['胎传']) / float(b1[2024]['胎传']) - 1) * 100:.0f}%"],
    ['Change over available span',
     f"Deaths under 5 y: {(gs.loc[2023, 'gbd_u5_deaths_both'] / gs.loc[1990, 'gbd_u5_deaths_both'] - 1) * 100:.1f}% (1990-2023); "
     f"DALYs {(gs.loc[2023, 'gbd_u5_daly_both'] / gs.loc[1990, 'gbd_u5_daly_both'] - 1) * 100:.1f}%",
     f"Notified cases: {(float(b1[2025]['胎传']) / float(b1[2012]['胎传']) - 1) * 100:.1f}% (2012-2025)",
     f"Notified cases: {(float(b2d[2025]['胎传']) / float(b2d[2023]['胎传']) - 1) * 100:.1f}% (2023-2025)"],
], columns=['Quantity', 'GBD 2023 (model)', 'NNDRS series B1 (final-review date)',
            'NNDRS series B2 (report date)'])
w(t5, 'Table5.csv')

# ══════════════════════════════════════════════════════════════
# Table 6  省际不平等
# ══════════════════════════════════════════════════════════════
ineq = pd.read_csv(os.path.join(PROC, 'province_inequality_2004_2024.csv'), encoding='utf-8-sig')
ineq['max_prov_en'] = ineq.max_prov.map(lambda p: PROV_EN.get(p, p))
ineq['min_prov_en'] = ineq.min_prov.map(lambda p: PROV_EN.get(p, p))
t6 = pd.DataFrame({
    'year': ineq.year,
    'provinces': ineq.n_prov,
    'mean_incidence_per_100k': ineq.mean_inc.map(lambda v: f'{v:.3f}'),
    'CV_pct': ineq.cv_pct.map(lambda v: f'{v:.2f}'),
    'Gini_incidence': ineq.gini_rate.map(lambda v: f'{v:.4f}'),
    'Gini_cases': ineq.gini_cases.map(lambda v: f'{v:.4f}'),
    'highest_province': ineq.max_prov_en,
    'max_incidence': ineq.max_inc.map(lambda v: f'{v:.2f}'),
    'lowest_province': ineq.min_prov_en,
    'min_incidence': ineq.min_inc.map(lambda v: f'{v:.2f}'),
    'max_over_min': ineq.max_min_ratio.map(lambda v: f'{v:.1f}'),
})
w(t6, 'Table6.csv')

# ══════════════════════════════════════════════════════════════
# Table 7  2024 省排名 × 2020 早期率排名（解耦）
# ══════════════════════════════════════════════════════════════
r24 = pd.read_csv(os.path.join(PROC, 'province_2024_rank.csv'), encoding='utf-8-sig')
r20 = pd.read_csv(os.path.join(PROC, 'province_2020_rank.csv'), encoding='utf-8-sig')
r20 = r20.rename(columns={'rank': 'rank2020_total'})
early_rank = r20[['province', 'rank2020_total', 'early_incidence', 'incidence_2020',
                   'covert_pct', 'cases_2020']].copy()
early_rank['rank_early2020'] = early_rank.early_incidence.rank(ascending=False, method='min').astype(int)

t7 = r24.merge(early_rank, on='province', how='left')
t7['province_cn'] = t7.province
t7['province'] = t7.province.map(lambda p: PROV_EN.get(p, p))
t7['cases_change_2020_2024_pct'] = ((t7.cases_2024 / t7.cases_2020 - 1) * 100).map(lambda v: f'{v:+.1f}')
t7['rank_shift_early_minus_total'] = (t7['rank_early2020'] - t7['rank']).astype(int)
t7['rank_shift_early_vs_total_2020'] = (t7['rank_early2020'] - t7['rank2020_total']).astype(int)
t7 = t7[['rank', 'province', 'province_cn', 'cases_2024', 'incidence_2024',
         'share_of_national_pct', 'rank2020_total', 'incidence_2020',
         'rank_early2020', 'early_incidence',
         'rank_shift_early_vs_total_2020', 'rank_shift_early_minus_total',
         'covert_pct', 'cases_2020', 'cases_change_2020_2024_pct']]
t7.columns = ['rank_by_total_incidence_2024', 'province', 'province_cn', 'cases_2024',
              'incidence_2024_per_100k', 'share_of_national_2024_pct',
              'rank_by_total_incidence_2020', 'incidence_2020_per_100k',
              'rank_by_early_incidence_2020', 'early_incidence_2020_per_100k',
              'rank_shift_early_vs_total_2020', 'rank_shift_early_minus_total',
              'latent_pct_2020', 'cases_2020', 'change_in_cases_2020_to_2024_pct']
w(t7, 'Table7.csv')

print('\n全部表格完成。')

# -*- coding: utf-8 -*-
import csv, sys, os, collections
sys.stdout.reconfigure(encoding='utf-8')
os.makedirs('processed', exist_ok=True)

f = lambda v: float(v) if v not in ('', None) else 0.0
prov = list(csv.DictReader(open('raw/NNDRS_province_syphilis_2004_2020.csv', encoding='utf-8-sig')))

# 归一化
NORM = {'全 国': '全国', '全国': '全国', '宁 夏': '宁夏', '宁夏': '宁夏', '广 西': '广西',
        '广西': '广西', '新 疆': '新疆', '新疆': '新疆', '西 藏': '西藏', '西藏': '西藏',
        '黑龙江': '黑龙江省', '黑龙江省': '黑龙江省', '内蒙古': '内蒙古自治区',
        '内蒙古自治区': '内蒙古自治区'}
for r in prov:
    r['group'] = NORM.get(r['group'], r['group']).replace(' ', '')

# ---- A. 2019 -> 2020 各省变化 ----
d = collections.defaultdict(dict)
for r in prov:
    if r['stage'] == '梅毒(合计)':
        d[r['group']][r['year']] = r
rows = []
for p in sorted(k for k in d if k != '全国'):
    a = d[p].get('2019', {}); b = d[p].get('2020', {})
    c19 = f(a.get('cases', '')); c20 = f(b.get('cases', ''))
    rows.append({'province': p, 'cases_2019': c19, 'cases_2020': c20,
                 'change_pct': round((c20 - c19) / c19 * 100, 1) if c19 else '',
                 'inc_2019': a.get('incidence_per100k', ''), 'inc_2020': b.get('incidence_per100k', '')})
rows.sort(key=lambda x: x['change_pct'] if x['change_pct'] != '' else 0)
with open('processed/province_2019_2020_change.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('=== 2019->2020 降幅最大 5 省 / 上升 5 省 ===')
for r in rows[:5] + rows[-5:]:
    print(f"  {r['province']:<8} {r['cases_2019']:>8.0f} -> {r['cases_2020']:>8.0f}  {r['change_pct']:>6}%")

# ---- B. 全国分型年度序列（来自省表全国行）----
STAGES = ['I期梅毒', 'II期梅毒', 'III期梅毒', '胎传梅毒', '隐性梅毒', '梅毒(合计)']
nat = collections.defaultdict(dict)
for r in prov:
    if r['group'] == '全国':
        nat[r['year']][r['stage']] = r
years = [str(y) for y in range(2004, 2021)]
out = []
for y in years:
    if y not in nat:
        continue
    tot = f(nat[y].get('梅毒(合计)', {}).get('cases', ''))
    hi = f(nat[y].get('隐性梅毒', {}).get('cases', ''))
    e12 = f(nat[y].get('I期梅毒', {}).get('cases', '')) + f(nat[y].get('II期梅毒', {}).get('cases', ''))
    e12i = f(nat[y].get('I期梅毒', {}).get('incidence_per100k', '')) + f(nat[y].get('II期梅毒', {}).get('incidence_per100k', ''))
    out.append({'year': y, 'total_cases': tot,
                'total_incidence': nat[y].get('梅毒(合计)', {}).get('incidence_per100k', ''),
                'early_cases_I_II': e12, 'early_incidence_I_II': round(e12i, 4),
                'covert_cases': hi, 'covert_pct': round(hi / tot * 100, 2) if tot else '',
                'congenital_cases': f(nat[y].get('胎传梅毒', {}).get('cases', ''))})
with open('processed/national_stage_annual_2004_2020.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)

print()
print('=== 全国 2004-2020（数据中心口径）===')
print('year  总发病   I+II期   I+II发病率  隐性  隐性占比  胎传')
for r in out:
    print(f"{r['year']} {r['total_cases']:>9.0f} {r['early_cases_I_II']:>9.0f} {r['early_incidence_I_II']:>10.3f} "
          f"{r['covert_cases']:>9.0f} {r['covert_pct']:>8.2f}% {r['congenital_cases']:>6.0f}")

# -*- coding: utf-8 -*-
"""加工：归一化省名 -> 宽表 / 不平等指标 / 分型构成 / 年龄分布"""
import csv, sys, os, re, math
import collections
sys.stdout.reconfigure(encoding='utf-8')

os.makedirs('processed', exist_ok=True)

NORM = {
    '全 国': '全国', '全国': '全国',
    '宁 夏': '宁夏', '宁夏': '宁夏',
    '广 西': '广西', '广西': '广西',
    '新 疆': '新疆', '新疆': '新疆',
    '西 藏': '西藏', '西藏': '西藏',
    '黑龙江': '黑龙江省', '黑龙江省': '黑龙江省',
    '内蒙古': '内蒙古自治区', '内蒙古自治区': '内蒙古自治区',
}


def norm(g):
    g = NORM.get(g, g)
    return g.replace(' ', '')


STAGES = ['I期梅毒', 'II期梅毒', 'III期梅毒', '胎传梅毒', '隐性梅毒']
f = lambda v: float(v) if v not in ('', None) else 0.0


def load(path):
    out = []
    for r in csv.DictReader(open(path, encoding='utf-8-sig')):
        r['group'] = norm(r['group'])
        out.append(r)
    return out


prov = load('raw/NNDRS_province_syphilis_2004_2020.csv')
ages = load('raw/NNDRS_age_syphilis_2004_2020.csv')

# ---------- 1. 归一化长表 ----------
with open('processed/NNDRS_province_syphilis_clean_long.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.DictWriter(fh, fieldnames=['year', 'province', 'stage', 'cases', 'deaths',
                                       'incidence_per100k', 'mortality_per100k'])
    w.writeheader()
    for r in prov:
        if r['group'] == '全国':
            continue
        w.writerow({'year': r['year'], 'province': r['group'], 'stage': r['stage'],
                    'cases': r['cases'], 'deaths': r['deaths'],
                    'incidence_per100k': r['incidence_per100k'],
                    'mortality_per100k': r['mortality_per100k']})

# ---------- 2. 省 x 年 宽表（合计发病数与发病率） ----------
g = collections.defaultdict(dict)
for r in prov:
    if r['group'] == '全国' or r['stage'] != '梅毒(合计)':
        continue
    g[r['group']][r['year']] = (r['cases'], r['incidence_per100k'])

provs = sorted(k for k in g if k != '全国')
years = [str(y) for y in range(2004, 2021)]
with open('processed/province_year_cases.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh)
    w.writerow(['province'] + years)
    for p in provs:
        w.writerow([p] + [g[p].get(y, ('', ''))[0] for y in years])
with open('processed/province_year_incidence.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh)
    w.writerow(['province'] + years)
    for p in provs:
        w.writerow([p] + [g[p].get(y, ('', ''))[1] for y in years])

# ---------- 3. 省际不平等指标 ----------
def cv(vals):
    vals = [v for v in vals if v is not None]
    if len(vals) < 2:
        return 0
    m = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))
    return sd / m * 100

def gini(vals):
    v = sorted(x for x in vals if x is not None and x >= 0)
    n = len(v)
    if n == 0 or sum(v) == 0:
        return 0
    cum = sum((i + 1) * x for i, x in enumerate(v))
    return (2 * cum) / (n * sum(v)) - (n + 1) / n

rows = []
for y in years:
    inc = [f(g[p][y][1]) for p in provs if y in g[p] and g[p][y][1] != '']
    cas = [f(g[p][y][0]) for p in provs if y in g[p] and g[p][y][0] != '']
    if not inc:
        continue
    hi = max(inc); lo = min(inc)
    rows.append({'year': y, 'n_prov': len(inc), 'mean_inc': round(sum(inc) / len(inc), 3),
                 'cv_pct': round(cv(inc), 2), 'gini': round(gini(cas), 4),
                 'max_inc': round(hi, 2), 'min_inc': round(lo, 2),
                 'max_min_ratio': round(hi / lo, 1) if lo else ''})
with open('processed/province_inequality_2004_2020.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

print('=== 省际不平等逐年 ===')
print('year  省数  均发病率  CV%    Gini   最高    最低   倍数')
for r in rows:
    print(f"{r['year']}  {r['n_prov']:>3}  {r['mean_inc']:>7.2f} {r['cv_pct']:>6.2f} {r['gini']:>6.3f} {r['max_inc']:>7.2f} {r['min_inc']:>6.2f} {r['max_min_ratio']:>7}")

# ---------- 4. 2020 分省排名 + 分型构成 ----------
print()
print('=== 2020 年分省（按发病率降序）与分型构成 ===')
det = collections.defaultdict(dict)
for r in prov:
    if r['group'] == '全国':
        continue
    det[r['group']][r['stage']] = r

rank = sorted(provs, key=lambda p: -f(det[p].get('梅毒(合计)', {}).get('incidence_per100k', '')))
print('排名 省份     发病数   发病率   隐性占比   I+II期    I+II发病率  胎传')
out = []
for i, p in enumerate(rank, 1):
    d = det[p]
    tot = f(d.get('梅毒(合计)', {}).get('cases', ''))
    inc = d.get('梅毒(合计)', {}).get('incidence_per100k', '')
    hid = f(d.get('隐性梅毒', {}).get('cases', ''))
    e12 = f(d.get('I期梅毒', {}).get('cases', '')) + f(d.get('II期梅毒', {}).get('cases', ''))
    e12i = f(d.get('I期梅毒', {}).get('incidence_per100k', '')) + f(d.get('II期梅毒', {}).get('incidence_per100k', ''))
    con = f(d.get('胎传梅毒', {}).get('cases', ''))
    hp = hid / tot * 100 if tot else 0
    out.append({'rank': i, 'province': p, 'cases_2020': tot, 'incidence_2020': inc,
                'covert_pct': round(hp, 2), 'early_cases': e12, 'early_incidence': round(e12i, 3),
                'congenital': con})
    print(f"{i:>3}  {p:<8} {tot:>8.0f} {f(inc):>7.2f}  {hp:>6.2f}% {e12:>8.0f} {e12i:>8.3f} {con:>6.0f}")

with open('processed/province_2020_rank.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
    w.writeheader(); w.writerows(out)

# ---------- 5. 年龄分布 ----------
print()
print('=== 全国分年龄组（I+II期发病率，2019 vs 2020）===')
aget = collections.defaultdict(dict)
for r in ages:
    if r['group'] in ('合计', '全 国', '全国', ''):
        continue
    aget[r['group']][(r['year'], r['stage'])] = r
ags = sorted(set(r['group'] for r in ages if re.match(r'^\d', r['group'])),
             key=lambda x: int(re.match(r'(\d+)', x).group(1)))
rows2 = []
for a in ags:
    e19 = f(aget[a].get(('2019', 'I期梅毒'), {}).get('incidence_per100k', '')) + \
          f(aget[a].get(('2019', 'II期梅毒'), {}).get('incidence_per100k', ''))
    e20 = f(aget[a].get(('2020', 'I期梅毒'), {}).get('incidence_per100k', '')) + \
          f(aget[a].get(('2020', 'II期梅毒'), {}).get('incidence_per100k', ''))
    h20 = f(aget[a].get(('2020', '隐性梅毒'), {}).get('incidence_per100k', ''))
    t20 = f(aget[a].get(('2020', '梅毒(合计)'), {}).get('incidence_per100k', ''))
    con20 = f(aget[a].get(('2020', '胎传梅毒'), {}).get('incidence_per100k', ''))
    rows2.append({'age_group': a, 'early_inc_2019': round(e19, 3), 'early_inc_2020': round(e20, 3),
                  'covert_inc_2020': round(h20, 3), 'total_inc_2020': round(t20, 3),
                  'congenital_inc_2020': round(con20, 3)})
    print(f"  {a:<10} I+II 2019={e19:>7.2f}  I+II 2020={e20:>7.2f}  隐性={h20:>8.2f}  合计={t20:>8.2f}")
with open('processed/national_age_incidence_2019_2020.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows2[0].keys()))
    w.writeheader(); w.writerows(rows2)

print()
print('输出文件:')
for r, d, fs in os.walk('processed'):
    for x in fs:
        print('  ', os.path.join(r, x))

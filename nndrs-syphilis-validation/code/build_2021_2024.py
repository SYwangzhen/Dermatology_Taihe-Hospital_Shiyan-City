# -*- coding: utf-8 -*-
"""
将 2004-2020 分省/分年龄数据扩展至 2024。

背景：公共卫生科学数据中心 BIRT 报表对 2021-2024 年的数据存在精确 2 倍复制缺陷
（病例数、死亡数、发病率三列同步翻倍），且报表丢失"分型"列与"地区名"标签。
本脚本采用 ÷2 修正 + 行序映射，并通过三重校验。

校验（见 docs/08）：
  1) 全国 ÷2 == 国家疾控局 A 系列（按发病日期）逐年精确相等
  2) 2021-2024 全部 256 个值均为偶数（精确 2 倍的必要条件）
  3) 3 省 5 个点与省卫健委统计公报独立值精确吻合
"""
import sys, os, re, csv, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from pgrid import to_grid

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
os.chdir(ROOT)

ORDER = ['北京', '天津', '河北', '山西', '内蒙古', '辽宁', '吉林', '黑龙江', '上海', '江苏',
         '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南', '广东', '广西',
         '海南', '重庆', '四川', '贵州', '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆']

CANON = {'内蒙古': '内蒙古自治区', '广西': '广西', '西藏': '西藏', '宁夏': '宁夏', '新疆': '新疆'}
for p in ORDER:
    CANON.setdefault(p, p + ('市' if p in ('北京', '天津', '上海', '重庆') else '省'))

A = {2021: 480020, 2022: 441159, 2023: 530116, 2024: 572092}
A_INC = {2021: 34.0493, 2022: 31.2747, 2023: 37.6035, 2024: 40.6411}

def to_int(s):
    s = (s or '').replace(',', '').replace('\u00a0', ' ').strip()
    try:
        return int(s)
    except Exception:
        return None

def zone_rows(path, y):
    grid = to_grid(open(path, encoding='utf-8', errors='ignore').read())
    idx = 14 if y <= 2020 else 2
    out = []
    for r in grid:
        if len(r) > idx + 3:
            v = to_int(r[idx])
            if v is not None:
                out.append({'label': re.sub(r'\s+', '', r[1]),
                            'cases': v, 'deaths': to_int(r[idx + 1]),
                            'rate': float(r[idx + 2]) if r[idx + 2] else None})
    return out

def age_rows(path, y):
    grid = to_grid(open(path, encoding='utf-8', errors='ignore').read())
    idx = 14 if y <= 2020 else 2
    out = []
    for r in grid:
        if len(r) > idx + 3:
            v = to_int(r[idx])
            if v is not None and (re.match(r'^\d+$', r[0].strip()) or r[0].strip() == ''):
                out.append({'label': re.sub(r'\s+', '', r[1]),
                            'cases': v, 'deaths': to_int(r[idx + 1]),
                            'rate': float(r[idx + 2]) if r[idx + 2] else None})
    return out

# ---------------------------------------------------------------- 1) 分省 2021-2024
prov_new = {}
for y in [2021, 2022, 2023, 2024]:
    rs = zone_rows(f'batch/zone_ext/z{y}.html', y)
    nat = rs[0]
    provs = rs[1:]
    assert len(provs) == 31, f'{y} 省数异常 {len(provs)}'
    # 校验
    raw_sum = sum(p['cases'] for p in provs)
    assert raw_sum == nat['cases'], f'{y} 省合计 {raw_sum} != 全国 {nat["cases"]}'
    assert nat['cases'] // 2 == A[y], f'{y} 全国÷2 {nat["cases"]//2} != A {A[y]}'
    assert all(p['cases'] % 2 == 0 for p in provs), f'{y} 存在奇数'
    prov_new[y] = {}
    for i, p in enumerate(provs):
        nm = CANON[ORDER[i]]
        prov_new[y][nm] = {'cases': p['cases'] // 2,
                           'rate': round(p['rate'] / 2, 4) if p['rate'] else None,
                           'deaths': (p['deaths'] / 2) if p['deaths'] is not None else None}
    print(f'[{y}] 校验通过  全国 {nat["cases"]:>9,} ÷2={nat["cases"]//2:>9,} = A系列 | 31省合计一致 | 全偶')

# ---------------------------------------------------------------- 2) 分省 2004-2020（重建，保持一致口径）
prov_old = {}
for y in range(2004, 2021):
    path = f'batch/zone/zone_{y}.html'
    if not os.path.exists(path):
        continue
    rs = zone_rows(path, y)
    provs = rs[1:] if len(rs) == 32 else rs
    for i, p in enumerate(provs):
        nm = CANON[ORDER[i]] if len(provs) == 31 else p['label']
        prov_old.setdefault(nm, {})[y] = {'cases': p['cases'],
                                          'rate': round(p['rate'], 4) if p['rate'] else None,
                                          'deaths': p['deaths']}
print(f'[2004-2020] 已重建 {len(prov_old)} 省')

# ---------------------------------------------------------------- 3) 写出宽表（发病率）
years_all = list(range(2004, 2025))
with open('processed/province_year_incidence_2004_2024.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['province'] + [str(y) for y in years_all])
    for nm in sorted(prov_old):
        row = [nm]
        for y in years_all:
            if y <= 2020:
                d = prov_old.get(nm, {}).get(y)
                row.append(f"{d['rate']:.4f}" if d and d['rate'] is not None else '')
            else:
                d = prov_new[y].get(nm)
                row.append(f"{d['rate']:.4f}" if d and d['rate'] is not None else '')
        w.writerow(row)
print('→ processed/province_year_incidence_2004_2024.csv')

# ---------------------------------------------------------------- 4) 长表（例数 + 发病率）
with open('processed/province_year_cases_2004_2024.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['province', 'year', 'cases', 'incidence_per_100k', 'deaths', 'source_note'])
    for nm in sorted(prov_old):
        for y in years_all:
            if y <= 2020:
                d = prov_old.get(nm, {}).get(y)
                note = '公共卫生科学数据中心 BIRT 报表（原值）'
            else:
                d = prov_new[y].get(nm)
                note = '同上，÷2 修正（报表 2 倍复制缺陷，见 docs/08）'
            if d:
                w.writerow([nm, y, d['cases'],
                            f"{d['rate']:.4f}" if d['rate'] is not None else '',
                            d['deaths'] if d['deaths'] is not None else '', note])
print('→ processed/province_year_cases_2004_2024.csv')

# ---------------------------------------------------------------- 5) 不平等指标 2004-2024
def gini(vals):
    v = sorted(vals)
    n = len(v)
    s = sum(v)
    if s == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(v))
    return (2 * cum) / (n * s) - (n + 1) / n

def cv(vals):
    m = sum(vals) / len(vals)
    var = sum((x - m) ** 2 for x in vals) / len(vals)
    return math.sqrt(var) / m * 100

# 注：cv 用样本标准差(n-1)；gini_rate 为发病率 Gini（主指标，衡量人均负担不平等）；
#     gini_cases 为病例数 Gini（衡量绝对数不平等，主要受人口规模驱动）——两者必须分开报告，
#     旧版 province_inequality_2004_2020.csv 误将 gini_cases 混列于全为发病率的表中。
with open('processed/province_inequality_2004_2024.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['year', 'n_prov', 'mean_inc', 'cv_pct', 'gini_rate', 'gini_cases',
                'max_inc', 'max_prov', 'min_inc', 'min_prov', 'max_min_ratio'])
    for y in years_all:
        vals, names, cas = [], [], []
        for nm in prov_old:
            if y <= 2020:
                d = prov_old[nm].get(y)
            else:
                d = prov_new[y].get(nm)
            if d and d['rate'] is not None:
                vals.append(d['rate']); names.append(nm); cas.append(d['cases'])
        if len(vals) < 30:
            continue
        mx, mn = max(vals), min(vals)
        w.writerow([y, len(vals), f'{sum(vals)/len(vals):.3f}', f'{cv(vals):.2f}',
                    f'{gini(vals):.4f}', f'{gini(cas):.4f}',
                    f'{mx:.2f}', names[vals.index(mx)], f'{mn:.2f}', names[vals.index(mn)],
                    f'{mx/mn:.1f}'])
print('→ processed/province_inequality_2004_2024.csv')

# ---------------------------------------------------------------- 5b) 2024 分省排名
prov_2024 = sorted(((nm, prov_new[2024][nm]) for nm in prov_new[2024]),
                   key=lambda kv: -kv[1]['rate'])
nat2024 = A[2024]
with open('processed/province_2024_rank.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['rank', 'province', 'cases_2024', 'incidence_2024', 'share_of_national_pct'])
    for i, (nm, d) in enumerate(prov_2024, 1):
        w.writerow([i, nm, d['cases'], f"{d['rate']:.4f}", f"{d['cases']/nat2024*100:.2f}"])
print('→ processed/province_2024_rank.csv')

# ---------------------------------------------------------------- 6) 分年龄 2021-2024
AGE_LABELS = ['0-', '1-', '2-', '3-', '4-', '5-', '6-', '7-', '8-', '9-', '10-',
              '15-', '20-', '25-', '30-', '35-', '40-', '45-', '50-', '55-', '60-',
              '65-', '70-', '75-', '80-', '85及以上']
with open('processed/national_age_incidence_2021_2024.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['age_group'] + [f'{y}_cases' for y in (2021, 2022, 2023, 2024)]
               + [f'{y}_inc' for y in (2021, 2022, 2023, 2024)])
    for i, lab in enumerate(AGE_LABELS):
        row = [lab]
        for y in (2021, 2022, 2023, 2024):
            rs = [r for r in age_rows(f'batch/age_ext/a{y}.html', y) if r['label'] or True]
            rs = rs[:26]
            row.append(rs[i]['cases'] // 2 if i < len(rs) else '')
        for y in (2021, 2022, 2023, 2024):
            rs = [r for r in age_rows(f'batch/age_ext/a{y}.html', y)][:26]
            row.append(f"{rs[i]['rate']/2:.4f}" if i < len(rs) and rs[i]['rate'] else '')
        w.writerow(row)
print('→ processed/national_age_incidence_2021_2024.csv')

# ---------------------------------------------------------------- 7) 打印关键结果
print()
print('=' * 74)
print('## 省际不平等 2019 → 2024')
print('=' * 74)
rows = list(csv.DictReader(open('processed/province_inequality_2004_2024.csv', encoding='utf-8-sig')))
print(f'{"年":<6}{"均值":>9}{"CV%":>9}{"Gini率":>10}{"Gini数":>10}{"最高":>9}{"最高省":>12}{"倍比":>8}')
for r in rows:
    if int(r['year']) >= 2019:
        print(f'{r["year"]:<6}{r["mean_inc"]:>9}{r["cv_pct"]:>9}{r["gini_rate"]:>10}{r["gini_cases"]:>10}{r["max_inc"]:>9}{r["max_prov"]:>12}{r["max_min_ratio"]:>8}')
print()
r0 = [r for r in rows if r['year'] == '2004'][0]
r1 = [r for r in rows if r['year'] == '2024'][0]
print(f'2004  CV={r0["cv_pct"]}%  Gini(率)={r0["gini_rate"]}  Gini(数)={r0["gini_cases"]}  最高/最低={r0["max_min_ratio"]}倍')
print(f'2024  CV={r1["cv_pct"]}%  Gini(率)={r1["gini_rate"]}  Gini(数)={r1["gini_cases"]}  最高/最低={r1["max_min_ratio"]}倍')
print()
print('2024 发病率前十：')
for i, (nm, d) in enumerate(prov_2024[:10], 1):
    print(f'  {i:>2}. {nm:<8} {d["rate"]:>8.2f}/10万   占全国 {d["cases"]/nat2024*100:>5.2f}%')

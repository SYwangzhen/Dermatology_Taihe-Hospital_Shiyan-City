# -*- coding: utf-8 -*-
import csv, sys, os, collections
sys.stdout.reconfigure(encoding='utf-8')

P = 'raw/NNDRS_province_syphilis_2004_2020.csv'
recs = list(csv.DictReader(open(P, encoding='utf-8-sig')))

# 地区清单
regions = sorted(set(r['group'] for r in recs))
print('地区数:', len(regions))
print(regions)
print()

f = lambda v: float(v) if v else 0.0

# 校验：31 省求和 vs 全国
print('=== 校验：省合计 vs 全国行（梅毒合计·发病数）===')
for y in range(2004, 2021):
    nat = [r for r in recs if r['year'] == str(y) and r['group'] in ('全 国', '全国') and r['stage'] == '梅毒(合计)']
    provs = [r for r in recs if r['year'] == str(y) and r['group'] not in ('全 国', '全国') and r['stage'] == '梅毒(合计)']
    if not nat:
        continue
    s = sum(f(r['cases']) for r in provs)
    n = f(nat[0]['cases'])
    d = (s - n) / n * 100 if n else 0
    print(f'  {y}  全国={n:>10.0f}  省合计={s:>10.0f}  差={d:+.2f}%  省数={len(provs)}')

print()
print('=== 分型合计校验（2020，全国）===')
for st in ['I期梅毒', 'II期梅毒', 'III期梅毒', '胎传梅毒', '隐性梅毒']:
    hit = [r for r in recs if r['year'] == '2020' and r['group'] in ('全 国', '全国') and r['stage'] == st]
    if hit:
        print(f'  {st:10s} {hit[0]["cases"]:>10s}')
sub = sum(f([r for r in recs if r['year'] == '2020' and r['group'] in ('全 国', '全国') and r['stage'] == st][0]['cases'])
          for st in ['I期梅毒', 'II期梅毒', 'III期梅毒', '胎传梅毒', '隐性梅毒'])
tot = f([r for r in recs if r['year'] == '2020' and r['group'] in ('全 国', '全国') and r['stage'] == '梅毒(合计)'][0]['cases'])
print(f'  分型相加={sub:.0f}  合计={tot:.0f}  差={sub-tot:+.0f}')

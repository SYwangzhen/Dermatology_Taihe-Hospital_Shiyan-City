# -*- coding: utf-8 -*-
"""解析 batch/ 下的 BIRT HTML 报表 -> 结构化 CSV"""
import re, os, csv, sys
sys.stdout.reconfigure(encoding='utf-8')

STAGES = ['III期梅毒', 'I期梅毒', 'II期梅毒', '梅毒(合计)', '胎传梅毒', '隐性梅毒']
MEAS = ['发病数', '死亡数', '发病率', '死亡率']


def clean(s):
    s = s.replace('&#xa0;', ' ').replace('&nbsp;', ' ')
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def rows_of(path):
    h = open(path, encoding='utf-8', errors='ignore').read()
    out = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', h, re.S | re.I):
        cells = []
        for attrs, inner in re.findall(r'<t[dh]([^>]*)>(.*?)</t[dh]>', tr, re.S | re.I):
            m = re.search(r'colspan=[\'"]?(\d+)', attrs, re.I)
            n = int(m.group(1)) if m else 1
            cells.append(clean(inner))
            cells.extend([''] * (n - 1))
        out.append(cells)
    return out


def num(s):
    if s in ('', '-', '—', '…'):
        return ''
    s = s.replace(',', '')
    try:
        float(s)
        return s
    except ValueError:
        return ''


def parse(kind, year):
    rows = rows_of(f'batch/{kind}/{kind}_{year}.html')
    # 找数据起始行：第 4 行(索引3)是表头行(含'发病数')，其后为数据
    start = None
    for i, r in enumerate(rows):
        if '发病数' in r:
            start = i + 1
            break
    if start is None:
        return []
    recs = []
    for r in rows[start:]:
        if len(r) < 25:
            continue
        label = r[0]
        grp = r[1]
        if not grp or grp.startswith('Oct ') or grp.startswith('Page'):
            continue
        if kind == 'age':
            if not re.match(r'^\d+$', label):   # age 表 col0 是序号
                continue
        vals = r[2:26]
        if len(vals) < 24:
            continue
        for si, stage in enumerate(STAGES):
            seg = vals[si * 4:si * 4 + 4]
            if len(seg) < 4:
                continue
            recs.append({
                'year': year, 'group': grp, 'stage': stage,
                'cases': num(seg[0]), 'deaths': num(seg[1]),
                'incidence_per100k': num(seg[2]), 'mortality_per100k': num(seg[3]),
            })
    return recs


def main():
    os.makedirs('raw', exist_ok=True)
    for kind, fname in [('zone', 'NNDRS_province_syphilis_2004_2020.csv'),
                        ('age', 'NNDRS_age_syphilis_2004_2020.csv')]:
        allrec = []
        for y in range(2004, 2021):
            allrec += parse(kind, y)
        with open('raw/' + fname, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=['year', 'group', 'stage', 'cases',
                                              'deaths', 'incidence_per100k', 'mortality_per100k'])
            w.writeheader()
            w.writerows(allrec)
        print(fname, '记录数 =', len(allrec))

    # 校验：全国合计 各年
    print()
    print('=== 校验：全国 / 梅毒(合计) 逐年 ===')
    recs = list(csv.DictReader(open('raw/NNDRS_province_syphilis_2004_2020.csv', encoding='utf-8-sig')))
    for y in range(2004, 2021):
        hit = [r for r in recs if r['year'] == str(y) and r['group'] in ('全 国', '全国')
               and r['stage'] == '梅毒(合计)']
        if hit:
            print(f'  {y}  发病数={hit[0]["cases"]:>8s}  发病率={hit[0]["incidence_per100k"]}')


if __name__ == '__main__':
    main()

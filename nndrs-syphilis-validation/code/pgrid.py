# -*- coding: utf-8 -*-
"""统一解析 BIRT 报表 HTML → 二维单元格列表（处理 colspan/rowspan 造成的列数不一致）"""
import re, sys

def to_grid(html):
    """把表格转为规整的行×列文本网格"""
    m = re.search(r'<table[^>]*>(.*?)</table>', html, re.S)
    if not m:
        return []
    body = m.group(1)
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', body, re.S)
    grid = []
    for r in rows:
        cells = re.findall(r'<t[dh]([^>]*)>(.*?)</t[dh]>', r, re.S)
        line = []
        for attrs, c in cells:
            v = re.sub(r'<[^>]+>', '', c)
            v = v.replace('&#xa0;', ' ').replace('&nbsp;', ' ').replace('\xa0', ' ')
            v = re.sub(r'\s+', ' ', v).strip()
            cs = re.search(r'colspan\s*=\s*[\"\']?(\d+)', attrs, re.I)
            n = int(cs.group(1)) if cs else 1
            line.append(v)
            for _ in range(n - 1):
                line.append('')
        grid.append(line)
    return grid

def text(html):
    b = re.sub(r'<script.*?</script>', '', html, flags=re.S)
    b = re.sub(r'<style.*?</style>', '', b, flags=re.S)
    b = re.sub(r'<[^>]+>', ' ', b)
    return re.sub(r'\s+', ' ', b).strip()

if __name__ == '__main__':
    for f in sys.argv[1:]:
        h = open(f, encoding='utf-8', errors='ignore').read()
        g = to_grid(h)
        print('=' * 72)
        print('###', f, '| rows=', len(g), '| bytes=', len(h))
        for i, r in enumerate(g[:12]):
            nz = [c for c in r if c]
            print(f'  [{i}] n={len(r)} | {r[:8]}')
        if len(g) <= 6:
            print('  TEXT:', text(h)[:300])

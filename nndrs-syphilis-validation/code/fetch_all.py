# -*- coding: utf-8 -*-
"""从 phsciencedata.cn 的 BIRT 报表接口批量取数：
   ReportZoneYear  -> 分地区统计表（省份 × 梅毒分型）
   ReportAgeYear   -> 分年龄组统计表（年龄组 × 性别？ × 分型）
   diseaseId=17 = 梅毒
"""
import os, re, sys, time, json, urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

BASE = 'https://www.phsciencedata.cn/Share/preview'
OUT = 'batch'
os.makedirs(os.path.join(OUT, 'zone'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'age'), exist_ok=True)

YEARS = [str(y) for y in range(2004, 2021)]

HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/122.0 Safari/537.36',
    'Referer': 'https://www.phsciencedata.cn/Share/index.jsp',
    'Accept': 'text/html,application/xhtml+xml,*/*',
}


def fetch(report, year):
    q = urllib.parse.urlencode({'__report': report, 'years': year,
                                'diseaseId': '17', '__format': 'html'})
    url = BASE + '?' + q
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode('utf-8', 'ignore')


def clean(s):
    s = s.replace('&#xa0;', ' ').replace('&nbsp;', ' ')
    s = re.sub(r'<[^>]+>', '', s)
    s = s.replace('&amp;', '&')
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def parse_table(html):
    """返回 rows: list of list[str]（每个 <tr> 的单元格按顺序）"""
    rows = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S | re.I):
        cells = [clean(td) for td in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S | re.I)]
        # 展开 colspan
        spans = [int(m) if m else 1
                 for m in re.findall(r'<t[dh][^>]*colspan=[\'"]?(\d+)', tr, re.I)]
        if any(sp > 1 for sp in spans):
            expanded = []
            spans_full = re.findall(r'<t[dh]([^>]*)>(.*?)</t[dh]>', tr, re.S | re.I)
            for attrs, inner in spans_full:
                m = re.search(r'colspan=[\'"]?(\d+)', attrs, re.I)
                n = int(m.group(1)) if m else 1
                c = clean(inner)
                expanded.append(c)
                expanded.extend([''] * (n - 1))
            cells = expanded
        rows.append(cells)
    return rows


def main():
    log = []
    for kind, report in [('zone', 'ReportZoneYear.rptdesign'),
                         ('age', 'ReportAgeYear.rptdesign')]:
        for y in YEARS:
            path = os.path.join(OUT, kind, f'{kind}_{y}.html')
            if os.path.exists(path) and os.path.getsize(path) > 20000:
                log.append((kind, y, 'cached', os.path.getsize(path)))
                continue
            try:
                html = fetch(report, y)
                open(path, 'w', encoding='utf-8').write(html)
                log.append((kind, y, 'ok', len(html)))
            except Exception as e:
                log.append((kind, y, 'ERR ' + str(e)[:60], 0))
            time.sleep(0.8)

    for k, y, st, n in log:
        print(f'{k:5s} {y} {st:12s} {n}')


if __name__ == '__main__':
    main()

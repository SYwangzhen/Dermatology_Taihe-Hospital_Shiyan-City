# -*- coding: utf-8 -*-
"""
抓取 2021-2024 年分省 / 分年龄登记报表（公共卫生科学数据中心 BIRT 接口）。

无需登录：BIRT 报表引擎的 /Share/preview 端点对注册前的会话亦可返回数据。
年份下拉（getQuerystart）只到 2020，故 2021-2024 必须直接构造 URL 获取。

用法： python scripts/fetch_2021_2024.py
输出： batch/zone_ext/  batch/age_ext/  batch/month_ext/
"""
import os, sys, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
os.chdir(ROOT)

HOST = 'https://www.phsciencedata.cn/Share/preview'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')

for d in ['batch/zone_ext', 'batch/age_ext', 'batch/month_ext']:
    os.makedirs(d, exist_ok=True)

COOKIE = 'batch/.cookies.txt'

def get(url, out):
    cmd = ['curl', '-sS', '-L', '--max-time', '40', '-A', UA,
           '-b', COOKIE, '-c', COOKIE, url, '-o', out,
           '-w', '%{http_code} %{size_download}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()

# 先访问首页建立会话（避免 ;jsessionid 注入导致的“非法路径”）
get('https://www.phsciencedata.cn/Share/index.jsp', '/dev/null')

jobs = []
for y in range(2020, 2026):
    jobs.append((f'{HOST}?__report=ReportZoneYear.rptdesign&years={y}&diseaseId=17&__format=html',
                 f'batch/zone_ext/z{y}.html'))
    jobs.append((f'{HOST}?__report=ReportAgeYear.rptdesign&years={y}&diseaseId=17&__format=html',
                 f'batch/age_ext/a{y}.html'))
for y, months in [(2020, range(1, 13)), (2021, range(1, 13)), (2023, [12]), (2024, [8, 12])]:
    for m in months:
        jobs.append((f'{HOST}?__report=ReportZoneMonth.rptdesign&years={y}&diseaseId=17&months={m}&__format=html',
                     f'batch/month_ext/M{y}_{m}.html'))

for url, out in jobs:
    st = get(url, out)
    sz = os.path.getsize(out) if os.path.exists(out) else 0
    print(f'  {os.path.basename(out):<16} {st:>10}  -> {sz:>8,} B')
print('\n完成。原始报表已归档，勿删（复核与复现均依赖）。')

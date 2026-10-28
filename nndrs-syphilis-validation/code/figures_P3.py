# -*- coding: utf-8 -*-
"""
主文出图脚本 B（English labels, Lancet style, 中线小数点）
  Fig 4  Structural discordance: sex and age
         (A GBD 性别别率 | B 性别比背离 | C 年龄别率 2020 | D 年龄别比值)
         —— 合并原 Fig 4 + 原 Fig 5
  Fig 5  Between-province inequality and its resolution
         (A Gini | B CV | C 极差 | D 总率×早期率散点 | E 排名变化)
         —— 合并原 Fig 8 + 原 Fig 8b
输出：figures/Fig{4,5}.png|pdf（PNG 300 dpi）
"""
import os, sys, re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullFormatter
from matplotlib.lines import Line2D
import matplotlib.gridspec as gridspec

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, 'processed')
RAW = os.path.join(BASE, 'raw')
TAB = os.path.join(BASE, 'tables')
FIG = os.path.join(BASE, 'figures')
# GBD 2023 Results Tool extract (not redistributed; see README, 'Reproduction').
GBDRAWA = os.environ.get('GBD_AGE_SEX_CSV',
                         os.path.join(BASE, 'raw', 'B_age_sex_1990_2023.csv'))
os.makedirs(FIG, exist_ok=True)

# ── 小数点样式：默认标准句点（EID/AMA 等要求 ASCII 句点）；
#    设环境变量 FIG_MIDDOT=1 可切回 Lancet 风格的中点 ·（U+00B7）
MIDDOT = os.environ.get('FIG_MIDDOT') == '1'


def D(s):
    """Render the decimal separator for the target journal."""
    s = str(s)
    return re.sub(r'(?<=\d)\.(?=\d)', '\u00b7', s) if MIDDOT else s


def dotfmt(fmt='g'):
    def f(v, _):
        return D(f'{v:{fmt}}')
    return FuncFormatter(f)


plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'font.size': 7,
    'axes.labelsize': 7.5,
    'axes.titlesize': 8,
    'xtick.labelsize': 6.8,
    'ytick.labelsize': 6.8,
    'legend.fontsize': 6.5,
    'axes.linewidth': 0.7,
    'xtick.major.width': 0.7,
    'ytick.major.width': 0.7,
    'xtick.major.size': 2.6,
    'ytick.major.size': 2.6,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.03,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'legend.frameon': False,
})

C = {
    'gbd':  '#B2182B', 'A': '#2166AC', 'B1': '#1B7837', 'B2': '#762A83',
    'grey': '#7F7F7F', 'dark': '#111111', 'band': '#EFEFEF',
    'stall': '#FDE7E7', 'zone': '#E8E8E8',
}

def panel_title(ax, letter, text, pad=5):
    ax.set_title(f'{letter}  {text}', loc='left', fontweight='bold', pad=pad)

def save(fig, name):
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(FIG, f'{name}.{ext}'))
    print(f'  -> figures/{name}.png / .pdf')

# ══════════════════════════════════════════════════════════════
# 载入数据
# ══════════════════════════════════════════════════════════════
gbd = pd.read_csv(os.path.join(PROC, 'gbd_incidence_series.csv'), encoding='utf-8-sig')
age20 = pd.read_csv(os.path.join(PROC, 'national_age_incidence_2019_2020.csv'), encoding='utf-8-sig')
ineq = pd.read_csv(os.path.join(PROC, 'province_inequality_2004_2024.csv'), encoding='utf-8-sig')
t7 = pd.read_csv(os.path.join(TAB, 'Table7.csv'), encoding='utf-8-sig')

if os.path.exists(GBDRAWA):
    _g = pd.read_csv(GBDRAWA)
    _ch = _g[_g.location_name == 'China']
    _grate = _ch[(_ch.measure_name == 'Incidence') & (_ch.metric_name == 'Rate')
                 & (_ch.year == 2020) & (_ch.sex_name == 'Both')][['age_name', 'val']]
else:
    # fall back to the released dataset S3 (same GBD 2023 values, China only)
    _s3 = pd.read_csv(os.path.join(BASE, 'data', 'S3_gbd_china_age_sex_1990_2023.csv'),
                      encoding='utf-8-sig')
    _s3 = _s3[(_s3.year == 2020) & (_s3.sex_name == 'Both')]
    _grate = _s3[['age_name', 'rate_per_100k']].rename(columns={'rate_per_100k': 'val'})
GBD_AGE_ORDER = ['<5 years', '5-9 years', '10-14 years', '15-19 years', '20-24 years',
                 '25-29 years', '30-34 years', '35-39 years', '40-44 years', '45-49 years',
                 '50-54 years', '55-59 years', '60-64 years', '65-69 years', '70-74 years',
                 '75-79 years', '80-84 years', '85-89 years']
ALAB = ['<5', '5–9', '10–14', '15–19', '20–24', '25–29', '30–34', '35–39', '40–44',
        '45–49', '50–54', '55–59', '60–64', '65–69', '70–74', '75–79', '80–84', '85+']
gmap = {r.age_name: r.val for r in _grate.itertuples()}
GBD_AGE = np.array([gmap.get(a, 0.0) for a in GBD_AGE_ORDER], dtype=float)
for extra in ('90-94 years', '95+ years'):
    GBD_AGE[-1] += gmap.get(extra, 0.0)

_ar = dict(zip(age20.age_group, age20.total_inc_2020))
NNDRS_AGE = np.array([
    np.mean([_ar[k] for k in ['0-', '1-', '2-', '3-', '4-']]),
    np.mean([_ar[k] for k in ['5-', '6-', '7-', '8-', '9-']]),
] + [_ar[k] for k in ['10-', '15-', '20-', '25-', '30-', '35-', '40-', '45-', '50-',
                      '55-', '60-', '65-', '70-', '75-', '80-', '85及以上']], dtype=float)

# ══════════════════════════════════════════════════════════════
# Fig 4  结构背离：性别 + 年龄  ← 原 Fig 4 + 原 Fig 5
# ══════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(7.09, 6.9))
gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.62, wspace=0.34)

# ---- A: GBD sex-specific ASIR ----
ax = fig.add_subplot(gs[0, 0])
ax.fill_between(gbd.year, gbd.gbd_asir_female, gbd.gbd_asir_male, color='#F4D9DD', zorder=1)
ax.plot(gbd.year, gbd.gbd_asir_male, '-', color=C['gbd'], lw=1.3, label='GBD male ASIR')
ax.plot(gbd.year, gbd.gbd_asir_female, '-', color='#4393C3', lw=1.3, label='GBD female ASIR')
ax.set_xlim(1989.5, 2023.9)
ax.set_ylim(0, 265)
ax.set_xticks(range(1990, 2024, 5))
ax.set_xlabel('Year')
ax.set_ylabel('Age-standardised rate\nper 100,000')
panel_title(ax, 'A', 'GBD modelled burden by sex')
ax.legend(loc='lower left', labelspacing=0.3, bbox_to_anchor=(0.01, 0.02))
ax.annotate(D('217.9'), (2023, 217.87), xytext=(-3, 4), textcoords='offset points', fontsize=6.3,
            color=C['gbd'], ha='right')
ax.annotate(D('63.3'), (2023, 63.26), xytext=(-3, -10), textcoords='offset points', fontsize=6.3,
            color='#4393C3', ha='right')
ax.text(2006, 150, D('male excess ≈ 3.4–4.8×\nthroughout 1990–2023'), fontsize=6.3,
        color='#8A2B3C', ha='center', va='center')

# ---- B: sex ratio comparison ----
ax = fig.add_subplot(gs[0, 1])
mr = gbd.gbd_asir_male / gbd.gbd_asir_female
ax.plot(gbd.year, mr, '-', color=C['gbd'], lw=1.3, label='GBD male:female ASIR ratio')
ax.axhspan(0.86, 0.96, color='#D9E8F0', zorder=0)
ax.plot([2014, 2019], [0.91, 0.91], '-', color=C['B1'], lw=1.4)
ax.plot([2011], [1.00], 'o', color=C['B2'], ms=4.2, mfc='white', mew=1.0)
ax.plot([2024], [1.04], 'o', color=C['B2'], ms=4.2, mfc='white', mew=1.0)
ax.plot([2025], [1.10], 'o', color=C['B2'], ms=4.2, mfc='white', mew=1.0)
ax.axhline(1.0, color='#AAAAAA', lw=0.7, ls='--', zorder=1)
ax.set_xlim(2009.2, 2026.4)
ax.set_ylim(0, 5.4)
ax.set_yticks([0, 1, 2, 3, 4, 5])
ax.set_xticks([2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024])
ax.set_xlabel('Year')
ax.set_ylabel('Male ÷ female ratio')
panel_title(ax, 'B', 'Divergence in sex structure')
ax.annotate(D('3.44 : 1'), (2023, 3.444), xytext=(3, 9), textcoords='offset points',
            fontsize=6.3, color=C['gbd'])
ax.annotate(D('0.86–0.96 : 1\n(2014–2019)'), (2016.5, 0.91), xytext=(-2, -20),
            textcoords='offset points', fontsize=6.2, color=C['B1'], ha='center')
ax.annotate(D('1.10 : 1\n(2025)'), (2025, 1.10), xytext=(-2, -21), textcoords='offset points',
            fontsize=6.2, color=C['B2'], ha='center')
ax.annotate('', xy=(2023.4, 3.44), xytext=(2023.4, 1.04),
            arrowprops=dict(arrowstyle='<->', lw=0.7, color='#444444'))
ax.text(2022.2, 2.20, D('3.6×'), fontsize=6.6, color='#333333', ha='center')
h = [Line2D([], [], color=C['gbd'], lw=1.3), Line2D([], [], color=C['B1'], lw=1.4),
     Line2D([], [], color=C['B2'], marker='o', ls='none', mfc='white', mew=1.0, ms=4.2)]
ax.legend(h, ['GBD (model)', 'NNDRS reported, 2014–2019', 'NNDRS reported, single years'],
          loc='center left', bbox_to_anchor=(0.01, 0.52), labelspacing=0.35)

# ---- C: age-specific rate, two systems ----
x = np.arange(len(ALAB))
ax = fig.add_subplot(gs[1, 0])
ax.axvspan(12.5, 17.5, color=C['zone'], zorder=0)
ax.bar(x, NNDRS_AGE, 0.66, color='#C7D9E8', edgecolor=C['A'], linewidth=0.5,
       label='NNDRS notified rate')
ax.plot(x, GBD_AGE, '-o', color=C['gbd'], lw=1.4, ms=2.8, mfc='white', mew=0.9, zorder=3,
        label='GBD modelled incidence')
ax.set_xlim(-0.7, 17.7)
ax.set_ylim(0, 400)
ax.set_xticks(x)
ax.set_xticklabels(ALAB, rotation=90, fontsize=6.0)
ax.set_xlabel('Age group (years)')
ax.set_ylabel('Rate per 100,000')
panel_title(ax, 'C', 'Age-specific rate, 2020')
ax.legend(loc='upper right', bbox_to_anchor=(1.02, 1.02), labelspacing=0.3)
ax.annotate(D('352.4'), (5, 352.4), xytext=(0, 6), textcoords='offset points', fontsize=6.2,
            color=C['gbd'], ha='center')
ax.annotate(D('44.4'), (4, 44.4), xytext=(3, 3), textcoords='offset points', fontsize=6.2,
            color=C['A'], ha='left')
ax.annotate(D('90.4'), (17, 90.4), xytext=(-2, 5), textcoords='offset points', fontsize=6.2,
            color=C['A'], ha='right')
ax.text(14.2, 240, D('GBD assigns zero\nincidence at\n65 years and above'), fontsize=6.1,
        color=C['gbd'], ha='center', va='center', style='italic', linespacing=1.4)
ax.text(15.6, 120, D('NNDRS peak:\n85+ y'), fontsize=6.1, color=C['A'], ha='center',
        linespacing=1.4)

# ---- D: ratio by age ----
ax = fig.add_subplot(gs[1, 1])
ratio = np.divide(GBD_AGE, NNDRS_AGE, out=np.zeros_like(GBD_AGE), where=NNDRS_AGE > 0)
keep = np.arange(len(ALAB))[:13]
ax.axvspan(12.5, 17.5, color=C['zone'], zorder=0)
ax.axhline(1.0, color='#AAAAAA', lw=0.7, ls='--', zorder=1)
ax.plot(keep, ratio[keep], '-o', color=C['dark'], lw=1.3, ms=2.8, mfc='white', mew=0.9,
        zorder=3, label='GBD ÷ NNDRS')
zx = np.arange(13, 18)
ax.plot(zx, np.full(len(zx), 0.30), 'v', color=C['gbd'], ms=3.4, mfc='white', mew=0.9, zorder=3)
ax.set_yscale('log')
ax.set_ylim(0.26, 80)
ax.set_yticks([0.3, 1, 3, 10, 30])
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: D(f'{v:g}×')))
ax.yaxis.set_minor_formatter(NullFormatter())
ax.set_xlim(-0.7, 17.7)
ax.set_xticks(x)
ax.set_xticklabels(ALAB, rotation=90, fontsize=6.0)
ax.set_xlabel('Age group (years)')
ax.set_ylabel('Ratio (GBD ÷ NNDRS)')
panel_title(ax, 'D', 'Model-to-notification ratio by age')
ax.legend(loc='upper right', bbox_to_anchor=(0.99, 0.99), labelspacing=0.3)
ax.annotate(D('model overestimates\nyoung adults 2–10×'), xy=(5.0, 9.84), xytext=(7.6, 26),
            fontsize=6.1, color='#333333', ha='center',
            arrowprops=dict(arrowstyle='-', lw=0.6, color='#888888'))
ax.annotate(D('underestimates from\n60 y upward (0 at 65+)'), xy=(13.0, 0.62), xytext=(2.6, 0.36),
            fontsize=6.1, color=C['gbd'], ha='left', va='bottom',
            arrowprops=dict(arrowstyle='-', lw=0.6, color=C['gbd']))
save(fig, 'Fig4')
plt.close(fig)

# ══════════════════════════════════════════════════════════════
# Fig 5  省际不平等与其分辨率  ← 原 Fig 8 + 原 Fig 8b
# ══════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(7.09, 6.3))
gs = gridspec.GridSpec(2, 6, figure=fig, hspace=0.60, wspace=0.85)

x = ineq.year.values
stall_from = 2020

def shade(ax):
    ax.axvspan(stall_from - 0.5, 2024.5, color=C['stall'], zorder=0)
    ax.axvline(2019, color='#999999', lw=0.6, ls=':', zorder=1)

# ---- A: Gini ----
ax = fig.add_subplot(gs[0, 0:2])
ax.plot(x, ineq.gini_rate, '-o', color=C['gbd'], lw=1.2, ms=2.4, mfc='white', mew=0.7,
        label='Gini of incidence rate')
ax.plot(x, ineq.gini_cases, '-s', color='#4393C3', lw=1.2, ms=2.4, mfc='white', mew=0.7,
        label='Gini of case counts')
shade(ax)
ax.set_xlim(2003.4, 2024.6); ax.set_ylim(0.20, 0.60)
ax.set_xticks(range(2004, 2025, 5))
ax.set_yticks([0.2, 0.3, 0.4, 0.5, 0.6])
ax.yaxis.set_major_formatter(dotfmt('g'))
ax.set_xlabel('Year'); ax.set_ylabel('Gini coefficient')
panel_title(ax, 'A', 'Gini coefficient')
ax.legend(loc='lower left', handlelength=1.4, bbox_to_anchor=(-0.02, -0.02))
ax.annotate(D('0.537'), xy=(2004, 0.5366), xytext=(2006.0, 0.572), textcoords='data',
            fontsize=6.3, ha='center', va='center',
            arrowprops=dict(arrowstyle='-', lw=0.5, color='#888888', shrinkA=1, shrinkB=2))
ax.annotate(D('0.246 \u2192 0.266'), (2023.7, 0.2657), xytext=(2016.4, 0.310), textcoords='data',
            fontsize=6.3, ha='left', va='center',
            arrowprops=dict(arrowstyle='-', lw=0.5, color='#888888', shrinkA=2, shrinkB=2))

# ---- B: CV ----
ax = fig.add_subplot(gs[0, 2:4])
ax.plot(x, ineq.cv_pct, '-o', color='#D95F02', lw=1.2, ms=2.4, mfc='white', mew=0.7)
shade(ax)
ax.set_xlim(2003.4, 2024.6); ax.set_ylim(30, 140)
ax.set_xticks(range(2004, 2025, 5))
ax.set_xlabel('Year'); ax.set_ylabel('CV (%)')
panel_title(ax, 'B', 'Coefficient of variation')
ax.annotate(D('126.4%'), (2004, 126.4), xytext=(4, 3), textcoords='offset points', fontsize=6.3)
ax.annotate(D('43.7%'), (2019, 43.66), xytext=(2, -10), textcoords='offset points', fontsize=6.3)
ax.annotate(D('47.6%'), (2024, 47.60), xytext=(-15, 6), textcoords='offset points', fontsize=6.3, ha='center')
ax.text(2021.9, 100, D('no further\nconvergence'), fontsize=6.1, color='#B2182B', ha='center',
        style='italic')

# ---- C: max/min ratio ----
ax = fig.add_subplot(gs[0, 4:6])
ax.plot(x, ineq.max_min_ratio, '-o', color='#4D4D4D', lw=1.2, ms=2.4, mfc='white', mew=0.7)
shade(ax)
ax.set_yscale('log')
ax.set_xlim(2003.4, 2024.6); ax.set_ylim(4, 400)
ax.set_yticks([5, 10, 20, 50, 100, 200, 300])
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: D(f'{v:g}×')))
ax.yaxis.set_minor_formatter(NullFormatter())
ax.set_xticks(range(2004, 2025, 5))
ax.set_xlabel('Year'); ax.set_ylabel('Highest ÷ lowest')
panel_title(ax, 'C', 'Between-province ratio')
ax.annotate(D('285×'), (2004, 285.3), xytext=(5, 1), textcoords='offset points', fontsize=6.3)
ax.annotate(D('6.0×'), (2019, 6.0), xytext=(3, -10), textcoords='offset points', fontsize=6.3)
ax.annotate(D('7.1×'), (2024, 7.1), xytext=(-16, 6), textcoords='offset points', fontsize=6.3)

# ---- D: scatter 2024 total rate vs 2020 early rate ----
ax = fig.add_subplot(gs[1, 0:3])
t = t7.copy()
dx = t.incidence_2024_per_100k.values
dy = t.early_incidence_2020_per_100k.values
col = t.change_in_cases_2020_to_2024_pct.values
sz = np.sqrt(t.cases_2024.values) / 3.6
sc = ax.scatter(dx, dy, c=col, s=sz, cmap='RdBu_r', vmin=-30, vmax=80,
                edgecolor='#555555', linewidth=0.4, zorder=3)
ax.axvline(dx.mean(), color='#AAAAAA', lw=0.6, ls=':', zorder=1)
ax.axhline(dy.mean(), color='#AAAAAA', lw=0.6, ls=':', zorder=1)
lab = {'Qinghai': (-5, -1, 'right'), 'Tibet': (0, 6, 'center'), 'Yunnan': (-5, -1, 'right'),
       'Hainan': (5, -1, 'left'), 'Xinjiang': (-5, -2, 'right'), 'Guizhou': (5, -1, 'left'),
       'Shanghai': (-5, 0, 'right'), 'Liaoning': (-5, -1, 'right'),
       'Jiangsu': (-5, 0, 'right'), 'Zhejiang': (-5, 0, 'right'), 'Guangdong': (-5, -6, 'right'),
       'Hebei': (5, -7, 'left')}
for r_ in t.itertuples():
    if r_.province in lab:
        ddx, ddy, ha = lab[r_.province]
        ax.annotate(r_.province, (r_.incidence_2024_per_100k, r_.early_incidence_2020_per_100k),
                    xytext=(ddx, ddy), textcoords='offset points', fontsize=5.9,
                    color='#222222', ha=ha)
ax.set_xlim(6, 108)
ax.set_ylim(-0.7, 17.4)
ax.xaxis.set_major_formatter(dotfmt('g'))
ax.yaxis.set_major_formatter(dotfmt('g'))
ax.set_xlabel('2024 notified incidence rate (per 100,000)')
ax.set_ylabel('2020 primary + secondary rate\n(per 100,000)')
panel_title(ax, 'D', 'Total (2024) versus early syphilis (2020)')
cb = fig.colorbar(sc, ax=ax, fraction=0.040, pad=0.020)
cb.ax.yaxis.set_ticks_position('right')
cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: D('%d%%' % v)))
cb.ax.tick_params(labelsize=6.0, pad=1.5)
ax.text(11, 15.6, D('high total, high early:\ntransmission-driven'), fontsize=6.0,
        color='#333333', ha='left', va='center', linespacing=1.35)
ax.text(84, 0.4, D('high total, low early:\ndetection-driven'), fontsize=6.0,
        color='#333333', ha='center', va='center', linespacing=1.35)

# ---- E: rank-shift slope chart ----
ax = fig.add_subplot(gs[1, 3:6])
rk = t7.sort_values('rank_by_total_incidence_2020')
movers = {'Qinghai', 'Jilin', 'Yunnan', 'Hunan', 'Liaoning'}
for r_ in rk.itertuples():
    hot = r_.province in movers
    ax.plot([0, 1], [r_.rank_by_total_incidence_2020, r_.rank_by_early_incidence_2020],
            '-', color=C['gbd'] if hot else '#CCCCCC', lw=1.0 if hot else 0.6,
            alpha=0.95 if hot else 0.75, zorder=3 if hot else 2)
    if hot:
        ax.plot([0, 1], [r_.rank_by_total_incidence_2020, r_.rank_by_early_incidence_2020],
                'o', color=C['gbd'], ms=2.6, zorder=4)
        _name = r_.province.replace('Inner Mongolia', 'Inner\nMongolia')
        _lo = (-5, -2)
        ax.annotate(_name, (0, r_.rank_by_total_incidence_2020), xytext=_lo,
                    textcoords='offset points', fontsize=5.9, ha='right', va='center',
                    color='#222222', linespacing=1.25)
        # 右端标签：25–31 段三条线相邻（Hunan 25 / Qinghai 27 / Yunnan 31），逐个微调纵向偏移
        _ro = {'Hunan': (5, 10), 'Yunnan': (5, 0), 'Qinghai': (5, 0)}.get(r_.province, (5, -2))
        ax.annotate(_name, (1, r_.rank_by_early_incidence_2020), xytext=_ro,
                    textcoords='offset points', fontsize=5.9, ha='left', va='center',
                    color='#222222', linespacing=1.25)
ax.set_xlim(-0.62, 1.62)
ax.set_ylim(32.3, 0.1)
ax.set_xticks([0, 1])
ax.set_xticklabels(['2020 total incidence\n(31 provinces)', '2020 primary + secondary\n(31 provinces)'],
                   fontsize=6.3)
ax.set_ylabel('')
ax.set_yticks([1, 5, 10, 15, 20, 25, 30])
panel_title(ax, 'E', 'Rank shift between the two indicators', pad=14)
ax.text(0.0, 1.008, 'red: shift ≥15 places (n=5); nine provinces ≥12',
        transform=ax.transAxes, fontsize=5.0, color='#8c1d1d', ha='left', va='bottom')
save(fig, 'Fig5')
plt.close(fig)

# ── 清理已合并的旧图，避免残留 ────────────────────────────────
for stale in ('Fig6', 'Fig7', 'Fig8', 'Fig8b'):
    for ext in ('png', 'pdf'):
        p = os.path.join(FIG, f'{stale}.{ext}')
        if os.path.exists(p):
            os.remove(p)
            print('  rm  figures/%s.%s' % (stale, ext))

print('\n完成。figures/ 目录：')
for f in sorted(os.listdir(FIG)):
    print('  ', f)

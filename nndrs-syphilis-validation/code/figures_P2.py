# -*- coding: utf-8 -*-
"""
主文出图脚本 A（English labels, Lancet style, 中线小数点）
  Fig 1  Level discordance: three sources overall and for congenital syphilis
         (A 年度计数对数轴 | B 率 | C GBD 先天负担 | D 两官方系列胎传病例)
         —— 合并原 Fig 1 + 原 Fig 6
  Fig 2  Divergence in level, in reporting basis, and its attribution
         (A 比值轨迹与断点 | B 三条官方系列偏移 | C 分型渠道差 | D 报告质量归因)
         —— 合并原 Fig 2 + 原 Fig 7
  Fig 3  Stage composition and the collapse of early syphilis, 2012-2025
输出：figures/Fig{1,2,3}.png|pdf（PNG 300 dpi）
"""
import os, sys, re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullFormatter
import matplotlib.gridspec as gridspec
from scipy import stats

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE, 'processed')
RAW = os.path.join(BASE, 'raw')
FIG = os.path.join(BASE, 'figures')
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


# ── 全局样式 ──────────────────────────────────────────────────
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
    'gbd':   '#B2182B',   # GBD model
    'A':     '#2166AC',   # NNDRS series A (onset date)
    'B1':    '#1B7837',   # series B1 (final-review date)
    'B2':    '#762A83',   # series B2 (report date)
    'pri':   '#D6604D',   # primary
    'sec':   '#F4A582',   # secondary
    'ter':   '#9970AB',   # tertiary
    'con':   '#4393C3',   # congenital
    'lat':   '#BFBFBF',   # latent
    'gini_r': '#B2182B',
    'gini_c': '#4393C3',
    'stall': '#FDE7E7',
    'grey': '#7F7F7F',
    'dark': '#111111',
    'band': '#EFEFEF',
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
rat = pd.read_csv(os.path.join(PROC, 'p2_ratio_series.csv'), encoding='utf-8-sig')
gbd = pd.read_csv(os.path.join(PROC, 'gbd_incidence_series.csv'), encoding='utf-8-sig')
ann = pd.read_csv(os.path.join(RAW, 'NNDRS_syphilis_annual.csv'), encoding='utf-8-sig')
st = pd.read_csv(os.path.join(RAW, 'NNDRS_syphilis_stage.csv'), encoding='utf-8-sig')
st.columns = [c.strip().lstrip('\ufeff') for c in st.columns]
stb1 = st[st['口径'].str.contains('B1')].copy().sort_values('年份')
stb2 = st[st['口径'].str.contains('B2')].copy().sort_values('年份')
pop = pd.read_csv(os.path.join(PROC, 'china_population_derived.csv'), encoding='utf-8-sig').set_index('year')['population']

a_rate = ann[ann['系列'].str.startswith('A')][['年份', '报告发病率(每10万)']].dropna()
a_rate = a_rate.groupby('年份', as_index=False).first().sort_values('年份')

Q = pd.DataFrame({'year': [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021],
                  'under': [1.29, 1.08, 1.02, 0.67, 2.04, 0.50, 0.51, 0.50, 0.33],
                  'acc':   [93.87, 92.23, 95.24, 96.04, 95.77, 97.63, 98.25, 98.97, 98.73]})

# ══════════════════════════════════════════════════════════════
# Fig 1  水平对照（总体 + 先天）  ← 原 Fig 1 + 原 Fig 6
# ══════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(7.09, 6.9))
gs = gridspec.GridSpec(2, 2, figure=fig, height_ratios=[1.0, 0.92], hspace=0.52, wspace=0.40)

# ---- A: counts, log axis ----
ax = fig.add_subplot(gs[0, 0])
ax.axvspan(1988.6, 2003.5, color=C['band'], zorder=0)
ax.plot(rat.year, rat.gbd_cases, '-', color=C['gbd'], lw=1.3, label='GBD modelled incident infections')
a = rat.dropna(subset=['nndrs_a'])
ax.plot(a.year, a.nndrs_a, '-o', color=C['A'], lw=1.2, ms=2.4, mfc='white', mew=0.7,
        label='NNDRS series A (onset date)')
b1 = rat.dropna(subset=['nndrs_b1'])
ax.plot(b1.year, b1.nndrs_b1, '-s', color=C['B1'], lw=1.1, ms=2.2, mfc='white', mew=0.7,
        label='NNDRS series B1 (final-review)')
b2 = rat.dropna(subset=['nndrs_b2'])
ax.plot(b2.year, b2.nndrs_b2, 'D', color=C['B2'], ms=2.8, mfc='white', mew=0.8,
        label='NNDRS series B2 (report date)')
ax.set_yscale('log')
ax.set_ylim(3e4, 1.3e7)
ax.set_yticks([5e4, 1e5, 2e5, 5e5, 1e6, 2e6])
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v/1e6:g}M' if v >= 1e6 else f'{v/1e3:g}k'))
ax.yaxis.set_minor_formatter(NullFormatter())
ax.set_xlim(1988.6, 2025.8)
ax.set_xticks(range(1990, 2026, 5))
ax.set_xlabel('Year')
ax.set_ylabel('Cases per year (log scale)')
panel_title(ax, 'A', 'Annual incidence and notifications')
ax.legend(loc='upper left', bbox_to_anchor=(-0.01, 1.03), labelspacing=0.12,
          prop={'size': 6.1})
ax.annotate('1,957,724', (2023, 1957724), xytext=(-2, -8), textcoords='offset points',
            fontsize=6.3, color=C['gbd'], ha='right', va='top')
ax.annotate('530,116', (2023, 530116), xytext=(-2, -11), textcoords='offset points',
            fontsize=6.3, color=C['A'], ha='right')
ax.text(1989.3, 1.15e5, 'pre-2004 reporting platform\n(aggregate totals only)', fontsize=5.7,
        color='#555555', ha='left', va='center', style='italic', linespacing=1.35)

# ---- B: rates ----
ax = fig.add_subplot(gs[0, 1])
ax.plot(gbd.year, gbd.gbd_asir_both, '-', color=C['gbd'], lw=1.3,
        label='GBD age-standardised rate (model)')
ax.plot(a_rate['年份'], a_rate['报告发病率(每10万)'], '-o', color=C['A'], lw=1.2, ms=2.4,
        mfc='white', mew=0.7, label='NNDRS notified rate (crude)')
ax.set_xlim(1988.6, 2026.4)
ax.set_ylim(0, 218)
ax.set_xticks(range(1990, 2026, 5))
ax.set_xlabel('Year')
ax.set_ylabel('Rate per 100,000')
panel_title(ax, 'B', 'Rate: model versus notification')
ax.legend(loc='upper left', bbox_to_anchor=(-0.01, 1.02), labelspacing=0.3)
ax.annotate(D('144.2'), (2023, 144.2), xytext=(-5, -12), textcoords='offset points',
            fontsize=6.3, color=C['gbd'], ha='right')
ax.annotate(D('37.6'), (2023, 37.6), xytext=(-5, -11), textcoords='offset points',
            fontsize=6.3, color=C['A'], ha='right')
ax.annotate('', xy=(2023.7, 144.2), xytext=(2023.7, 37.6),
            arrowprops=dict(arrowstyle='<->', lw=0.7, color='#444444'))
ax.text(2023.9, 88, D('3.8×'), fontsize=6.4, color='#333333', rotation=90, va='center')
ax.text(1992.2, 122, 'flat', fontsize=6.3, color=C['gbd'], style='italic', ha='left')
ax.text(2013.0, 70, D('5.3× rise'), fontsize=6.3, color=C['A'], style='italic', ha='left')

# ---- C: GBD congenital burden ----
ax = fig.add_subplot(gs[1, 0])
ax.plot(gbd.year, gbd.gbd_u5_deaths_both, '-', color=C['gbd'], lw=1.5,
        label='Deaths <5 y (left)')
ax.set_xlim(1989.5, 2025.0)
ax.set_ylim(0, 3600)
ax.set_xticks([1990, 2000, 2010, 2020])
ax.set_xlabel('Year')
ax.set_ylabel('GBD deaths, <5 y')
panel_title(ax, 'C', 'GBD congenital burden')
ax2 = ax.twinx()
ax2.fill_between(gbd.year, 0, gbd.gbd_u5_daly_both / 1000, color='#E0D2EA', zorder=0,
                 label='DALYs <5 y (right)')
ax2.set_ylim(0, 320)
ax2.set_ylabel('DALYs (10³)')
ax2.spines['right'].set_visible(True)
ax2.spines['right'].set_linewidth(0.7)
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc='upper right', bbox_to_anchor=(1.04, 1.02), labelspacing=0.3)
ax.text(1990.4, 3390, '3,210', fontsize=6.2, color=C['gbd'], ha='left')
ax.annotate('831', (2023, 831), xytext=(6, -1), textcoords='offset points', fontsize=6.2,
            color=C['gbd'], ha='left', va='center')
ax.text(2001, 1500, D('−74.1% (1990–2023)'), fontsize=6.2, color='#333333', ha='center')

# ---- D: notified congenital cases, two official series + implied ratio ----
ax = fig.add_subplot(gs[1, 1])
yy = stb1['年份'].values
cong = stb1['胎传'].values.astype(float)
ax.bar(yy, cong, 0.66, color='#C7D9E8', edgecolor=C['A'], linewidth=0.5,
       label='Series B1 (final-review date)')
s2 = stb2[stb2['年份'] >= 2023]
ax.plot(s2['年份'], s2['胎传'].values, 'D', color=C['B2'], ms=3.6, mfc='white', mew=0.9,
        label='Series B2 (report date)')
ax.set_xlim(2011.3, 2026.6)
ax.set_ylim(0, 14600)
ax.set_xticks([2012, 2015, 2018, 2021, 2024])
ax.set_xlabel('Year')
ax.set_ylabel('Notified cases')
panel_title(ax, 'D', 'Notified congenital syphilis, two series')
ax.legend(loc='upper right', bbox_to_anchor=(1.04, 1.02), labelspacing=0.3)
ax.annotate('11,175', (2012, 11175), xytext=(2, 4), textcoords='offset points', fontsize=6.2,
            color=C['A'])
ax.annotate('844', (2024, 844), xytext=(9, 1), textcoords='offset points', fontsize=6.2,
            color=C['B2'], ha='left', va='center')
ax.annotate('', xy=(2023.7, 844), xytext=(2023.7, 523),
            arrowprops=dict(arrowstyle='<->', lw=0.7, color=C['B2']))
ax.annotate(D('+61%'), xy=(2023.72, 790), xytext=(2022.5, 2900), fontsize=6.2, color=C['B2'],
            ha='center', va='center',
            arrowprops=dict(arrowstyle='-', lw=0.6, color=C['B2'], shrinkA=2, shrinkB=1))
ax.text(2013.4, 10200, D('B1: −96.7% (2012 → 2025)'), fontsize=6.2, color='#333333', ha='left')
ax.text(2015.3, 7250, D('GBD <5-y deaths per notified case, 2024:\n1.59 (B1) vs 0.99 (B2)'),
        fontsize=6.0, color='#333333', ha='left', va='center', linespacing=1.45)
save(fig, 'Fig1')
plt.close(fig)

# ══════════════════════════════════════════════════════════════
# Fig 2  背离、口径与归因  ← 原 Fig 2 + 原 Fig 7
# ══════════════════════════════════════════════════════════════
import matplotlib.gridspec as gridspec

fig = plt.figure(figsize=(7.09, 5.5))
gs = gridspec.GridSpec(2, 3, figure=fig, height_ratios=[1.0, 1.0], hspace=0.52, wspace=0.55)

# ---- A: cross-system ratio ----
axA = fig.add_subplot(gs[0, :])
d = rat[(rat.year >= 2004) & (rat.year <= 2023) & (rat.gbd_over_A != '')]
x = d.year.astype(float).values
y = d.gbd_over_A.astype(float).values
axA.plot(x, y, '-', color=C['gbd'], lw=1.3, marker='o', ms=3.0, mfc='white',
         mew=0.9, zorder=3, label='GBD incident infections ÷ notified cases')
for (a_, b_, col) in [(2004, 2009, '#7F7F7F'), (2010, 2018, '#7F7F7F'), (2019, 2023, '#111111')]:
    m = (x >= a_) & (x <= b_)
    k = np.polyfit(x[m], np.log10(y[m]), 1)
    xs = np.linspace(a_, b_, 60)
    axA.plot(xs, 10 ** np.polyval(k, xs), '--', color=col, lw=0.9, zorder=2)
for bp in (2010, 2019):
    axA.axvline(bp - 0.5, color='#999999', lw=0.6, ls=':', zorder=1)
axA.set_yscale('log')
axA.set_ylim(3.0, 45)
axA.set_yticks([3, 5, 10, 20, 40])
axA.yaxis.set_major_formatter(FuncFormatter(lambda v, _: D(f'{v:g}×')))
axA.yaxis.set_minor_formatter(NullFormatter())
axA.set_xlim(2003.2, 2023.9)
axA.set_xticks(range(2004, 2024, 2))
axA.set_xlabel('Year')
axA.set_ylabel('Ratio (GBD ÷ NNDRS-A)')
panel_title(axA, 'A', 'Cross-system divergence: model-to-notification ratio')
axA.annotate(D('26.4×'), (2004, y[0]), textcoords='offset points', xytext=(-1, 7),
             fontsize=6.5, color=C['gbd'])
axA.text(2022.6, 3.05, D('3.7×'), fontsize=6.5, color=C['gbd'], ha='right')
axA.text(2008.6, 21.5, D('APC −21.8%\n(2004–2009)'), fontsize=6.2, color='#4D4D4D',
         ha='center', va='center')
axA.text(2014.0, 4.35, D('APC −6.3%\n(2010–2018)'), fontsize=6.2, color='#4D4D4D',
         ha='center', va='center')
axA.text(2021.7, 8.2, D('APC 0.0%\n(2019–2023)'), fontsize=6.2, color='#111111',
         ha='center', va='center')
axA.legend(loc='upper right', handlelength=1.6)
axA.text(0.985, 0.63, 'gap stalled after 2018', transform=axA.transAxes, ha='right',
         fontsize=6.2, color='#111111', style='italic')

# ---- B: within-system ratios ----
axB = fig.add_subplot(gs[1, 0])
full = pd.DataFrame({'year': range(2004, 2026)})
b1a = full.merge(rat[rat.b1_over_A_pct != ''][['year', 'b1_over_A_pct']], on='year', how='left')
b2b1 = full.merge(rat[rat.b2_over_b1_pct != ''][['year', 'b2_over_b1_pct']], on='year', how='left')
axB.plot(b1a.year, b1a.b1_over_A_pct, '-s', color=C['B1'], lw=1.1, ms=2.6, mfc='white', mew=0.8,
         label='Series B1 vs A')
axB.plot(b2b1.year, b2b1.b2_over_b1_pct, '-D', color=C['B2'], lw=1.1, ms=2.6, mfc='white', mew=0.8,
         label='Series B2 vs B1')
axB.axhline(0, color='#CCCCCC', lw=0.6, zorder=1)
axB.set_xlim(2003.2, 2025.8)
axB.set_ylim(-2, 22)
axB.set_xticks(range(2004, 2026, 4))
axB.set_xlabel('Year')
axB.set_ylabel('Difference between series (%)')
panel_title(axB, 'B', 'Parallel official series')
axB.legend(loc='upper left', bbox_to_anchor=(0.01, 1.02), ncol=1, labelspacing=0.3)
axB.annotate(D('B2 vs B1 ≈ +12.8%\n(2023–2025)'), xy=(2023, 11.74), xytext=(2017.5, 15.0),
             fontsize=6.0, color=C['B2'], ha='center',
             arrowprops=dict(arrowstyle='-', lw=0.6, color=C['B2']))

# ---- C: stage-specific channel deviation ----
axC = fig.add_subplot(gs[1, 1])
dev = pd.read_csv(os.path.join(PROC, 'stage_channel_deviation.csv'), encoding='utf-8-sig')
order = ['一期', '二期', '三期', '胎传', '隐性']
lab = ['Prim', 'Sec', 'Tert', 'Cong', 'Latent']
dev = dev[dev.stage.isin(order)]
w = 0.26
for i, yv in enumerate((2023, 2024, 2025)):
    vals = [dev[(dev.stage == s) & (dev.year == yv)].B2_vs_B1_pct.values[0] for s in order]
    axC.bar(np.arange(len(order)) + (i - 1) * w, vals, w, color=['#9970AB', '#762A83', '#4A1A56'][i],
            edgecolor='white', linewidth=0.4, label=str(yv))
axC.set_xticks(np.arange(len(order)))
axC.set_xticklabels(lab, fontsize=6.0)
axC.set_ylim(0, 84)
axC.set_yticks([0, 20, 40, 60, 80])
axC.set_ylabel('B2 vs B1 (%)')
panel_title(axC, 'C', 'Channel gap is stage-specific')
axC.legend(loc='upper left', ncol=3, columnspacing=0.8, handlelength=1.0,
           bbox_to_anchor=(0.0, 1.02), labelspacing=0.25)
axC.annotate(D('+55–61%'), xy=(3, 61.4), xytext=(1.45, 71), fontsize=6.2, color='#4A1A56',
             ha='center', arrowprops=dict(arrowstyle='-', lw=0.6, color='#4A1A56'))
axC.text(-0.45, 12, 'small for\nsecondary', fontsize=5.8, color='#333333', ha='left', va='bottom')

# ---- D: attribution (reporting quality) ----
axD = fig.add_subplot(gs[1, 2])
qq = Q.merge(rat[rat.gbd_over_A != ''][['year', 'gbd_over_A']], on='year')
lv = np.log10(qq.gbd_over_A.astype(float).values)
r, p = stats.pearsonr(qq.under.values, lv)
k = np.polyfit(qq.under.values, lv, 1)
xs = np.linspace(0.2, 2.2, 50)
axD.plot(xs, 10 ** np.polyval(k, xs), '--', color='#888888', lw=0.9, zorder=1)
axD.plot(qq.under, qq.gbd_over_A.astype(float), 'o', color=C['gbd'], ms=4.0, mfc='white',
         mew=1.0, zorder=3)
axD.annotate('2013', (1.29, float(qq[qq.year == 2013].gbd_over_A.iloc[0])),
             xytext=(4, 2), textcoords='offset points', fontsize=6.0, color='#555555', ha='left')
axD.annotate('2017', (2.04, float(qq[qq.year == 2017].gbd_over_A.iloc[0])),
             xytext=(-4, -4), textcoords='offset points', fontsize=6.0, color='#555555', ha='right')
axD.set_yscale('log')
axD.set_ylim(2.5, 22)
axD.set_yticks([3, 5, 10, 20])
axD.yaxis.set_major_formatter(FuncFormatter(lambda v, _: D(f'{v:g}×')))
axD.yaxis.set_minor_formatter(NullFormatter())
axD.set_xlim(0.15, 2.45)
axD.set_xticks([0.5, 1.0, 1.5, 2.0])
axD.xaxis.set_major_formatter(dotfmt('g'))
axD.set_xlabel('Under-reporting rate (%)')
axD.set_ylabel('GBD ÷ NNDRS-A ratio')
panel_title(axD, 'D', 'Attribution: reporting quality')
axD.text(0.52, 15.6, D(f'r = {r:.2f}, p = {p:.2f}\n(n = 9, 2013–2021)'),
         fontsize=6.1, color='#333333', linespacing=1.4)
axD.text(0.42, 11.5, D('under-reporting always\n<2.1%; gap stays 3.7×'),
         fontsize=5.9, color='#333333', va='top', ha='left', linespacing=1.4)
save(fig, 'Fig2')
plt.close(fig)

# ══════════════════════════════════════════════════════════════
# Fig 3  分型构成与早期梅毒塌陷
# ══════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(7.09, 3.4))
fig.subplots_adjust(wspace=0.46)

# ---- A: stacked stage composition ----
axA, axA2 = axes[0], axes[0].twinx()
yy = stb1['年份'].values
comp = [('隐性', 'Latent', C['lat']), ('一期', 'Primary', C['pri']),
        ('二期', 'Secondary', C['sec']), ('三期', 'Tertiary', C['ter']),
        ('胎传', 'Congenital', C['con'])]
bottom = np.zeros(len(yy))
for col, lbl, c in comp:
    v = stb1[col].values.astype(float) / 1000
    axA.bar(yy, v, 0.68, bottom=bottom, color=c,
            edgecolor='white', linewidth=0.3, label=lbl)
    bottom += v
axA.set_xlim(2011.3, 2025.7)
axA.set_ylim(0, 660)
axA.set_xticks(range(2012, 2026, 2))
axA.set_xlabel('Year')
axA.set_ylabel('Notified cases (thousands)')
axA.set_yticks([0, 100, 200, 300, 400, 500, 600])
panel_title(axA, 'A', 'Stage composition of notifications')
_ord = ['Latent', 'Secondary', 'Congenital', 'Primary', 'Tertiary']
_h = {lbl: hh for hh, lbl in zip(*axA.get_legend_handles_labels())}
axA.legend([_h[k] for k in _ord], _ord, loc='upper left', ncol=2, columnspacing=0.7,
           handlelength=1.0, handletextpad=0.4, labelspacing=0.25,
           bbox_to_anchor=(-0.015, 1.03))
axA2.plot(yy, stb1['隐性占比(%)'].values, '-o', color='#111111', lw=1.0, ms=2.4,
          mfc='white', mew=0.7)
axA2.set_ylim(50, 97)
axA2.set_yticks([50, 60, 70, 80, 90])
axA2.set_ylabel('Latent proportion (%)')
axA2.spines['right'].set_visible(True)
axA2.spines['right'].set_linewidth(0.7)
axA2.annotate(D('54.6%'), (2012, 54.57), xytext=(5, -7), textcoords='offset points', fontsize=6.3)
axA2.annotate(D('91.9%'), (2025, 91.87), xytext=(-18, 5), textcoords='offset points', fontsize=6.3)

# ---- B: early syphilis collapse ----
axB, axB2 = axes[1], axes[1].twinx()
early = stb1['一期+二期'].values.astype(float)
rate = early / pop.loc[yy].values * 1e5
axB.bar(yy, early / 1000, 0.68, color='#C7D9E8', edgecolor=C['A'], linewidth=0.5,
        label='Notified cases (left)')
axB.set_xlim(2011.3, 2025.7)
axB.set_ylim(0, 215)
axB.set_xticks(range(2012, 2026, 2))
axB.set_xlabel('Year')
axB.set_ylabel('Primary + secondary cases (thousands)')
axB.set_yticks([0, 50, 100, 150, 200])
panel_title(axB, 'B', 'Collapse of early (infectious) syphilis')
axB2.plot(yy, rate, '-o', color=C['gbd'], lw=1.2, ms=2.6, mfc='white', mew=0.8,
          label='Rate (right)')
axB2.set_ylim(0, 17)
axB2.set_yticks([0, 4, 8, 12, 16])
axB2.set_ylabel('Rate per 100,000')
axB2.spines['right'].set_visible(True)
axB2.spines['right'].set_linewidth(0.7)
h1, l1 = axB.get_legend_handles_labels(); h2, l2 = axB2.get_legend_handles_labels()
axB.legend(h1 + h2, l1 + l2, loc='upper right', handlelength=1.2,
           bbox_to_anchor=(1.02, 1.04))
axB.text(2021.0, 147, D('Primary + secondary:\n176,291 (2012) → 42,669 (2025)\n−75.8%;  '
                        'APC −10.0% (2012–2025)'),
         fontsize=6.4, color='#333333', ha='center', va='center', linespacing=1.45)
save(fig, 'Fig3')
plt.close(fig)

print('\n完成。figures/ 目录：')
for f in sorted(os.listdir(FIG)):
    print('  ', f)

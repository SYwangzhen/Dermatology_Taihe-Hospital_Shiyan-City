# -*- coding: utf-8 -*-
"""GBD 套路增补图（2026-10-28 大修）

Fig 6  What drives the rise, and where it is slowing
   A  Das Gupta decomposition of the change in notified cases, 2012-2023
   B  Provincial EAPC before and after 2019, with 95% CI
Figure A1（附录）Province-year heat panel, 2004-2024
   —— 用热图替代分省地图，规避审图号，信息量不减
输出：figures/Fig6.png|pdf、figures/FigA1.png|pdf（PNG 300 dpi）
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB = os.path.join(BASE, 'tables')
DATA = os.path.join(BASE, 'data')
FIG = os.path.join(BASE, 'figures')
os.makedirs(FIG, exist_ok=True)

MIDDOT = os.environ.get('FIG_MIDDOT') == '1'


def D(s):
    s = str(s)
    return s.replace('.', '\u00b7') if MIDDOT else s


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

C = {'up': '#B2182B', 'down': '#2166AC', 'grey': '#7F7F7F'}


def panel_title(ax, letter, text, pad=5):
    ax.set_title('%s  %s' % (letter, text), loc='left', fontweight='bold', pad=pad)


def save(fig, name):
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(FIG, '%s.%s' % (name, ext)),
                    dpi=300 if ext == 'png' else None)
    plt.close(fig)
    print('  -> figures/%s.png / .pdf' % name)


DEC = pd.read_csv(os.path.join(TAB, 'Table9_decomposition.csv'))
PE = pd.read_csv(os.path.join(TAB, 'Table10_province_eapc.csv'))
S1 = pd.read_csv(os.path.join(DATA, 'S1_provincial_incidence_2004_2024.csv'), encoding='utf-8-sig')
YEARS = [c for c in S1.columns if c.isdigit()]

# ══════════════════════════════════════════════════════════════
# Fig 6  A 分解瀑布 + B 省级 EAPC
# ══════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(7.09, 3.95))
gs = gridspec.GridSpec(1, 2, figure=fig, width_ratios=[1.0, 1.12], wspace=0.30)

# ---- A
ax = fig.add_subplot(gs[0, 0])
row = DEC[(DEC.y0 == 2012) & (DEC.y1 == 2023)].iloc[0]
steps = [('2012', row.n0, None),
         ('Population\ngrowth', row['pop'], C['up']),
         ('Age\nstructure', row['structure'], C['up']),
         ('Reporting\nrate', row['rate'], C['up']),
         ('2023', row.n1, None)]
cur = 0.0
for i, (lab, val, col) in enumerate(steps):
    if col is None:
        ax.bar(i, val, 0.60, color='#4D4D4D', zorder=3)
        ax.text(i, val * 1.012, format(int(round(val)), ','), ha='center', va='bottom',
                fontsize=6.1, color='#222222')
        cur = val
    else:
        bottom = cur
        ax.bar(i, val, 0.60, bottom=bottom, color=col, alpha=0.88, zorder=3)
        ax.plot([i - 0.30, i + 0.72], [bottom + val, bottom + val], ls=':', lw=0.7,
                color='#666666', zorder=2)
        ax.text(i, bottom + val + row.n1 * 0.008,
                '%s\n%+.0f%%' % (format(int(round(val)), ','), 100 * val / row.dn),
                ha='center', va='bottom', fontsize=5.8, color=col, linespacing=1.2)
        cur = bottom + val
ax.set_xticks(np.arange(len(steps)))
ax.set_xticklabels([s[0] for s in steps], fontsize=6.0, linespacing=1.2)
ax.set_ylim(0, row.n1 * 1.19)
ax.set_xlim(-0.62, len(steps) - 0.38)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: '%dk' % (v / 1e3)))
ax.set_ylabel('Notified cases')
panel_title(ax, 'A', 'What drove the rise, 2012\u20132023')
ax.text(0.02, 0.97, 'total %s (%+.1f%%)' % (format(int(round(row.dn)), ','),
                                            100 * row.dn / row.n0),
        transform=ax.transAxes, fontsize=6.0, va='top', color='#333333')

# ---- B
ax = fig.add_subplot(gs[0, 1])
pe = PE.sort_values('eapc_1924').reset_index(drop=True)
ax.axvline(0, color='#999999', lw=0.7, zorder=1)
for i, r in pe.iterrows():
    ax.plot([r.lo_0419, r.hi_0419], [i + 0.17, i + 0.17], color=C['down'], lw=0.8, alpha=0.6, zorder=2)
    ax.plot([r.lo_1924, r.hi_1924], [i - 0.17, i - 0.17], color=C['up'], lw=0.8, alpha=0.6, zorder=2)
    ax.plot([r.eapc_0419, r.eapc_1924], [i + 0.17, i - 0.17], color='#C8C8C8', lw=0.5, zorder=1)
    ax.plot(r.eapc_0419, i + 0.17, 'o', ms=1.9, color=C['down'], zorder=3)
    ax.plot(r.eapc_1924, i - 0.17, 'o', ms=1.9, color=C['up'], zorder=3)
ax.set_yticks(np.arange(len(pe)))
ax.set_yticklabels(pe.province, fontsize=4.9)
ax.set_ylim(-0.9, len(pe) - 0.1)
ax.set_xlim(-16, 50)
ax.tick_params(axis='y', length=1.2, width=0.5)
ax.set_xlabel('EAPC (%), 95% CI')
panel_title(ax, 'B', 'Provincial trend before and after 2019')
ax.legend(handles=[Line2D([], [], marker='o', ls='', ms=2.8, color=C['down'], label='2004\u20132019'),
                   Line2D([], [], marker='o', ls='', ms=2.8, color=C['up'], label='2019\u20132024')],
          loc='lower right', bbox_to_anchor=(1.0, 0.0), prop={'size': 5.8}, labelspacing=0.28,
          handletextpad=0.3)

save(fig, 'Fig6')

# ══════════════════════════════════════════════════════════════
# Figure A1（附录）省-年热图
# ══════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(7.09, 4.35))
ax = fig.add_subplot(111)
order = PE.sort_values('rate_2024', ascending=False).province.tolist()
idx = [S1.index[S1.province == p][0] for p in order]
mat = S1[YEARS].apply(pd.to_numeric, errors='coerce').values[idx, :]
cmap = LinearSegmentedColormap.from_list(
    'rate', ['#F7FBFF', '#C6DBEF', '#6BAED6', '#2171B5', '#08306B'])
im = ax.imshow(mat, aspect='auto', cmap=cmap, interpolation='nearest')
ax.set_xticks(np.arange(len(YEARS)))
ax.set_xticklabels(YEARS, fontsize=5.8, rotation=90)
ax.set_yticks(np.arange(len(order)))
ax.set_yticklabels(order, fontsize=5.4)
ax.tick_params(axis='both', length=1.5, width=0.5)
for s in ('left', 'bottom', 'top', 'right'):
    ax.spines[s].set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.022, pad=0.012)
cb.set_label('Notified incidence rate per 100,000', fontsize=6.0)
cb.ax.tick_params(labelsize=5.6, length=1.5, width=0.5)
cb.outline.set_linewidth(0.4)
ax.set_title('Province\u2013year notified incidence rate, ranked by 2024 level',
             loc='left', fontweight='bold', pad=6, fontsize=8)
ax.axvline(YEARS.index('2019'), color='#111111', lw=0.7, ls=':', zorder=3)

save(fig, 'FigA1')
print('完成 Fig6（A 分解 / B 省级 EAPC）与 FigA1（省-年热图）')

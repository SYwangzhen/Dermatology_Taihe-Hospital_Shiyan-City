# -*- coding: utf-8 -*-
"""Appendix A9：把三准则框架移植到结核病（最小化演练）。

数据全部为公开汇总数，不随仓库分发大表，直接内嵌下列两段序列：

1. WHO Global Tuberculosis Report 2025（中国，2015–2024）
   估算发病数 e_inc_num 及其 95% 不确定区间，
   通报数 c_newinc（全型别，new + relapse），肺外结核 new_ep，
   细菌学确诊 new_labconf。
   来源：https://www.who.int/publications/i/item/9789240116924
   数据文件：WHO global TB database，ds=estimates / ds=notifications（iso3=CHN）。

2. 中国法定传染病通报（肺结核，按发病日期）
   2015–2019：Chen W, Zhang H, Du X, Li T, Zhao Y. China CDC Wkly. 2020;2(12):181–4.
   2023：2023 年全国法定传染病疫情概况（NDCPA）
   2024：2024 年全国法定传染病疫情概况（NDCPA）

运行：python code/tb_portability.py
"""
import math

# ---------------------------------------------------------------- 数据
YEARS = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]

# WHO 估算：发病数、下限、上限、发病率/10 万
WHO_EST = {
    2015: (905000, 737000, 1090000, 65),
    2016: (884000, 719000, 1070000, 63),
    2017: (879000, 715000, 1060000, 62),
    2018: (861000, 701000, 1040000, 61),
    2019: (827000, 673000, 997000, 58),
    2020: (834000, 678000, 1000000, 58),
    2021: (781000, 635000, 941000, 55),
    2022: (748000, 608000, 901000, 52),
    2023: (741000, 603000, 893000, 52),
    2024: (696000, 567000, 839000, 49),
}

# WHO 口径通报数：全型别 c_newinc、肺外 new_ep、细菌学确诊 new_labconf
WHO_NOTIF = {
    2013: (847176, 30767, 275915),
    2014: (819283, 32348, 235704),
    2015: (798439, 33259, 215151),
    2016: (778493, 35369, 207740),
    2017: (773150, 36525, 212914),
    2018: (795245, 42471, 249251),
    2019: (728265, 39109, 295225),
    2020: (624715, 33473, 297862),
    2021: (585340, 28192, 296854),
    2022: (501261, 28570, 268247),
    2023: (564918, 29458, 326625),
    2024: (531097, 30105, 330357),
}

# NDCPA 口径通报数：肺结核（仅肺部），按发病日期
NDCPA_PTB = {
    2015: 864015, 2016: 836236, 2017: 835193, 2018: 823342, 2019: 775764,
    2023: 613091, 2024: 569081,
}


def eapc(first, last, years):
    """年均变化百分比：100 × [(last/first)^(1/years) − 1]。"""
    return 100 * ((last / first) ** (1.0 / years) - 1)


def main():
    y0, y1 = YEARS[0], YEARS[-1]
    est, lo, hi, rate = WHO_EST[y1]
    notif_all = WHO_NOTIF[y1][0]
    ndcpa = NDCPA_PTB[y1]

    print('=== 准则 1 水平（%d）===' % y1)
    print('WHO 估算      %9s（95%% UI %s–%s），发病率 %d/10 万'
          % (format(est, ','), format(lo, ','), format(hi, ','), rate))
    print('NDCPA 肺结核  %9s' % format(ndcpa, ','))
    print('WHO 通报全型  %9s' % format(notif_all, ','))
    print('比值 R        %.2f（NDCPA 口径）/ %.2f（WHO 口径）' % (est / ndcpa, est / notif_all))
    print('R 的区间      %.2f–%.2f（按模型 95%% UI 上下界重算）' % (lo / ndcpa, hi / ndcpa))
    print('判定          通报数落在区间内，贴近下界 → 边缘，非决定性')
    print()

    print('=== 准则 2 趋势（%d–%d）===' % (y0, y1))
    e_model = eapc(WHO_EST[y0][0], WHO_EST[y1][0], y1 - y0)
    e_ndcpa = eapc(NDCPA_PTB[2015], NDCPA_PTB[2024], 9)
    e_who = eapc(WHO_NOTIF[2015][0], WHO_NOTIF[2024][0], 9)
    print('模型估算      %.1f%%/年（%s → %s）'
          % (e_model, format(WHO_EST[y0][0], ','), format(WHO_EST[y1][0], ',')))
    print('NDCPA 通报    %.1f%%/年（%s → %s）'
          % (e_ndcpa, format(NDCPA_PTB[2015], ','), format(NDCPA_PTB[2024], ',')))
    print('WHO 通报全型  %.1f%%/年（%s → %s）'
          % (e_who, format(WHO_NOTIF[2015][0], ','), format(WHO_NOTIF[2024][0], ',')))
    print('两种通报口径相差 %.1f 个百分点 → 同向、同量级，趋势准则成立'
          % abs(e_ndcpa - e_who))
    print()

    print('=== 准则 3 结构（%d）===' % y1)
    ep, lab = WHO_NOTIF[y1][1], WHO_NOTIF[y1][2]
    print('肺外结核占比  %.1f%%（%s/%s）——病例定义可解释的上限'
          % (100 * ep / notif_all, format(ep, ','), format(notif_all, ',')))
    print('细菌学确诊占比 %.1f%%（%d）→ %.1f%%（%d）——内部构成改善而非恶化'
          % (100 * WHO_NOTIF[2013][2] / WHO_NOTIF[2013][0], 2013,
             100 * lab / notif_all, y1))
    print()
    print('结论：三准则可算、可判定，且给出与梅毒不同的结论（趋势准则通过）；')
    print('      限制在于 WHO 结核估算本身以通报数据与漏检率假设标定，两流不完全独立。')


if __name__ == '__main__':
    main()

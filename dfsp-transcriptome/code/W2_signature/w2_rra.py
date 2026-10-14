"""W2 步骤2: RobustRankAggreg 秩聚合 → 核心诊断签名
基于 Kolde et al. 2012 的 order-statistic 方法（python 实现）
对两个队列的 per-gene p 值排序，计算 RRA rho 统计量 p 值，BH 校正
"""
import pandas as pd, numpy as np
from scipy.stats import beta

W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"

def bh_fdr(pvals):
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    fdr = ranked * n / np.arange(1, n + 1)
    fdr = np.minimum.accumulate(fdr[::-1])[::-1]
    fdr = np.clip(fdr, 0, 1)
    out = np.empty_like(p)
    out[order] = fdr
    return out

def rra_pvalue(ranks, n_genes, n_lists):
    """ranks: 该基因在 n_lists 个列表中的 rank（1-based）
    RRA: rho = n_lists * min_k Pr(B(k, n_lists-k+1) <= x_(k))
    """
    xs = np.sort(np.array(ranks, dtype=float) / n_genes)
    k = np.arange(1, len(xs) + 1)
    pvals = beta.cdf(xs, k, n_lists - k + 1)
    rho = n_lists * pvals.min()
    return min(rho, 1.0)

# 载入两队列 DEG
d1 = pd.read_csv(f"{W2D}/DEG_g42948_DFSP_vs_rest.csv").set_index("gene")
d2 = pd.read_csv(f"{W2D}/DEG_g2553_DFSP_vs_rest.csv").set_index("gene")

genes = list(set(d1.index) & set(d2.index))
print(f"两队列共有基因: {len(genes)}")

rows = []
for g in genes:
    p1, p2 = d1.loc[g, "p"], d2.loc[g, "p"]
    md1, md2 = d1.loc[g, "median_diff"], d2.loc[g, "median_diff"]
    if np.isnan(p1) or np.isnan(p2):
        continue
    # 在该队列中的 rank（按 p 升序）
    r1 = int(d1["p"].rank(ascending=True)[g])
    r2 = int(d2["p"].rank(ascending=True)[g])
    rho_p = rra_pvalue([r1, r2], len(genes), 2)
    rows.append({"gene": g, "rank_42948": r1, "rank_2553": r2,
                 "p_42948": p1, "p_2553": p2,
                 "md_42948": md1, "md_2553": md2,
                 "rra_p": rho_p, "direction": "up" if (md1 > 0 and md2 > 0) else ("down" if (md1 < 0 and md2 < 0) else "conflict")})

rra = pd.DataFrame(rows)
rra["rra_fdr"] = bh_fdr(rra["rra_p"])
rra = rra.sort_values("rra_p")

sig = rra[(rra["rra_fdr"] < 0.05) & (rra["direction"] != "conflict")]
rra.to_csv(f"{W2D}/RRA_rank_aggregation.csv", index=False)
sig.to_csv(f"{W2D}/RRA_signature_genes.csv", index=False)

print(f"RRA 显著基因（FDR<0.05 且方向一致）: {len(sig)}")
print(sig["direction"].value_counts().to_string())
print("\nTop 30 签名基因（按 rra_p）:")
print(sig.head(30)[["gene", "rra_p", "rra_fdr", "md_42948", "md_2553", "direction"]].to_string(index=False))

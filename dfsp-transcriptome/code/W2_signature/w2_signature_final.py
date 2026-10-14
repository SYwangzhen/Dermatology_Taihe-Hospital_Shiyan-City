"""W2 步骤2final: 共识诊断签名（两队列同向 + 各自 p<0.05）+ 效应量排序 + RRA 辅助评分
输出：signature 基因表（含 RRA rho 辅助信息），供 ML 特征选择
"""
import pandas as pd, numpy as np
from scipy.stats import beta

W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"

d1 = pd.read_csv(f"{W2D}/DEG_g42948_DFSP_vs_rest.csv").set_index("gene")
d2 = pd.read_csv(f"{W2D}/DEG_g2553_DFSP_vs_rest.csv").set_index("gene")

def rra_pvalue(ranks, n_genes, n_lists=2):
    xs = np.sort(np.array(ranks, float) / n_genes)
    k = np.arange(1, len(xs) + 1)
    return min(float(n_lists * beta.cdf(xs, k, n_lists - k + 1).min()), 1.0)

# 候选池：双队列 p<0.05 且同向
rows = []
for g in d1.index:
    if g not in d2.index:
        continue
    p1, p2 = d1.loc[g, "p"], d2.loc[g, "p"]
    md1, md2 = d1.loc[g, "median_diff"], d2.loc[g, "median_diff"]
    if np.isnan(p1) or np.isnan(p2) or p1 >= 0.05 or p2 >= 0.05:
        continue
    if np.sign(md1) != np.sign(md2):
        continue
    rows.append({"gene": g, "direction": "up" if md1 > 0 else "down",
                 "p_42948": p1, "p_2553": p2,
                 "fdr_42948": d1.loc[g, "fdr"], "fdr_2553": d2.loc[g, "fdr"],
                 "auc_42948": d1.loc[g, "auc"], "auc_2553": d2.loc[g, "auc"],
                 "md_42948": md1, "md_2553": md2,
                 "effect_score": abs(md1) + abs(md2)})

sig = pd.DataFrame(rows).sort_values("effect_score", ascending=False)
# RRA 辅助评分（池内按 p 排序）
pool = sig["gene"].tolist()
r1 = d1.loc[pool, "p"].rank()
r2 = d2.loc[pool, "p"].rank()
sig["rra_p"] = [rra_pvalue([r1[g], r2[g]], len(pool)) for g in pool]

sig.to_csv(f"{W2D}/signature_consensus_genes.csv", index=False)
print(f"共识诊断签名: {len(sig)} 基因（up {sum(sig['direction']=='up')} / down {sum(sig['direction']=='down')}）")
print("\nTop 40（按效应量）:")
print(sig.head(40)[["gene", "direction", "md_42948", "md_2553", "auc_42948", "auc_2553", "rra_p"]].to_string(index=False))

"""W2 步骤2v2: RobustRankAggreg 秩聚合（文献标准用法）
候选池 = 两队列方向一致的基因（up/down 分开）；池内按各队列 p 值排序 → RRA rho → BH 校正
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

def rra_pvalue(ranks, n_genes, n_lists=2):
    xs = np.sort(np.array(ranks, dtype=float) / n_genes)
    k = np.arange(1, len(xs) + 1)
    pvals = beta.cdf(xs, k, n_lists - k + 1)
    return min(float(n_lists * pvals.min()), 1.0)

d1 = pd.read_csv(f"{W2D}/DEG_g42948_DFSP_vs_rest.csv").set_index("gene")
d2 = pd.read_csv(f"{W2D}/DEG_g2553_DFSP_vs_rest.csv").set_index("gene")

all_res = []
for direction, sign in [("up", 1), ("down", -1)]:
    # 候选池：两队列方向一致（同向），剔除 NaN
    cand = [g for g in d1.index if g in d2.index
            and np.sign(d1.loc[g, "median_diff"]) == sign
            and np.sign(d2.loc[g, "median_diff"]) == sign
            and not (np.isnan(d1.loc[g, "p"]) or np.isnan(d2.loc[g, "p"]))]
    if len(cand) < 5:
        print(f"{direction}: 候选池仅 {len(cand)}，跳过")
        continue
    # 池内 rank（按各自队列 p 升序）
    r1 = d1.loc[cand, "p"].rank(ascending=True).astype(int)
    r2 = d2.loc[cand, "p"].rank(ascending=True).astype(int)
    rows = []
    for g in cand:
        rows.append({
            "gene": g, "direction": direction,
            "rank1": int(r1[g]), "rank2": int(r2[g]),
            "p_42948": d1.loc[g, "p"], "p_2553": d2.loc[g, "p"],
            "md_42948": d1.loc[g, "median_diff"], "md_2553": d2.loc[g, "median_diff"],
            "rra_p": rra_pvalue([r1[g], r2[g]], len(cand)),
        })
    rdf = pd.DataFrame(rows)
    rdf["rra_fdr"] = bh_fdr(rdf["rra_p"])
    all_res.append(rdf)
    sig = rdf[rdf["rra_fdr"] < 0.05]
    print(f"{direction}: 候选池 {len(cand)}，RRA 显著(FDR<0.05) {len(sig)}")

res = pd.concat(all_res, ignore_index=True).sort_values("rra_p")
res.to_csv(f"{W2D}/RRA_signature_genes_v2.csv", index=False)
sig = res[res["rra_fdr"] < 0.05]
sig.to_csv(f"{W2D}/RRA_signature_genes.csv", index=False)
print(f"\n最终诊断签名（RRA FDR<0.05）: {len(sig)} 基因（up {sum(sig['direction']=='up')} / down {sum(sig['direction']=='down')}）")
print("\nTop 40:")
print(sig.head(40)[["gene", "rra_p", "rra_fdr", "md_42948", "md_2553", "direction"]].to_string(index=False))

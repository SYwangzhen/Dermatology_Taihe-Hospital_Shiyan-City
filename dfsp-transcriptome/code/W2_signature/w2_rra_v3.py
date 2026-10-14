"""W2 步骤2v3: RRA 标准用法——候选池 = 各队列显著基因的并集，池内聚合 + BH
"""
import pandas as pd, numpy as np
from scipy.stats import beta

W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"

def bh_fdr(pvals):
    p = np.asarray(pvals, dtype=float); n = len(p)
    order = np.argsort(p); ranked = p[order]
    fdr = np.minimum.accumulate((ranked * n / np.arange(1, n + 1))[::-1])[::-1]
    out = np.empty_like(p); out[order] = np.clip(fdr, 0, 1)
    return out

def rra_pvalue(ranks, n_genes, n_lists=2):
    xs = np.sort(np.array(ranks, float) / n_genes)
    k = np.arange(1, len(xs) + 1)
    return min(float(n_lists * beta.cdf(xs, k, n_lists - k + 1).min()), 1.0)

d1 = pd.read_csv(f"{W2D}/DEG_g42948_DFSP_vs_rest.csv").set_index("gene")
d2 = pd.read_csv(f"{W2D}/DEG_g2553_DFSP_vs_rest.csv").set_index("gene")

def sig_genes(df, thresh=0.05):
    up = set(df[(df["p"] < thresh) & (df["median_diff"] > 0)].index)
    dn = set(df[(df["p"] < thresh) & (df["median_diff"] < 0)].index)
    return up, dn

up1, dn1 = sig_genes(d1)
up2, dn2 = sig_genes(d2)

all_res = []
for direction, s1, s2 in [("up", up1, up2), ("down", dn1, dn2)]:
    pool = sorted(s1 | s2)
    pool = [g for g in pool if g in d1.index and g in d2.index]
    if len(pool) < 5:
        continue
    r1 = d1.loc[pool, "p"].rank(ascending=True)
    r2 = d2.loc[pool, "p"].rank(ascending=True)
    rows = [{
        "gene": g, "direction": direction,
        "rank1": float(r1[g]), "rank2": float(r2[g]),
        "p_42948": d1.loc[g, "p"], "p_2553": d2.loc[g, "p"],
        "md_42948": d1.loc[g, "median_diff"], "md_2553": d2.loc[g, "median_diff"],
        "rra_p": rra_pvalue([r1[g], r2[g]], len(pool)),
    } for g in pool]
    rdf = pd.DataFrame(rows)
    rdf["rra_fdr"] = bh_fdr(rdf["rra_p"])
    sig = rdf[rdf["rra_fdr"] < 0.05]
    print(f"{direction}: 候选池 {len(pool)}（q1 {len(s1)} ∪ q2 {len(s2)}），RRA 显著 {len(sig)}")
    all_res.append(rdf)

res = pd.concat(all_res, ignore_index=True).sort_values("rra_p")
res.to_csv(f"{W2D}/RRA_all_v3.csv", index=False)
sig = res[res["rra_fdr"] < 0.05]
sig.to_csv(f"{W2D}/RRA_signature_genes.csv", index=False)
print(f"\n最终诊断签名（RRA FDR<0.05）: {len(sig)} 基因")
print(sig["direction"].value_counts().to_string() if len(sig) else "")
print("\nTop 50 签名:")
print(sig.head(50)[["gene", "rra_p", "rra_fdr", "md_42948", "md_2553", "direction"]].to_string(index=False) if len(sig) else "（无）")

"""W2 步骤4: 诊断签名基因 × Ge2023 15 亚群 marker 交叉定位（细胞来源）
对 151 共识签名基因 + 8+8 ML panel 基因，统计其落在哪些单细胞亚群的 top marker 中
"""
import pandas as pd, numpy as np

W1 = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"

# 单细胞 marker：每个 cluster 的 top15（按 avg_log2FC）
top = pd.read_csv(f"{W1}/Ge2023_cluster_top15_markers.csv", index_col=0)
# 每 cluster 的显著 marker 列表（avg_log2FC>0.5）
cluster_markers = {}
for c in top.index:
    genes = [g for g in top.columns if top.loc[c, g] > 0.5]
    cluster_markers[int(c)] = genes

# 细胞类型注释（基于 Ge 2023 论文 + marker 生物学判断）
celltype = {
    0: "Malignant/DFSP-like (APOD+)", 1: "Malignant/DFSP-like", 2: "CAF/Myofibroblast",
    3: "T cells", 4: "T cells", 5: "Macrophages", 6: "Fibroblast",
    7: "Malignant/cycling", 8: "B cells", 9: "NK cells", 10: "Endothelial",
    11: "Smooth muscle", 12: "Plasma cells", 13: "CAF", 14: "Mast cells",
}
# 打印各 cluster top 推断（复核）
print("=== 各亚群 top marker 推断 ===")
for c in sorted(cluster_markers):
    ms = cluster_markers[c][:8]
    print(f"  cluster {c}: {', '.join(ms)}")

# 签名基因
sig = pd.read_csv(f"{W2D}/signature_consensus_genes.csv")
panels = pd.read_csv(f"{W2D}/ML_panel_genes.csv")

def locate(gene_set, name):
    hits = {}
    for c, ms in cluster_markers.items():
        inter = set(gene_set) & set(ms)
        if inter:
            hits[c] = inter
    print(f"\n=== {name}（{len(gene_set)} 基因）亚群定位 ===")
    for c in sorted(hits):
        print(f"  cluster {c} [{celltype.get(c, '?')}]: {len(hits[c])} 基因 -> {sorted(hits[c])[:12]}")
    return hits

h_up = sig[sig["direction"] == "up"]["gene"].tolist()
h_dn = sig[sig["direction"] == "down"]["gene"].tolist()
locate(h_up, "共识签名-上调")
locate(h_dn, "共识签名-下调")

panel_genes = panels["gene"].unique().tolist()
locate(panel_genes, "ML panel 基因")

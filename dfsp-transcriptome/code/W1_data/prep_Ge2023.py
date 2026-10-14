"""W1: 清洗 Ge2023 补充表 → 15 亚群 marker 矩阵 + 伪时间 DEG 表"""
import pandas as pd, os

S = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/data/Ge2023_scRNA_supp"
OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
os.makedirs(OUTD, exist_ok=True)

# MOESM1: 15 亚群 DEG
df = pd.read_csv(f"{S}/Ge2023_MOESM1.dat", skiprows=1, encoding="utf-8", on_bad_lines="skip")
df.columns = [c.strip().lstrip(".") if isinstance(c, str) else c for c in df.columns]
# 找到实际数据列
df = df[["p_val", "avg_log2FC", "pct.1", "pct.2", "p_val_adj", "cluster", "gene"]].copy()
df["cluster"] = pd.to_numeric(df["cluster"], errors="coerce")
df["avg_log2FC"] = pd.to_numeric(df["avg_log2FC"], errors="coerce")
df = df.dropna(subset=["cluster", "gene"])
n_clusters = int(df["cluster"].nunique())
print(f"MOESM1: {len(df)} DEG 行, {n_clusters} 个亚群, 基因数 {df['gene'].nunique()}")

# 每亚群 top15 marker
tops = df.sort_values(["cluster", "avg_log2FC"], ascending=[True, False]).groupby("cluster").head(15)
top_table = tops.pivot_table(index="cluster", columns="gene", values="avg_log2FC").fillna(0)
top_table.to_csv(f"{OUTD}/Ge2023_cluster_top15_markers.csv")
df.to_csv(f"{OUTD}/Ge2023_cluster_DEG_all.csv", index=False)

# MOESM3: 伪时间轨迹 DEG
df3 = pd.read_csv(f"{S}/Ge2023_MOESM3.dat", skiprows=1, encoding="utf-8", on_bad_lines="skip")
df3.columns = [str(c).strip() for c in df3.columns]
if "gene_short_name" in df3.columns:
    df3 = df3[["gene_short_name", "pval", "qval"]].copy()
    df3 = df3.rename(columns={"gene_short_name": "gene"})
    df3 = df3.dropna(subset=["gene"])
    df3.to_csv(f"{OUTD}/Ge2023_pseudotime_DEG.csv", index=False)
    print(f"MOESM3: {len(df3)} 个轨迹 DEG, 示例: {df3['gene'].head(10).tolist()}")

print("亚群 marker 分布:")
print(top_table.notna().sum(axis=1).to_string())

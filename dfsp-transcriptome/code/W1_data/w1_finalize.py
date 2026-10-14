"""W1 收尾：全队列符号统一、per-cohort z-score、合并交集矩阵、注释总表"""
import pandas as pd, numpy as np, os

OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"

def load_matrix(path, gene_col):
    df = pd.read_csv(path, index_col=0) if not path.endswith(".gz") else pd.read_csv(path, index_col=0, compression="gzip")
    df.index = df.index.astype(str).str.strip().str.upper()
    df = df[~df.index.duplicated(keep="first")]
    df = df[df.index != "NA"]
    return df

# 1) 载入各队列矩阵
g42948 = load_matrix(f"{OUTD}/GSE42948_matrix.csv.gz", None)
g2553 = load_matrix(f"{OUTD}/GSE2553_matrix.csv.gz", None)
tcga = load_matrix(f"{OUTD}/TCGA-SARC_matrix.csv.gz", None)

print("GSE42948:", g42948.shape, "| GSE2553:", g2553.shape, "| TCGA:", tcga.shape)

# 2) 交集基因
common = sorted(set(g42948.index) & set(g2553.index) & set(tcga.index))
print(f"三队列交集基因: {len(common)}")

# 3) per-cohort z-score（按行，即每基因）
def zscore(df):
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1).replace(0, np.nan), axis=0)

z42948 = zscore(g42948.loc[common])
z2553 = zscore(g2553.loc[common])
ztcga = zscore(tcga.loc[common])

# 4) 合并（列拼接，样本前缀加队列名）
merged = pd.concat([z42948.add_prefix("G42948_"), z2553.add_prefix("G2553_"), ztcga.add_prefix("TCGA_")], axis=1)
print("合并矩阵:", merged.shape)

# 5) 注释总表
ann_parts = []
for f in ["GSE42948_annotation.csv", "GSE2553_annotation.csv", "GSE150787_annotation.csv", "TCGA-SARC_annotation.csv"]:
    a = pd.read_csv(f"{OUTD}/{f}")
    a["disease"] = a.get("disease", a.get("group", ""))
    ann_parts.append(a)
allann = pd.concat(ann_parts, ignore_index=True)
allann["disease"] = allann["disease"].fillna("").astype(str)
# 统一 DFSP 标签
allann.loc[allann["disease"].str.contains("Dermato", case=False), "disease"] = "DFSP"
allann.to_csv(f"{OUTD}/ALL_cohorts_annotation.csv", index=False)
print("注释总表:", allann.shape)
print("队列分布:", allann["cohort"].value_counts().to_dict())
print("DFSP 样本总数:", (allann["disease"] == "DFSP").sum())

# 6) 保存合并矩阵
merged.to_csv(f"{OUTD}/MERGED_zscore_matrix.csv.gz", compression="gzip")
common_genes = pd.DataFrame({"gene": common})
common_genes.to_csv(f"{OUTD}/common_genes_3cohorts.csv", index=False)
print("W1 收尾完成。")

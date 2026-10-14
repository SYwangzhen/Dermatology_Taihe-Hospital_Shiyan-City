"""W1: 整理 GSE42948 10groups 矩阵（已符号化）→ 表达矩阵 + 样本注释表"""
import gzip, re, pandas as pd

SRC = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/data/GSE42948_10groups.fibrous.tumor.transcriptome_RPM_round.txt.gz"
OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
import os
os.makedirs(OUTD, exist_ok=True)

with gzip.open(SRC, "rt") as f:
    for _ in range(2):
        f.readline()
    df = pd.read_csv(f, sep="\t", index_col=0)

df = df.loc[:, ~df.columns.duplicated()]
df = df[~df.index.duplicated(keep="first")]

def parse_group(col):
    m = re.search(r"_([A-Z]+)$", col)
    return m.group(1) if m else "NA"

groups = [parse_group(c) for c in df.columns]
ann = pd.DataFrame({
    "sample": df.columns,
    "group": groups,
})
ann["cohort"] = "GSE42948"
ann["platform"] = "GPL10999_3SEQ"
ann["disease"] = ann["group"].map({
    "DFSP": "DFSP", "FC": "Fibrosarcoma", "DTF": "Desmoid",
    "SFT": "SFT", "EF": "EF", "IF": "IF", "PF": "PF",
    "NPAF": "NPAF", "FOTS": "FOTS", "NF": "NF",
}).fillna("Other")

df.to_csv(f"{OUTD}/GSE42948_matrix.csv.gz", compression="gzip")
ann.to_csv(f"{OUTD}/GSE42948_annotation.csv", index=False)
print("GSE42948 matrix:", df.shape)
print(ann["group"].value_counts().to_string())

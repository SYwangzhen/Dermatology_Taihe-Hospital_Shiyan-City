"""W1: 整理 GSE2553（GPL1977）→ 符号化表达矩阵 + 样本注释"""
import gzip, re, pandas as pd, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gpl_parser import load_family_platform, normalize_symbols

DATA = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/data"
ANNOT = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/gpl_annot/GPL1977_family.soft.gz"
OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
os.makedirs(OUTD, exist_ok=True)

# 1) 读 series matrix 表达表
with gzip.open(f"{DATA}/GSE2553_series_matrix.txt.gz", "rt", errors="replace") as f:
    lines = f.read().splitlines()
idx = next(i for i, l in enumerate(lines) if l.startswith("!series_matrix_table_begin"))
hdr = [x.strip('"') for x in lines[idx + 1].split("\t")]
expr = pd.DataFrame([l.split("\t") for l in lines[idx + 2:]])
expr.columns = hdr[: expr.shape[1]]
expr["ID_REF"] = expr["ID_REF"].astype(str).str.strip('"')
samples = hdr[1:]
expr[samples] = expr[samples].apply(pd.to_numeric, errors="coerce")

# 2) GPL 注释映射（family.soft.gz 平台表流式解析）
mapping = normalize_symbols(load_family_platform(ANNOT))
print(f"GPL1977 平台表: {len(mapping)} 个探针→基因映射")
expr["gene"] = expr["ID_REF"].map(mapping)
expr = expr.dropna(subset=["gene"])
expr = expr[~expr["gene"].isin(["", "NA"])]
expr = expr[["gene"] + samples].drop_duplicates("gene")

# 3) 样本分组：从 GSM 的标题提取肉瘤类型
import csv
annot_rows = list(csv.DictReader(open(f"{OUTD}/../sample_annotation_raw.csv", encoding="utf-8")))
title_map = {r["GSM"]: r["title"] for r in annot_rows if r["GSE"] == "GSE2553"}
grp = []
for s in samples:
    t = title_map.get(s, "")
    m = re.match(r"([A-Za-z\s\-]+?)(?:\s*\d*)$", t)
    grp.append(m.group(1).strip() if m else t)

ann = pd.DataFrame({"sample": samples, "group": grp, "cohort": "GSE2553", "platform": "GPL1977_cDNA"})
expr.to_csv(f"{OUTD}/GSE2553_matrix.csv.gz", compression="gzip", index=False)
ann.to_csv(f"{OUTD}/GSE2553_annotation.csv", index=False)
print("GSE2553 matrix:", expr.shape)
print(ann["group"].value_counts().to_string())

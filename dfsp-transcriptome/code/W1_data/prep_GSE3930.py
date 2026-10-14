"""W1: 整理 GSE3930（11 个 GPL，多平台合并）→ 符号化表达矩阵 + 样本注释
- 剔除 aCGH 样本（title 以 'aCGH' 开头）
- 每个 GPL 子文件：探针矩阵 → 基因符号映射
- 合并策略：同一 GSM 仅保留其所在平台表达；按基因符号 union 各平台 rbind
"""
import gzip, re, glob, os, sys, csv
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gpl_parser import load_gpl_annot, normalize_symbols

DATA = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/data"
ANNOT = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/gpl_annot"
OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
os.makedirs(OUTD, exist_ok=True)

# 样本标题表（判断 aCGH）
annot_rows = list(csv.DictReader(open(f"{OUTD}/../sample_annotation_raw.csv", encoding="utf-8")))
title_map = {}
for r in annot_rows:
    if r["GSE"].startswith("GSE3930"):
        title_map.setdefault(r["GSM"], r["title"])

def parse_matrix_file(fn, gpl):
    with gzip.open(fn, "rt", errors="replace") as f:
        lines = f.read().splitlines()
    idx = next(i for i, l in enumerate(lines) if l.startswith("!series_matrix_table_begin"))
    hdr = [x.strip('"') for x in lines[idx + 1].split("\t")]
    df = pd.DataFrame([l.split("\t") for l in lines[idx + 2:]])
    df.columns = hdr[: df.shape[1]]
    df["ID_REF"] = df["ID_REF"].astype(str).str.strip('"')
    samples = hdr[1:]
    df[samples] = df[samples].apply(pd.to_numeric, errors="coerce")
    return df, samples

# 各平台注释缓存
gpl_cache = {}
def get_map(gpl):
    if gpl not in gpl_cache:
        m = load_gpl_annot(f"{ANNOT}/{gpl}.annot.gz")
        gpl_cache[gpl] = normalize_symbols(m)
    return gpl_cache[gpl]

frames = []
used_samples = set()
for fn in sorted(glob.glob(f"{DATA}/GSE3930-*_series_matrix.txt.gz")):
    gpl = re.search(r"GPL\d+", os.path.basename(fn)).group(0)
    df, samples = parse_matrix_file(fn, gpl)
    # 剔除 aCGH 样本
    keep = [s for s in samples if "aCGH" not in title_map.get(s, "")]
    if not keep:
        print(f"{gpl}: 全部为 aCGH，跳过")
        continue
    df = df[["ID_REF"] + keep]
    mapping = get_map(gpl)
    df["gene"] = df["ID_REF"].map(mapping)
    df = df.dropna(subset=["gene"])
    df = df[~df["gene"].isin(["", "NA"])]
    df = df[["gene"] + keep].drop_duplicates("gene")
    frames.append(df)
    used_samples.update(keep)
    print(f"{gpl}: {len(keep)} 表达样本, 映射 {df['gene'].nunique()} 基因")

# 合并（rbind，union 基因）
merged = pd.concat(frames, ignore_index=True)
merged = merged.drop_duplicates("gene", keep="first")
merged = merged.set_index("gene")
# 保留顺序
samples_ordered = []
for df in frames:
    for s in df.columns[1:]:
        if s not in samples_ordered:
            samples_ordered.append(s)
merged = merged[samples_ordered]

ann = pd.DataFrame({"sample": samples_ordered})
ann["title"] = ann["sample"].map(title_map)
ann["group"] = ann["title"].apply(lambda t: re.sub(r"^aCGH:", "", str(t)).split("(")[0].strip() if t else "")
ann["cohort"] = "GSE3930"
ann["platform"] = "Stanford_cDNA"

merged.to_csv(f"{OUTD}/GSE3930_matrix.csv.gz", compression="gzip")
ann.to_csv(f"{OUTD}/GSE3930_annotation.csv", index=False)
print("GSE3930 merged matrix:", merged.shape)
print("样本:", len(samples_ordered))
for g in sorted(set(ann["group"]))[:40]:
    print("  ", g, int((ann["group"] == g).sum()))

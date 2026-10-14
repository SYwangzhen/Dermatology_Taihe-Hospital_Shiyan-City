"""提取各 series matrix 的样本级注释，构建样本注释总表（W1 步骤 1 的辅助产出）。"""
import gzip, glob, os, re, csv

DATA = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/data"
OUT = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/sample_annotation_raw.csv"

def parse_series(fn):
    """返回 series 元数据 + 样本注释 dict{GSM: {title, source, characteristics}}"""
    series = {}
    samples = {}
    with gzip.open(fn, "rt", errors="replace") as f:
        cur = None
        for line in f:
            if line.startswith("!Series_"):
                key, _, rest = line.partition(" ")
                series[key] = rest.strip()
            elif line.startswith("!Sample_"):
                parts = line.rstrip("\n").split("\t")
                key = parts[0].lstrip("!").strip()
                vals = [p.strip('"') for p in parts[1:]]
                if key in ("Sample_geo_accession", "Sample_title", "Sample_source_name", "Sample_characteristics", "Sample_platform_id"):
                    for i, v in enumerate(vals):
                        gsm = samples.setdefault(f"s{i}", {})
                        gsm[key] = v
                    # rebuild index by geo accession later
            elif line.startswith("!series_matrix_table_begin"):
                break
    # reindex by geo accession
    out = {}
    accs = [v["Sample_geo_accession"] for v in samples.values() if "Sample_geo_accession" in v]
    if accs:
        for k, v in samples.items():
            out[v["Sample_geo_accession"]] = v
    return series, out

rows = []
for fn in sorted(glob.glob(os.path.join(DATA, "*_series_matrix.txt.gz"))):
    series, samples = parse_series(fn)
    gse = os.path.basename(fn).split("_")[0]
    for gsm, info in samples.items():
        chars = " | ".join(info.get("Sample_characteristics", "") if isinstance(info.get("Sample_characteristics",""), str) else "")
        rows.append({
            "GSE": gse,
            "GSM": gsm,
            "platform": info.get("Sample_platform_id", ""),
            "title": info.get("Sample_title", ""),
            "source": info.get("Sample_source_name", ""),
            "characteristics": chars,
        })

# 去重（GSE3930 多平台子文件会重复出现同一 GSM）
seen = set()
uniq = []
for r in rows:
    key = (r["GSE"], r["GSM"])
    if key in seen:
        continue
    seen.add(key)
    uniq.append(r)

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["GSE", "GSM", "platform", "title", "source", "characteristics"])
    w.writeheader()
    w.writerows(uniq)

print(f"共 {len(uniq)} 个唯一样本（来自 {len(glob.glob(os.path.join(DATA,'*_series_matrix.txt.gz')))} 个 series matrix 文件）")
from collections import Counter
print("各队列样本数:", dict(Counter(r["GSE"] for r in uniq)))

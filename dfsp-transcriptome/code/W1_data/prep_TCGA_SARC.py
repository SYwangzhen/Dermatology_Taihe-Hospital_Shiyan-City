"""W1: 整理 TCGA-SARC：Ensembl→基因符号，合并临床/生存，按 disease_type 分组"""
import pandas as pd, gzip, os

D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/data/TCGA-SARC"
OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
os.makedirs(OUTD, exist_ok=True)

# 1) 表达矩阵
expr = pd.read_csv(f"{D}/TCGA-SARC.star_tpm.tsv.gz", sep="\t", compression="gzip")
expr = expr.rename(columns={"Ensembl_ID": "ensembl"})
expr["ensembl"] = expr["ensembl"].str.replace(r"\.\d+$", "", regex=True)

# 2) probemap 映射
pm = pd.read_csv(f"{D}/gencode.v36.annotation.gtf.gene.probemap", sep="\t")
pm["id"] = pm["id"].str.replace(r"\.\d+$", "", regex=True)
pm = pm[["id", "gene"]].drop_duplicates("id")
expr = expr.merge(pm, left_on="ensembl", right_on="id", how="left")
expr = expr.dropna(subset=["gene"])
expr = expr.drop(columns=["ensembl", "id"])
expr = expr.groupby("gene").mean(numeric_only=True)
expr = expr.loc[~expr.index.duplicated(keep="first")]
# 只保留肿瘤样本(01A/01B/06A 等)
expr = expr.loc[:, expr.columns.str.match(r"TCGA-[A-Z0-9]{2}-[A-Z0-9]{4}-\d\d[A-Z]")]

# 3) 临床
clin = pd.read_csv(f"{D}/TCGA-SARC.clinical.tsv.gz", sep="\t", compression="gzip")
clin["sample"] = clin["sample"].str.strip()
clin = clin.drop_duplicates("sample", keep="first")
clin = clin.set_index("sample")

# 4) 生存
surv = pd.read_csv(f"{D}/TCGA-SARC.survival.tsv.gz", sep="\t")
surv = surv.rename(columns={"sample": "sample", "_PATIENT": "patient"})
surv = surv.drop_duplicates("sample", keep="first")
surv = surv.set_index("sample")

# 5) 注释表
ann = pd.DataFrame({"sample": expr.columns})
ann["cohort"] = "TCGA-SARC"
ann = ann.join(clin[["disease_type", "primary_site", "gender.demographic", "age_at_index.demographic", "vital_status.demographic"]], on="sample")
ann = ann.join(surv[["OS.time", "OS"]], on="sample")
ann["platform"] = "RNAseq_STAR_TPM"

expr.to_csv(f"{OUTD}/TCGA-SARC_matrix.csv.gz", compression="gzip")
ann.to_csv(f"{OUTD}/TCGA-SARC_annotation.csv", index=False)
print("TCGA-SARC matrix:", expr.shape)
print("disease_type 构成:")
print(ann["disease_type"].value_counts(dropna=False).to_string())
print("含 DFSP?", "DFSP" in set(ann["disease_type"].astype(str)))

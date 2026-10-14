"""W3 出图: Fig5a 微环境 ssGSEA 箱线图 + Fig5b 药物重定位条形图"""
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

W3D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W3_微环境药物"

# ---------- Fig5a: 微环境（两队列合并 ssGSEA，DFSP vs Control）----------
scores = pd.concat([
    pd.read_csv(f"{W3D}/ssgsea_GSE42948_scores.csv"),
    pd.read_csv(f"{W3D}/ssgsea_GSE2553_scores.csv"),
], ignore_index=True)
celltypes = [c for c in scores.columns if c != "group"]
EN = {"DFSP肿瘤(APOD+)": "DFSP tumor (APOD+)", "DFSP肿瘤": "DFSP tumor", "CAF/肌成纤维": "CAF/myofibroblast",
      "间质成纤维": "Fibroblast", "活化CAF": "Activated CAF", "T细胞": "T cells", "CD8/T": "CD8/T cells",
      "巨噬(C1Q+)": "Macrophage (C1Q+)", "巨噬(SPP1?)": "Macrophage (SPP1+)", "髓系炎性": "Myeloid/inflammatory",
      "内皮": "Endothelial", "肥大": "Mast cells", "间质成纤维": "Fibroblast", "间质(ECM)": "Stroma/ECM",
      "平滑肌": "Smooth muscle", "增殖": "Proliferating"}
# 有差异的程序（控制展示数量）
interest = ["DFSP肿瘤(APOD+)", "DFSP肿瘤", "CAF/肌成纤维", "间质成纤维", "活化CAF",
            "T细胞", "CD8/T", "巨噬(C1Q+)", "巨噬(SPP1?)", "髓系炎性", "内皮", "肥大"]
interest = [c for c in interest if c in celltypes]

melt = scores[interest + ["group"]].melt(id_vars="group", var_name="Cell program", value_name="ssGSEA score")
melt["Cell program"] = melt["Cell program"].map(EN).fillna(melt["Cell program"])
fig, ax = plt.subplots(figsize=(13, 4.5))
sns.boxplot(data=melt, x="Cell program", y="ssGSEA score", hue="group",
            palette={"DFSP": "#E24B4A", "Control": "#B4B2A9"},
            width=0.6, fliersize=2, ax=ax)
ax.set_xticklabels(ax.get_xticklabels(), rotation=35, ha="right", fontsize=9)
ax.set_ylabel("ssGSEA score (scRNA-informed)")
ax.legend(title="", fontsize=9)
ax.set_title("DFSP vs other sarcomas/fibrous tumors: cell-program enrichment (bulk projection of scRNA signatures)")
plt.tight_layout()
fig.savefig(f"{W3D}/Fig5a_microenvironment.png", dpi=300, bbox_inches="tight")
plt.close()
print("Fig5a 已保存")

# ---------- Fig5b: 药物重定位条形图 ----------
m = pd.read_csv(f"{W3D}/ChEMBL_drugs_final.csv")
m["drug"] = m["drug_name"].str.replace(r"\s+(HYDROCHLORIDE|MESYLATE|TOSYLATE|SULFATE|DIHYDRATE|ANHYDROUS)\s*$", "", regex=True).str.strip()
agg = m.groupby("drug").agg(genes=("gene", lambda x: ",".join(sorted(set(x)))), n=("gene", "nunique")).reset_index()
agg = agg.sort_values("n", ascending=False).head(18)
agg["label"] = agg["drug"] + " (" + agg["genes"] + ")"
fig, ax = plt.subplots(figsize=(9, 5.5))
colors = ["#E24B4A" if "IMATINIB" in d or "PAZOPANIB" in d or "SUNITINIB" in d or "SORAFENIB" in d else "#5F5E5A" for d in agg["drug"]]
bars = ax.barh(agg["drug"], agg["n"], color=colors, edgecolor="black", linewidth=0.5)
ax.invert_yaxis()
ax.set_xlabel("Number of DFSP signature genes targeted")
ax.set_title("Drug repurposing: ChEMBL drugs targeting DFSP up-regulated signature genes")
for b, row in zip(bars, agg.itertuples()):
    ax.text(b.get_width() + 0.15, b.get_y() + b.get_height() / 2, row.genes, va="center", fontsize=7.5, color="#2C2C2A")
plt.tight_layout()
fig.savefig(f"{W3D}/Fig5b_drugs.png", dpi=300, bbox_inches="tight")
plt.close()
print("Fig5b 已保存")
print(agg.to_string(index=False))

"""W3 步骤2: 药物重定位——签名基因 → DGIdb 药物相互作用查询
上调/下调签名基因批量查询 DGIdb，提取可靶向药物，与伊马替尼/帕唑帕尼机制交叉
"""
import pandas as pd, requests, json, time, os

W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"
W3D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W3_微环境药物"
os.makedirs(W3D, exist_ok=True)

sig = pd.read_csv(f"{W2D}/signature_consensus_genes.csv")
up = sig[sig["direction"] == "up"]["gene"].tolist()
dn = sig[sig["direction"] == "down"]["gene"].tolist()

BASE = "https://dgidb.org/api/v2/interactions.json"
def query(genes, label):
    out = []
    for i in range(0, len(genes), 40):
        batch = genes[i:i + 40]
        params = {
            "genes": ",".join(batch),
            "interaction_sources": "DrugBank,PharmGKB,TTD,ChemblInteractions",
            "source_trust_levels": "Expert Curated",
        }
        try:
            r = requests.get(BASE, params=params, timeout=60)
            if r.status_code == 200:
                d = r.json()
                for g in d.get("matchedTerms", []):
                    gene = g.get("searchTerm", "")
                    for inter in g.get("interactions", []):
                        out.append({
                            "gene": gene, "drug": inter.get("drugName", ""),
                            "interaction_type": inter.get("interactionType", ""),
                            "source": inter.get("sources", [{}])[0].get("source_db_name", "") if inter.get("sources") else "",
                        })
            time.sleep(0.3)
        except Exception as e:
            print("  err", e)
    df = pd.DataFrame(out)
    df.to_csv(f"{W3D}/DGIdb_{label}.csv", index=False)
    print(f"{label}: {len(genes)} 基因 → {len(df)} 条药物相互作用，{df['drug'].nunique() if len(df) else 0} 种药物")
    return df

print("=== 上调签名药物 ===")
du = query(up, "up_sig")
print("=== 下调签名药物 ===")
dd = query(dn, "down_sig")

# 已知 DFSP 治疗药物交叉
known = ["imatinib", "pazopanib", "sunitinib", "sorafenib", "nilotinib", "dasatinib", "axitinib", "sorafenib"]
if len(du):
    hit = du[du["drug"].str.lower().str.contains("|".join(known), na=False)]
    print(f"\n与已知 DFSP 药物（伊马替尼/帕唑帕尼/舒尼替尼等）交叉命中: {len(hit)}")
    print(hit.to_string(index=False) if len(hit) else "  （无直接命中）")
    print("\n上调签名 Top 30 药物（按基因数）:")
    top = du.groupby("drug")["gene"].apply(lambda x: ",".join(sorted(x))).reset_index()
    top["n"] = top["gene"].str.split(",").str.len()
    print(top.sort_values("n", ascending=False).head(30).to_string(index=False))

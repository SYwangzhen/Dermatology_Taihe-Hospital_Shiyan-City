"""W3 步骤2: 药物重定位——签名上调基因 → ChEMBL 靶点 → 已知药物
对 top 50 上调签名基因批量查询，汇总药物，与伊马替尼/帕唑帕尼交叉
"""
import pandas as pd, requests, time, os

W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"
W3D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W3_微环境药物"
os.makedirs(W3D, exist_ok=True)
H = {"User-Agent": "research/0.1"}

sig = pd.read_csv(f"{W2D}/signature_consensus_genes.csv")
up = sig[sig["direction"] == "up"].sort_values("effect_score", ascending=False).head(50)["gene"].tolist()
print(f"查询 top {len(up)} 上调签名基因的药物靶点...")

rows = []
target_cache = {}
for g in up:
    try:
        # 1) 基因 → 人类靶点
        r = requests.get(f"https://www.ebi.ac.uk/chembl/api/data/target/search", 
                         params={"q": g, "format": "json"}, headers=H, timeout=30)
        if r.status_code != 200:
            continue
        tgt = None
        for t in r.json().get("targets", []):
            if t.get("organism") == "Homo sapiens" and t.get("target_type") in ("SINGLE PROTEIN", "PROTEIN COMPLEX"):
                tgt = t.get("target_chembl_id"); break
        if not tgt:
            continue
        # 2) 靶点 → 药物（molecule）
        m = requests.get("https://www.ebi.ac.uk/chembl/api/data/molecule",
                         params={"target_chembl_id": tgt, "format": "json", "limit": 25}, headers=H, timeout=30)
        drugs = []
        for mol in m.json().get("molecules", []):
            nm = mol.get("pref_name") or mol.get("molecule_chembl_id")
            if nm and "(" not in nm:
                drugs.append(nm)
        for d in drugs:
            rows.append({"gene": g, "target": tgt, "drug": d})
        time.sleep(0.25)
    except Exception as e:
        print(f"  {g} err {e}")

df = pd.DataFrame(rows)
df.to_csv(f"{W3D}/ChEMBL_drugs_up_sig.csv", index=False)
print(f"完成: {len(df)} 条基因-药物关联，{df['drug'].nunique() if len(df) else 0} 种药物")

if len(df):
    # 已知 DFSP 药物交叉
    known = ["imatinib", "pazopanib", "sunitinib", "sorafenib", "nilotinib", "dasatinib", "axitinib", "ponatinib", "avapritinib", "sorafenib", "gefitinib", "erlotinib", "crizotinib"]
    df["drug_l"] = df["drug"].str.lower()
    hit = df[df["drug_l"].str.contains("|".join(known), na=False)]
    print(f"\n与已知酪氨酸激酶抑制剂交叉命中 {len(hit)} 条:")
    print(hit[["gene", "drug", "target"]].to_string(index=False) if len(hit) else "  （无直接命中，查看 top 药物）")
    print("\nTop 20 药物（按关联基因数）:")
    top = df.groupby("drug")["gene"].apply(lambda x: ",".join(sorted(set(x)))).reset_index()
    top["n"] = top["gene"].str.split(",").str.len()
    print(top.sort_values("n", ascending=False).head(20).to_string(index=False))

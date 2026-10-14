"""W3 步骤2v2: 药物重定位——ChEMBL 查询（改用 curl 子进程，绕开沙箱网络限制）
top 40 上调签名基因 → 人类靶点 → 已知药物
"""
import pandas as pd, subprocess, json, time, os

W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"
W3D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W3_微环境药物"
os.makedirs(W3D, exist_ok=True)
TMP = r"C:/Users/WZ/AppData/Local/Temp"

def curl_json(url, params=None, timeout=40):
    full = url + "?" + "&".join(f"{k}={v}" for k, v in (params or {}).items())
    out = f"{TMP}/ch_{int(time.time()*1000)}.json"
    try:
        subprocess.run(["curl", "-s", "--max-time", str(timeout), "-o", out, full],
                       capture_output=True, timeout=timeout + 10)
        with open(out, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
    finally:
        try: os.remove(out)
        except Exception: pass

sig = pd.read_csv(f"{W2D}/signature_consensus_genes.csv")
up = sig[sig["direction"] == "up"].sort_values("effect_score", ascending=False).head(40)["gene"].tolist()
print(f"查询 top {len(up)} 上调签名基因的药物靶点...", flush=True)

rows = []
for i, g in enumerate(up):
    d = curl_json("https://www.ebi.ac.uk/chembl/api/data/target/search",
                  {"q": g, "format": "json"})
    tgt = None
    for t in d.get("targets", []):
        if t.get("organism") == "Homo sapiens" and t.get("target_type") in ("SINGLE PROTEIN", "PROTEIN COMPLEX"):
            tgt = t.get("target_chembl_id"); break
    if not tgt:
        continue
    m = curl_json("https://www.ebi.ac.uk/chembl/api/data/molecule",
                  {"target_chembl_id": tgt, "format": "json", "limit": 25})
    for mol in m.get("molecules", []):
        nm = mol.get("pref_name") or mol.get("molecule_chembl_id")
        if nm:
            rows.append({"gene": g, "target": tgt, "drug": nm})
    time.sleep(0.2)
    if (i + 1) % 10 == 0:
        print(f"  {i+1}/{len(up)} 完成", flush=True)

df = pd.DataFrame(rows)
df.to_csv(f"{W3D}/ChEMBL_drugs_up_sig.csv", index=False)
print(f"完成: {len(df)} 条基因-药物关联，{df['drug'].nunique() if len(df) else 0} 种药物", flush=True)

if len(df):
    known = ["imatinib", "pazopanib", "sunitinib", "sorafenib", "nilotinib", "dasatinib",
             "axitinib", "ponatinib", "avapritinib", "gefitinib", "erlotinib", "crizotinib", "sorafenib"]
    df["drug_l"] = df["drug"].str.lower()
    hit = df[df["drug_l"].str.contains("|".join(known), na=False)]
    print(f"\n与已知酪氨酸激酶抑制剂交叉命中 {len(hit)} 条:")
    print(hit[["gene", "drug", "target"]].to_string(index=False) if len(hit) else "  （无直接命中，查看 top 药物）")
    print("\nTop 20 药物（按关联基因数）:")
    top = df.groupby("drug")["gene"].apply(lambda x: ",".join(sorted(set(x)))).reset_index()
    top["n"] = top["gene"].str.split(",").str.len()
    print(top.sort_values("n", ascending=False).head(20).to_string(index=False))

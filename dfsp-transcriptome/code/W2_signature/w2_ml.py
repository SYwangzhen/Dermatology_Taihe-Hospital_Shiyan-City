"""W2 步骤3: LASSO + SVM-RFE minimal panel + 双向外部验证 ROC + bootstrap CI
- 特征池: 151 共识签名基因
- 训练: 队列内 per-gene z-score; LASSO(L1) 选特征 → SVM-RFE 压缩 → panel(≤10)
- 外部验证: A) GSE42948训练→GSE2553验证  B) GSE2553训练→GSE42948验证
- 输出: panel 基因表 + 各方向 AUC(内部CV/外部) + bootstrap 95%CI + ROC 数据
"""
import pandas as pd, numpy as np, os
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.feature_selection import RFE
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold

OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"
os.makedirs(W2D, exist_ok=True)

rng = np.random.default_rng(42)

def load_cohort(cohort, genes):
    mfile = {"GSE42948": "GSE42948_matrix.csv.gz", "GSE2553": "GSE2553_matrix.csv.gz"}[cohort]
    mat = pd.read_csv(f"{OUTD}/{mfile}", index_col=0, compression="gzip")
    mat.index = mat.index.astype(str).str.strip().str.upper()
    mat = mat.loc[[g for g in genes if g in mat.index]]
    ann = pd.read_csv(f"{OUTD}/ALL_cohorts_annotation.csv")
    a = ann[ann["cohort"] == cohort].set_index("sample")
    grp = a.loc[mat.columns, "disease"].eq("DFSP").astype(int).values
    X = mat.T.values.astype(float)
    return X, grp, mat.index.tolist()

def zscore_cols(X):
    mu = np.nanmean(X, axis=0)
    sd = np.nanstd(X, axis=0)
    sd[sd == 0] = 1
    return (X - mu) / sd

def bootstrap_ci(y, score, n_boot=2000):
    aucs = []
    idx = np.arange(len(y))
    for _ in range(n_boot):
        i = rng.choice(idx, len(idx), replace=True)
        if len(np.unique(y[i])) < 2:
            continue
        try:
            aucs.append(roc_auc_score(y[i], score[i]))
        except ValueError:
            pass
    if len(aucs) < 100:
        return np.nan, np.nan
    return np.percentile(aucs, 2.5), np.percentile(aucs, 97.5)

def run_pipeline(train_cohort, test_cohort, panel_size=8):
    genes = pd.read_csv(f"{W2D}/signature_consensus_genes.csv")["gene"].tolist()
    Xtr, ytr, _ = load_cohort(train_cohort, genes)
    Xte, yte, _ = load_cohort(test_cohort, genes)
    Xtr, Xte = zscore_cols(Xtr), zscore_cols(Xte)
    Xtr = np.nan_to_num(Xtr); Xte = np.nan_to_num(Xte)

    # LASSO 特征选择（L1 逻辑回归，内部 CV 选 C）
    Cs = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
    best = None
    for C in Cs:
        lr = LogisticRegression(penalty="l1", solver="liblinear", C=C,
                                class_weight="balanced", max_iter=3000)
        aucs = []
        skf = StratifiedKFold(5, shuffle=True, random_state=42)
        for tr, va in skf.split(Xtr, ytr):
            lr.fit(Xtr[tr], ytr[tr])
            if len(np.unique(ytr[va])) == 2:
                aucs.append(roc_auc_score(ytr[va], lr.predict_proba(Xtr[va])[:, 1]))
        if aucs:
            m = np.mean(aucs)
            if best is None or m > best[0]:
                best = (m, C)
    C_best = best[1] if best else 0.5
    lasso = LogisticRegression(penalty="l1", solver="liblinear", C=C_best,
                               class_weight="balanced", max_iter=3000)
    lasso.fit(Xtr, ytr)
    sel = np.where(np.abs(lasso.coef_[0]) > 1e-6)[0]
    sel_genes = [genes[i] for i in sel]
    print(f"[{train_cohort}→{test_cohort}] LASSO 选择 {len(sel_genes)} 基因 (C={C_best}, 内CV AUC={best[0]:.3f})")

    # panel 选择：LASSO 不足 3 个时，用 SVM-RFE 在全部特征池上选（保证 panel 稳健）
    if len(sel_genes) < 3:
        print("  LASSO 过稀疏，改用 SVM-RFE 全池特征选择")
        sel = np.arange(len(genes))
        sel_genes = genes

    if len(sel_genes) >= 3:
        Xtr_s = Xtr[:, sel]; Xte_s = Xte[:, sel]
        svc = SVC(kernel="linear", C=1.0, class_weight="balanced")
        n_sel = min(panel_size, len(sel_genes))
        rfe = RFE(svc, n_features_to_select=n_sel)
        rfe.fit(Xtr_s, ytr)
        keep = [i for i, k in enumerate(rfe.support_) if k]
        panel_idx = [sel[i] for i in keep]
        panel = [genes[i] for i in panel_idx]
    else:
        panel = sel_genes
        panel_idx = list(sel)

    # 方向（LASSO 系数符号；全池 RFE 时用各基因单变量 AUC 符号）
    direction = {}
    for g in panel:
        gi = genes.index(g)
        if len(sel_genes) >= 3 and g in sel_genes:
            direction[g] = "up" if lasso.coef_[0][gi] > 0 else "down"
        else:
            x = Xtr[:, gi]
            direction[g] = "up" if np.nanmedian(x[ytr == 1]) > np.nanmedian(x[ytr == 0]) else "down"

    # 重新拟合 panel 模型（Logistic，L2 小正则）
    panel_idx_full = [genes.index(g) for g in panel]
    model = LogisticRegression(penalty="l2", C=1.0, class_weight="balanced", max_iter=3000)
    model.fit(Xtr[:, panel_idx_full], ytr)

    def score(X):
        return model.decision_function(X[:, panel_idx_full])

    skf = StratifiedKFold(5, shuffle=True, random_state=42)
    cv_aucs = []
    for tr, va in skf.split(Xtr, ytr):
        m = LogisticRegression(penalty="l2", C=1.0, class_weight="balanced", max_iter=3000)
        m.fit(Xtr[tr][:, panel_idx_full], ytr[tr])
        if len(np.unique(ytr[va])) == 2:
            cv_aucs.append(roc_auc_score(ytr[va], m.decision_function(Xtr[va][:, panel_idx_full])))
    train_auc = np.mean(cv_aucs) if cv_aucs else np.nan

    ext_score = score(Xte)
    ext_auc = roc_auc_score(yte, ext_score)
    lo, hi = bootstrap_ci(yte, ext_score)
    fpr, tpr, _ = roc_curve(yte, ext_score)

    print(f"  panel {len(panel)} 基因: {panel}")
    print(f"  内部CV AUC={train_auc:.3f} | 外部验证 AUC={ext_auc:.3f} (95%CI {lo:.3f}-{hi:.3f})")
    return {
        "train_cohort": train_cohort, "test_cohort": test_cohort,
        "panel": panel, "direction": direction,
        "train_auc": train_auc, "ext_auc": ext_auc, "ci": (lo, hi),
        "fpr": fpr, "tpr": tpr, "ext_score": ext_score, "y_ext": yte,
        "C_best": C_best,
    }

results = {}
for tc, vc in [("GSE42948", "GSE2553"), ("GSE2553", "GSE42948")]:
    results[f"{tc}→{vc}"] = run_pipeline(tc, vc)

# 保存 panel 与 AUC 汇总
all_panels = []
for k, r in results.items():
    for g in r["panel"]:
        all_panels.append({"train→test": k, "gene": g, "direction": r["direction"].get(g, "")})
pd.DataFrame(all_panels).drop_duplicates().to_csv(f"{W2D}/ML_panel_genes.csv", index=False)
summary = pd.DataFrame([{
    "direction": k, "n_panel": len(r["panel"]),
    "train_auc": round(r["train_auc"], 3), "ext_auc": round(r["ext_auc"], 3),
    "ci_lo": round(r["ci"][0], 3), "ci_hi": round(r["ci"][1], 3),
} for k, r in results.items()])
summary.to_csv(f"{W2D}/ML_AUC_summary.csv", index=False)
print("\n=== AUC 汇总 ===")
print(summary.to_string(index=False))

# ROC 数据保存（供仙桃/绘图，统一长度便于拼接）
for k, r in results.items():
    n = len(r["y_ext"])
    # 将 fpr/tpr 插值到固定网格
    grid = np.linspace(0, 1, 200)
    tpr_i = np.interp(grid, r["fpr"], r["tpr"])
    pd.DataFrame({"fpr_grid": grid, "tpr": tpr_i}).to_csv(
        f"{W2D}/ROC_data_{k.replace('→', '_to_')}.csv", index=False)
    np.save(f"{W2D}/ROC_scores_{k.replace('→', '_to_')}.npy", np.vstack([r["ext_score"], r["y_ext"]]))
print("\nW2 ML panel 完成。")

"""W2v2 (P0/P1): LOO-CV + 置换检验 + 敏感/特异 + Brier score + 管家基因敏感性
- LASSO C 选择与 panel 性能用 LeaveOneOut-CV（4-5 例 DFSP 下 5 折不可靠）
- 置换检验：固定 panel，打乱外部验证标签 1,000 次 → AUC 零分布 → 经验 p
- 管家基因敏感性：剔除 ACTB/GAPDH/B2M/TUBB/HPRT1/PPIA 后重跑同流程
"""
import pandas as pd, numpy as np, os, sys
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.feature_selection import RFE
from sklearn.metrics import roc_auc_score, roc_curve, brier_score_loss
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import confusion_matrix

OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"
os.makedirs(W2D, exist_ok=True)
rng = np.random.default_rng(2026)

HK = ["ACTB", "GAPDH", "B2M", "TUBB", "HPRT1", "PPIA", "18S", "RPLP0", "UBC", "YWHAZ"]

def load_cohort(cohort, genes):
    mfile = {"GSE42948": "GSE42948_matrix.csv.gz", "GSE2553": "GSE2553_matrix.csv.gz"}[cohort]
    mat = pd.read_csv(f"{OUTD}/{mfile}", index_col=0, compression="gzip")
    mat.index = mat.index.astype(str).str.upper()
    mat = mat.loc[[g for g in genes if g in mat.index]]
    ann = pd.read_csv(f"{OUTD}/ALL_cohorts_annotation.csv")
    a = ann[ann["cohort"] == cohort].set_index("sample")
    grp = a.loc[mat.columns, "disease"].eq("DFSP").astype(int).values
    return mat.T.values.astype(float), grp, mat.index.tolist()

def zscore_cols(X):
    mu = np.nanmean(X, axis=0); sd = np.nanstd(X, axis=0); sd[sd == 0] = 1
    return (X - mu) / sd

def bootstrap_ci(y, score, n_boot=2000):
    aucs = []; idx = np.arange(len(y))
    for _ in range(n_boot):
        i = rng.choice(idx, len(idx), replace=True)
        if len(np.unique(y[i])) < 2: continue
        try: aucs.append(roc_auc_score(y[i], score[i]))
        except ValueError: pass
    if len(aucs) < 100: return np.nan, np.nan
    return np.percentile(aucs, 2.5), np.percentile(aucs, 97.5)

def best_threshold(y, score):
    fpr, tpr, thr = roc_curve(y, score)
    j = tpr - fpr
    return thr[np.argmax(j)]

def run_pipeline(train_cohort, test_cohort, genes, tag, n_perm=1000):
    Xtr, ytr, _ = load_cohort(train_cohort, genes)
    Xte, yte, _ = load_cohort(test_cohort, genes)
    Xtr, Xte = zscore_cols(Xtr), zscore_cols(Xte)
    Xtr = np.nan_to_num(Xtr); Xte = np.nan_to_num(Xte)

    # LASSO C 选择：LOO-CV（每折 1 个验证样本 → 拼接 LOO 预测概率后计算整体 AUC）
    Cs = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
    loo = LeaveOneOut()
    best = None
    for C in Cs:
        probs = np.zeros(len(ytr))
        for tr, va in loo.split(Xtr, ytr):
            lr = LogisticRegression(penalty="l1", solver="liblinear", C=C, class_weight="balanced", max_iter=3000)
            lr.fit(Xtr[tr], ytr[tr])
            probs[va] = lr.predict_proba(Xtr[va])[:, 1]
        m = roc_auc_score(ytr, probs)
        if best is None or m > best[0]: best = (m, C)
    C_best = best[1] if best else 0.5
    lasso = LogisticRegression(penalty="l1", solver="liblinear", C=C_best, class_weight="balanced", max_iter=3000)
    lasso.fit(Xtr, ytr)
    sel = np.where(np.abs(lasso.coef_[0]) > 1e-6)[0]
    sel_genes = [genes[i] for i in sel]

    if len(sel_genes) < 3:
        sel = np.arange(len(genes)); sel_genes = genes
    Xtr_s, Xte_s = Xtr[:, sel], Xte[:, sel]
    n_sel = min(8, len(sel_genes))
    rfe = RFE(SVC(kernel="linear", C=1.0, class_weight="balanced"), n_features_to_select=n_sel)
    rfe.fit(Xtr_s, ytr)
    panel = [genes[int(sel[i])] for i, k in enumerate(rfe.support_) if k]
    pidx = [genes.index(g) for g in panel]

    model = LogisticRegression(penalty="l2", C=1.0, class_weight="balanced", max_iter=3000)
    model.fit(Xtr[:, pidx], ytr)

    # LOO-CV AUC（panel 固定，拼接 LOO 预测概率）
    loo_probs = np.zeros(len(ytr))
    for tr, va in loo.split(Xtr, ytr):
        m = LogisticRegression(penalty="l2", C=1.0, class_weight="balanced", max_iter=3000)
        m.fit(Xtr[tr][:, pidx], ytr[tr])
        loo_probs[va] = m.predict_proba(Xtr[va][:, pidx])[:, 1]
    loo_auc = roc_auc_score(ytr, loo_probs)

    ext_score = model.decision_function(Xte[:, pidx])
    ext_auc = roc_auc_score(yte, ext_score)
    lo, hi = bootstrap_ci(yte, ext_score)
    thr = best_threshold(yte, ext_score)
    yhat = (ext_score >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(yte, yhat).ravel()
    sens = tp / (tp + fn) if (tp + fn) else np.nan
    spec = tn / (tn + fp) if (tn + fp) else np.nan
    brier = brier_score_loss(yte, 1 / (1 + np.exp(-ext_score)))

    # 置换检验（固定 panel，打乱外部标签）
    perm = []
    for _ in range(n_perm):
        yp = rng.permutation(yte)
        if len(np.unique(yp)) == 2:
            perm.append(roc_auc_score(yp, ext_score))
    perm = np.array(perm)
    perm_p = (np.sum(perm >= ext_auc) + 1) / (n_perm + 1)

    print(f"[{tag}] LASSO(LOO) C={C_best}, LOO-AUC={loo_auc:.3f} | panel {n_sel}基因: {panel}")
    print(f"  外部 AUC={ext_auc:.3f} (95%CI {lo:.3f}-{hi:.3f}) | 置换p={perm_p:.4f} | 敏感={sens:.2f} 特异={spec:.2f} | Brier={brier:.3f}")
    return {"tag": tag, "panel": panel, "C": C_best, "loo_auc": loo_auc, "ext_auc": ext_auc,
            "ci": (lo, hi), "perm_p": perm_p, "sens": sens, "spec": spec, "brier": brier,
            "score": ext_score, "y": yte, "thr": thr, "n_hk_removed": sum(1 for g in genes if g in HK)}

genes_all = pd.read_csv(f"{W2D}/signature_consensus_genes.csv")["gene"].tolist()
genes_nohk = [g for g in genes_all if g not in HK]
print(f"管家基因剔除: {len(genes_all)} -> {len(genes_nohk)} ({len(genes_all)-len(genes_nohk)} 个被剔除)")

summary = []
for tc, vc in [("GSE42948", "GSE2553"), ("GSE2553", "GSE42948")]:
    r1 = run_pipeline(tc, vc, genes_all, f"{tc}->{vc} [全签名]")
    r2 = run_pipeline(tc, vc, genes_nohk, f"{tc}->{vc} [剔管家基因]")
    for r in (r1, r2):
        summary.append({"direction": r["tag"], "panel": ",".join(r["panel"]), "n_panel": len(r["panel"]),
                        "loo_auc": round(r["loo_auc"], 3), "ext_auc": round(r["ext_auc"], 3),
                        "ci_lo": round(r["ci"][0], 3), "ci_hi": round(r["ci"][1], 3),
                        "perm_p": r["perm_p"], "sens": round(r["sens"], 3), "spec": round(r["spec"], 3),
                        "brier": round(r["brier"], 3), "hk_removed": r["n_hk_removed"]})
        np.save(f"{W2D}/ROC_scores_v2_{r['tag'].replace('->','_').replace(' ','_').replace('[','').replace(']','').replace('全签名','full').replace('剔管家基因','nohk')}.npy",
                np.vstack([r["score"], r["y"]]))
pd.DataFrame(summary).to_csv(f"{W2D}/ML_AUC_summary_v2.csv", index=False)
print("\n=== 汇总（v2: LOO-CV + 置换检验） ===")
print(pd.DataFrame(summary)[["direction", "n_panel", "loo_auc", "ext_auc", "ci_lo", "ci_hi", "perm_p", "sens", "spec", "brier", "hk_removed"]].to_string(index=False))
print("\nW2 v2 完成。")

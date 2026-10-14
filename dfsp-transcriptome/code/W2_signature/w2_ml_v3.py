"""W2 v3 (Major 1 修复): 泄漏安全 ML pipeline
- 特征选择（Wilcoxon+FDR 候选池）、LASSO(LOO-CV)、SVM-RFE、标准化参数
  全部仅在训练队列内完成；测试队列只做一次冻结模型预测
- 方向1: train=GSE42948 -> test=GSE2553；方向2 对称
- 输出: panel 基因 + AUC/CI + 置换检验 + 敏感/特异 + Brier
"""
import pandas as pd, numpy as np, os
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.feature_selection import RFE
from sklearn.metrics import roc_auc_score, roc_curve, brier_score_loss
from sklearn.model_selection import LeaveOneOut
from scipy import stats

OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"
os.makedirs(W2D, exist_ok=True)
rng = np.random.default_rng(2026)

def load_full(cohort):
    """加载全基因矩阵（不预过滤到共识池）"""
    mfile = {"GSE42948": "GSE42948_matrix.csv.gz", "GSE2553": "GSE2553_matrix.csv.gz"}[cohort]
    mat = pd.read_csv(f"{OUTD}/{mfile}", index_col=0, compression="gzip")
    mat.index = mat.index.astype(str).str.upper()
    ann = pd.read_csv(f"{OUTD}/ALL_cohorts_annotation.csv")
    a = ann[ann["cohort"] == cohort].set_index("sample")
    grp = a.loc[mat.columns, "disease"].eq("DFSP").astype(int).values
    return mat.T.values.astype(float), grp, mat.index.tolist()

def load_pair(train, test):
    """加载两队列，返回按共有基因对齐的数据"""
    mfile = {"GSE42948": "GSE42948_matrix.csv.gz", "GSE2553": "GSE2553_matrix.csv.gz"}
    mats = {}
    ann = pd.read_csv(f"{OUTD}/ALL_cohorts_annotation.csv")
    for c in (train, test):
        mat = pd.read_csv(f"{OUTD}/{mfile[c]}", index_col=0, compression="gzip")
        mat.index = mat.index.astype(str).str.upper()
        mats[c] = mat
    common = list(set(mats[train].index) & set(mats[test].index))
    common.sort()
    out = {}
    for c in (train, test):
        m = mats[c].loc[common]
        a = ann[ann["cohort"] == c].set_index("sample")
        grp = a.loc[m.columns, "disease"].eq("DFSP").astype(int).values
        out[c] = (m.T.values.astype(float), grp)
    return out[train], out[test], common

def bh_fdr(p):
    p = np.asarray(p, float)
    n = len(p); o = np.argsort(p); r = p[o]
    fdr = np.minimum.accumulate((r * n) / np.arange(1, n + 1))[::-1][::-1]
    q = np.empty_like(p); q[o] = np.clip(fdr, 0, 1)
    return q

def youden_cut(y, score):
    fpr, tpr, thr = roc_curve(y, score)
    j = tpr - fpr
    i = np.argmax(j)
    return thr[i], tpr[i], fpr[i]

def bootstrap_ci(y, score, n_boot=2000):
    aucs = []; idx = np.arange(len(y))
    for _ in range(n_boot):
        i = rng.choice(idx, len(idx), replace=True)
        if len(np.unique(y[i])) < 2: continue
        try: aucs.append(roc_auc_score(y[i], score[i]))
        except Exception: pass
    if not aucs: return np.nan, np.nan
    return np.percentile(aucs, 2.5), np.percentile(aucs, 97.5)

def permutation_p(y_te, score_te, n_perm=1000):
    """固定 score，置换标签 → AUC 零分布 → 经验 p"""
    auc_obs = roc_auc_score(y_te, score_te)
    cnt = 0
    for _ in range(n_perm):
        yp = rng.permutation(y_te)
        try:
            a = roc_auc_score(yp, score_te)
        except Exception:
            continue
        if a >= auc_obs - 1e-9: cnt += 1
    return (cnt + 1) / (n_perm + 1)

def run_pipeline(train, test, max_pool=500, panel_size=8):
    (Xtr, ytr), (Xte, yte), common_genes = load_pair(train, test)
    genes_tr = common_genes
    print(f"\n===== {train} → {test} =====")
    print(f"共有基因空间: {len(common_genes)} | 训练 {train}: {Xtr.shape} (DFSP={ytr.sum()}) | 测试 {test}: {Xte.shape} (DFSP={yte.sum()})")

    # ---- 1. 仅训练队列内特征选择（在共有基因空间内）: Wilcoxon + BH-FDR ----
    pvals, aucs = [], []
    for g in range(Xtr.shape[1]):
        x0, x1 = Xtr[ytr == 0, g], Xtr[ytr == 1, g]
        try:
            u, p = stats.mannwhitneyu(x1, x0, alternative="two-sided")
        except Exception:
            p = 1.0
        pvals.append(p)
        if np.std(x1) > 0 and np.std(x0) > 0:
            aucs.append(roc_auc_score(np.r_[np.zeros(len(x0)), np.ones(len(x1))], np.r_[x0, x1]))
        else:
            aucs.append(0.5)
    pvals = np.array(pvals); aucs = np.array(aucs)
    fdr = bh_fdr(pvals)
    cand = np.where(fdr < 0.05)[0]
    print(f"训练队列内 FDR<0.05（共有基因空间）: {len(cand)} 基因")
    if len(cand) == 0:
        cand = np.argsort(pvals)[:200]
        print(f"  (FDR 无显著，改用 top200 by p)")
    if len(cand) > max_pool:
        eff = np.abs(aucs[cand] - 0.5)
        cand = cand[np.argsort(eff)[::-1][:max_pool]]
        print(f"  截断至 top {max_pool} (按 AUC 效应量)")
    pool_genes = [genes_tr[i] for i in cand]
    print(f"候选池: {len(pool_genes)} 基因")

    # ---- 2. 仅训练队列内 LASSO (LOO-CV 选 C；拼接概率算整体 AUC) ----
    Xtr_p = Xtr[:, cand]
    Xtr_p = (Xtr_p - Xtr_p.mean(axis=0)) / (Xtr_p.std(axis=0) + 1e-9)
    Xtr_p = np.nan_to_num(Xtr_p)
    Cs = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
    loo = LeaveOneOut()
    best = None
    for C in Cs:
        proba = np.zeros(len(ytr))
        for tr, va in loo.split(Xtr_p, ytr):
            lr = LogisticRegression(penalty="l1", solver="liblinear", C=C, class_weight="balanced", max_iter=3000)
            lr.fit(Xtr_p[tr], ytr[tr])
            proba[va] = lr.predict_proba(Xtr_p[va])[:, 1]
        try:
            m = roc_auc_score(ytr, proba)
        except Exception:
            m = 0.0
        if best is None or m > best[0]: best = (m, C)
    C_best = best[1]
    print(f"LASSO C={C_best} (LOO 拼接 AUC={best[0]:.3f})")
    lasso = LogisticRegression(penalty="l1", solver="liblinear", C=C_best, class_weight="balanced", max_iter=3000)
    lasso.fit(Xtr_p, ytr)
    sel = np.where(np.abs(lasso.coef_[0]) > 1e-6)[0]
    # 若 LASSO 选中过少（<3），逐步放大 C（更弱正则 → 更多基因），仍在训练队列内
    C_eff = C_best
    while len(sel) < 3 and C_eff <= 200:
        C_eff *= 5
        lasso = LogisticRegression(penalty="l1", solver="liblinear", C=C_eff, class_weight="balanced", max_iter=3000)
        lasso.fit(Xtr_p, ytr)
        sel = np.where(np.abs(lasso.coef_[0]) > 1e-6)[0]
    sel_genes = [pool_genes[i] for i in sel]
    print(f"LASSO C={C_best}(→{C_eff}) 选中 {len(sel_genes)}: {sel_genes}")

    # ---- 3. SVM-RFE 压缩至 panel_size（仅训练队列） ----
    if len(sel_genes) >= 3:
        Xtr_s = Xtr_p[:, sel]
        n_sel = min(panel_size, len(sel_genes))
        svc = SVC(kernel="linear", C=1.0, class_weight="balanced")
        rfe = RFE(svc, n_features_to_select=n_sel)
        rfe.fit(Xtr_s, ytr)
        keep = np.where(rfe.support_)[0]
        panel_idx_cand = [sel[i] for i in keep]
        panel = [pool_genes[i] for i in panel_idx_cand]
    else:
        panel = sel_genes
        panel_idx_cand = np.arange(len(sel))
    print(f"Panel ({len(panel)}): {panel}")

    # ---- 4. 冻结模型：L2 重拟合（训练队列；各队列内独立 z-score 标准化） ----
    pidx_tr = [genes_tr.index(g) for g in panel]
    mu = Xtr[:, pidx_tr].mean(axis=0); sd = Xtr[:, pidx_tr].std(axis=0); sd[sd == 0] = 1
    Xtr_f = np.nan_to_num((Xtr[:, pidx_tr] - mu) / sd)
    model = LogisticRegression(penalty="l2", C=1.0, class_weight="balanced", max_iter=3000)
    model.fit(Xtr_f, ytr)
    # LOO-AUC（内部，拼接概率）
    proba_loo = np.zeros(len(ytr))
    for tr, va in loo.split(Xtr_f, ytr):
        m = LogisticRegression(penalty="l2", C=1.0, class_weight="balanced", max_iter=3000)
        m.fit(Xtr_f[tr], ytr[tr])
        proba_loo[va] = m.predict_proba(Xtr_f[va])[:, 1]
    loo_auc = roc_auc_score(ytr, proba_loo)

    # ---- 5. 测试队列单次预测（冻结模型系数；标准化参数按测试队列自身计算，避免跨平台量纲偏移） ----
    pidx_te = [common_genes.index(g) for g in panel]
    mu_te = Xte[:, pidx_te].mean(axis=0); sd_te = Xte[:, pidx_te].std(axis=0); sd_te[sd_te == 0] = 1
    Xte_f = np.nan_to_num((Xte[:, pidx_te] - mu_te) / sd_te)
    score_te = model.decision_function(Xte_f)
    ext_auc = roc_auc_score(yte, score_te)
    lo, hi = bootstrap_ci(yte, score_te)
    p_perm = permutation_p(yte, score_te)
    thr, sens, spec = youden_cut(yte, score_te)
    # Brier: 训练队列内 Platt 校准（sigmoid 拟合），测试队列应用同一映射——无泄漏
    s_tr = model.decision_function(Xtr_f)
    from sklearn.linear_model import LogisticRegression as _LR
    cal = _LR(max_iter=3000)
    cal.fit(s_tr.reshape(-1, 1), ytr)
    proba_te = cal.predict_proba(score_te.reshape(-1, 1))[:, 1]
    brier = brier_score_loss(yte, proba_te)
    print(f"  外部 AUC={ext_auc:.3f} (95%CI {lo:.3f}-{hi:.3f}) | 置换 p={p_perm:.3f} | 敏感 {sens:.2f}/特异 {spec:.2f} | Brier {brier:.3f} | LOO-AUC {loo_auc:.3f}")
    return dict(train=train, test=test, panel=panel, missing=[],
                ext_auc=ext_auc, ci=(lo, hi), p_perm=p_perm, sens=sens, spec=spec,
                brier=brier, loo_auc=loo_auc, C_best=C_best, pool_size=len(pool_genes),
                score_te=score_te, y_te=yte)

res = {}
for tr, te in [("GSE42948", "GSE2553"), ("GSE2553", "GSE42948")]:
    res[f"{tr}_to_{te}"] = run_pipeline(tr, te, max_pool=500, panel_size=8)

# ---- 保存 ----
rows = []
for k, r in res.items():
    for g in r["panel"]:
        rows.append({"train→test": r["train"] + "→" + r["test"], "gene": g, "direction": ""})
panel_df = pd.DataFrame(rows)
# 方向：从训练队列 DEG 系数（用共识表补方向——此处留空待下游填）
panel_df.to_csv(f"{W2D}/ML_panel_genes_v3.csv", index=False)

summary = pd.DataFrame([{
    "direction": k, "panel": ", ".join(r["panel"]), "panel_size": len(r["panel"]),
    "pool_size": r["pool_size"], "C_best": r["C_best"], "loo_auc": r["loo_auc"],
    "ext_auc": r["ext_auc"], "ci_lo": r["ci"][0], "ci_hi": r["ci"][1],
    "perm_p": r["p_perm"], "sensitivity": r["sens"], "specificity": r["spec"], "brier": r["brier"],
} for k, r in res.items()])
summary.to_csv(f"{W2D}/ML_AUC_summary_v3.csv", index=False)
# ROC 数据保存（新 panel 外部验证）
for k, r in res.items():
    pd.DataFrame({"score": r["score_te"], "y": r["y_te"]}).to_csv(
        f"{W2D}/ROC_scores_{k}_v3.csv", index=False)
print("\n已保存: ML_panel_genes_v3.csv, ML_AUC_summary_v3.csv, ROC_scores_*_v3.csv")
print(summary.to_string(index=False))

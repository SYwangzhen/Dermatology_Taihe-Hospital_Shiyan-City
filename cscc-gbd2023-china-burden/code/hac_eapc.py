# -*- coding: utf-8 -*-
"""
hac_eapc.py — Newey-West (HAC) sensitivity analysis for full-period EAPCs.

Produces the numbers reported in the manuscript (Results "Newey-West
sensitivity analysis" and eMethods 3):
  * OLS EAPC point estimates and 95% CIs (for reference);
  * Newey-West HAC 95% CIs at lag 2 / 3 (prespecified) / 5;
  * Durbin-Watson statistics of the OLS residuals.

Estimator specification (matches eMethods 3):
  * regression  ln(ASR) = a + b*year, OLS;
  * EAPC = 100 * (exp(b) - 1);
  * HAC covariance: Newey-West sandwich with a Bartlett kernel,
    NO prewhitening, NO finite-sample correction
    (V = (X'X)^-1 [ sum_t u_t u_t' + sum_{l=1..L} w_l sum_t (u_t u_{t-l}' + u_{t-l} u_t') ] (X'X)^-1,
     u_t = x_t * e_t, w_l = 1 - l/(L+1));
  * lag rule L = floor(4 * (T/100)^(2/9)) = 3 for T = 34 (prespecified);
    lags 2 and 5 are reported as sensitivity checks.

All manuscript-reported values are asserted at the end of the script;
any mismatch raises AssertionError so the pipeline cannot silently
drift from the manuscript.
"""
import zipfile, csv, io, os, math, json

# BASE 解析：兼容两种布局——脚本位于工程根（本地开发）或 code/ 子目录（投稿 zip 解压后）
def _resolve_base():
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (here, os.path.dirname(here)):
        if os.path.isdir(os.path.join(cand, "data", "raw")):
            return cand
    return os.path.dirname(here)

BASE = _resolve_base()
RAW = os.path.join(BASE, "data", "raw")
OUT = os.path.join(BASE, "data", "processed", "reanalysis_v23")
os.makedirs(OUT, exist_ok=True)

MEAS_EN = {"发病率": "Incidence", "患病率": "Prevalence", "死亡": "Deaths",
           "伤残调整生命年": "DALY rate"}

# ---- load ASR file (age-standardized rates by sex) with strict filtering ----
zf = zipfile.ZipFile(os.path.join(RAW, "IHME-GBD_2023_DATA-cbf696fc-1.zip"))
rows = list(csv.DictReader(io.TextIOWrapper(zf.open(zf.namelist()[0]), "utf-8")))

def asr_series(meas_zh, loc="中国", sex="合计"):
    """Return {year: (val, lower, upper)} with uniqueness + completeness assertions."""
    d = {}
    for r in rows:
        if (r["location_name"] == loc and r["measure_name"] == meas_zh
                and r["sex_name"] == sex and r["metric_name"] == "率"
                and r["age_name"] == "年龄标准化"):
            key = int(r["year"])
            assert key not in d, f"duplicate row: {meas_zh} {loc} {sex} {key}"
            d[key] = (float(r["val"]), float(r["lower"]), float(r["upper"]))
    years = sorted(d)
    assert years == list(range(1990, 2024)), f"incomplete series {meas_zh}: {len(years)} years"
    assert all(v > 0 and lo > 0 for v, lo, _ in d.values()), f"non-positive rates in {meas_zh}"
    return d

def ols_fit(ys, xs):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    e = [y - (a + b * x) for x, y in zip(xs, ys)]
    dw = sum((e[i] - e[i - 1]) ** 2 for i in range(1, n)) / sum(ui ** 2 for ui in e)
    return b, e, dw

def nw_slope_se(xs, e, L):
    """Newey-West HAC SE of the slope (Bartlett kernel, no prewhitening,
    no finite-sample correction). u_t = x_t * e_t with x = [1, year]."""
    import numpy as np
    n = len(xs)
    X = np.column_stack([np.ones(n), np.array(xs, dtype=float)])
    u = X * np.array(e)[:, None]
    meat = u.T @ u
    for l in range(1, L + 1):
        w = 1.0 - l / (L + 1)
        G = u[l:].T @ u[:-l]
        meat += w * (G + G.T)
    XtX_inv = np.linalg.inv(X.T @ X)
    V = XtX_inv @ meat @ XtX_inv
    assert V[1, 1] > 0, "non-positive HAC variance"
    return float(math.sqrt(V[1, 1]))

def pval(z):
    from math import erf, sqrt
    return 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))

def lag_rule(T):
    return math.floor(4 * (T / 100) ** (2 / 9))

# ---- run ----
results = []
LAG_PRE = lag_rule(34)
assert LAG_PRE == 3, f"prespecified lag rule changed: {LAG_PRE}"
print(f"Prespecified lag L = floor(4*(34/100)^(2/9)) = {LAG_PRE}")
print(f"{'measure':<11} {'EAPC':>7} | {'OLS 95% CI':>18} {'P':>6} | "
      f"{'lag2 95% CI':>18} | {'lag3 95% CI':>18} {'P':>6} | {'lag5 95% CI':>18} | {'DW':>5}")
for meas_zh in ["发病率", "患病率", "死亡", "伤残调整生命年"]:
    d = asr_series(meas_zh)
    xs = [float(y) for y in range(1990, 2024)]
    ys = [math.log(d[y][0]) for y in range(1990, 2024)]
    b, e, dw = ols_fit(ys, xs)
    eapc = 100 * (math.exp(b) - 1)
    # OLS SE
    n = len(xs); mx = sum(xs) / n
    xd = [x - mx for x in xs]
    sxx = sum(x ** 2 for x in xd)
    s2 = sum(ui ** 2 for ui in e) / (n - 2)
    se_ols = math.sqrt(s2 / sxx)
    ci = {}
    for L in (2, 3, 5):
        se = nw_slope_se(xs, e, L)
        lo, hi = 100 * (math.exp(b - 1.96 * se) - 1), 100 * (math.exp(b + 1.96 * se) - 1)
        ci[L] = (lo, hi, se, pval(b / se))
    lo_o, hi_o = 100 * (math.exp(b - 1.96 * se_ols) - 1), 100 * (math.exp(b + 1.96 * se_ols) - 1)
    print(f"{MEAS_EN[meas_zh]:<11} {eapc:>+6.2f}% | [{lo_o:+5.2f},{hi_o:+5.2f}] "
          f"{pval(b/se_ols):6.3f} | [{ci[2][0]:+5.2f},{ci[2][1]:+5.2f}] | "
          f"[{ci[3][0]:+5.2f},{ci[3][1]:+5.2f}] {ci[3][3]:6.3f} | "
          f"[{ci[5][0]:+5.2f},{ci[5][1]:+5.2f}] | {dw:5.2f}")
    results.append({"measure": MEAS_EN[meas_zh], "eapc": round(eapc, 2),
                    "ols_ci": [round(lo_o, 2), round(hi_o, 2)],
                    "nw_lag2_ci": [round(ci[2][0], 2), round(ci[2][1], 2)],
                    "nw_lag3_ci": [round(ci[3][0], 2), round(ci[3][1], 2)],
                    "nw_lag3_p": round(ci[3][3], 3),
                    "nw_lag5_ci": [round(ci[5][0], 2), round(ci[5][1], 2)],
                    "durbin_watson": round(dw, 2)})

# ---- assertions against manuscript numbers (Results / eMethods 3) ----
expect = {
    "Incidence":  {"lag3": (2.78, 0.95, 4.64),   "lag5": (2.78, 0.86, 4.73)},
    "Prevalence": {"lag3": (3.87, 1.57, 6.23),   "lag5": (3.87, 1.45, 6.35)},
    "Deaths":     {"lag3": (0.05, -0.35, 0.44),  "lag5": (0.05, -0.39, 0.48)},
    "DALY rate":  {"lag3": (-0.40, -0.77, -0.02), "lag5": (-0.40, -0.81, 0.01)},
}
ok = True
for r in results:
    m = r["measure"]
    for key in ("lag3", "lag5"):
        pt, lo, hi = expect[m][key]
        got = (r["eapc"],) + tuple(r[f"nw_{key}_ci"])
        good = all(abs(g - e) < 0.005 + 1e-9 for g, e in zip(got, (pt, lo, hi)))
        ok &= good
        if not good:
            print(f"ASSERTION FAIL {m} {key}: got {got}, expected {(pt, lo, hi)}")
assert ok, "HAC results drifted from manuscript-reported values"
print("\nAll manuscript HAC values reproduced (lag 3 prespecified; lag 5 sensitivity).")

with open(os.path.join(OUT, "hac_eapc.json"), "w", encoding="utf-8") as f:
    json.dump({"spec": "Newey-West HAC, Bartlett kernel, no prewhitening, no finite-sample correction; "
                       "prespecified lag = floor(4*(T/100)^(2/9)) = 3 (T=34); lags 2 and 5 as sensitivity",
               "results": results}, f, indent=1)
print("output ->", os.path.join(OUT, "hac_eapc.json"))

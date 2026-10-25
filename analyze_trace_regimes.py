"""Point 2: classify traces by a property of the TRACE (not by how badly B1 did), then compare policies.
For every seed we regenerate exactly the arrivals that run_experiments.py used, find the peak arrival rate over
sliding windows, and convert it to the concurrency the Writer stage would need (Little's law:
peak_rate * mean_service). ratio = needed concurrency / container cap. ratio >= 1 means the trace OFFERS more
concurrent work than a non-batching deployment can run at its peak.
Use the SAME trace options as your run:
  python analyze_trace_regimes.py results30/all_runs.csv --azure-csv "data/invocations_per_function_md.anon.d01.csv"
Add --fixed-trace if you ran WITHOUT --vary-trace."""
import argparse, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_experiments as rx
import numpy as np, pandas as pd
from scipy import stats
from chainwarm.config import Config
from chainwarm.workload import counts_to_arrivals

ap = argparse.ArgumentParser()
ap.add_argument("csv", nargs="?", default=os.path.join("results", "all_runs.csv"))
ap.add_argument("--azure-csv", default=None)
ap.add_argument("--n-functions", type=int, default=60)
ap.add_argument("--trigger", default="queue")
ap.add_argument("--start-minute", type=int, default=0)
ap.add_argument("--minutes", type=int, default=60)
ap.add_argument("--rate", type=float, default=1.5)
ap.add_argument("--fixed-trace", action="store_true")
ap.add_argument("--window", type=float, default=60.0, help="sliding window (s) for the peak rate")
ap.add_argument("--threshold", type=float, default=None,
                help="ratio at/above which a trace counts as heavy. Default: split at the MEDIAN ratio of the seeds (a rule fixed in advance)")
a = ap.parse_args()
a.vary_trace = not a.fixed_trace
cfg = Config(mean_rate_jobs_per_s=a.rate, duration_min=a.minutes)
df = pd.read_csv(a.csv)
main = df[df.scenario == "main"]
seeds = sorted(main.seed.unique())
k = 1                                                   # Writer = the longest stage
svc = cfg.compute_s[k] + cfg.llm_median_s[k] * math.exp(cfg.llm_sigma ** 2 / 2)
rows = []
for s in seeds:
    counts, _ = rx.get_counts(a, s if a.vary_trace else 0)
    arr = counts_to_arrivals(counts, cfg.mean_rate_jobs_per_s, cfg.subminute_burst_alpha, s)
    edges = np.arange(0, a.minutes * 60 - a.window + 1, 5.0)
    peak = max(((arr >= t) & (arr < t + a.window)).sum() for t in edges) / a.window
    rows.append(dict(seed=s, peak_rate=peak, needed_concurrency=peak * svc, ratio=peak * svc / cfg.cap_per_stage,
                     burstiness=peak / max(len(arr) / (a.minutes * 60), 1e-9)))
ts = pd.DataFrame(rows).set_index("seed")
ts.to_csv(os.path.join(os.path.dirname(a.csv), "trace_stats.csv"))


def ci(x):
    x = np.asarray(x, float)
    return stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else float("nan")


metrics = ["lat_mean", "lat_p95", "miss_ratio", "cost_per_1k_jobs"]
thr = a.threshold if a.threshold is not None else float(ts.ratio.median())
over = ts.index[ts.ratio > thr].tolist() if a.threshold is None else ts.index[ts.ratio >= thr].tolist()
norm = [s for s in ts.index if s not in over]
out = [f"# Trace-based regimes (ratio = peak {a.window:.0f}-s arrival rate x Writer service / cap {cfg.cap_per_stage})\n",
       f"Split rule fixed in advance: {'median-ratio split (heavy = ratio above the median)' if a.threshold is None else 'ratio >= threshold'}, cut-off = {thr:.3f}. This uses only the trace, not any policy's outcome.\n",
       f"Seeds: {len(seeds)}; lighter: {len(norm)}; heavier: {len(over)}\n",
       "\n## Dose-response (Spearman correlation of ratio with each policy's outcome across seeds)\n"]
rows = []
for p in main.policy.unique():
    m = main[main.policy == p].set_index("seed").loc[ts.index]
    r = {"policy": p}
    for mt in ["lat_p95", "miss_ratio"]:
        rho, pv = stats.spearmanr(ts.ratio, m[mt])
        r[mt] = f"rho={rho:+.2f} (p={pv:.3f})"
    rows.append(r)
out.append(pd.DataFrame(rows).to_markdown(index=False))
for gname, group in [("LIGHTER traces", norm), ("HEAVIER traces", over)]:
    out.append(f"\n## {gname}: n={len(group)} seeds {group}\n")
    if not group:
        out.append("(none)"); continue
    sub = main[main.seed.isin(group)]
    out.append(pd.DataFrame([{"policy": p, **{m: f"{sub[sub.policy == p][m].mean():.3f} ± {ci(sub[sub.policy == p][m]):.3f}"
                              for m in metrics}} for p in sub.policy.unique()]).to_markdown(index=False))
    cw = sub[sub.policy == "ChainWarm"].set_index("seed")
    for other in ["B1-AWS-default", "B1b-AWS-batch4", "B1c-AWS-fixedWindow"]:
        o = sub[sub.policy == other].set_index("seed")
        rr = []
        for m in metrics:
            d = (cw[m] - o[m]).to_numpy(); h = ci(d)
            try:
                pw = stats.wilcoxon(d).pvalue if len(d) > 5 and np.any(d != 0) else float("nan")
            except ValueError:
                pw = float("nan")
            robust = len(d) > 1 and abs(d.mean()) > h and (np.isnan(pw) or pw < 0.05)
            rr.append({"metric": m, "mean_diff": f"{d.mean():+.4f}", "ci95": f"±{h:.4f}",
                       "wilcoxon_p": "n/a (n<=5)" if np.isnan(pw) else f"{pw:.4f}", "robust": "YES" if robust else "no"})
        out.append(f"\nChainWarm minus {other} (paired, n={len(cw)}); 'robust' = CI excludes 0 AND Wilcoxon p<0.05:\n"
                   + pd.DataFrame(rr).to_markdown(index=False))
open(os.path.join(os.path.dirname(a.csv), "trace_regimes.md"), "w", encoding="utf-8").write("\n".join(out))

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
for p in ["B1-AWS-default", "B1b-AWS-batch4", "B4-Universal-Workers", "ChainWarm"]:
    m = main[main.policy == p].set_index("seed").loc[ts.index]
    ax[0].scatter(ts.ratio, m.miss_ratio, label=p, s=25); ax[1].scatter(ts.ratio, m.lat_p95, label=p, s=25)
for x, t in zip(ax, ["Deadline-miss ratio", "P95 latency (s)"]):
    x.axvline(thr, color="k", ls=":"); x.set_xlabel("offered peak concurrency / cap"); x.set_title(t); x.grid(alpha=.3)
ax[1].set_yscale("log"); ax[0].legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(os.path.dirname(a.csv), "fig_trace_regimes.png"), dpi=150)
print("\n".join(out)); print("\nSaved trace_regimes.md, trace_stats.csv, fig_trace_regimes.png")

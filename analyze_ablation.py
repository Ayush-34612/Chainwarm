"""Point 3: paired analysis of the ABLATION runs (ChainWarm vs each variant with one component removed).
'robust' = 95% CI excludes 0 AND Wilcoxon p < 0.05 (both agree). Usage: python analyze_ablation.py results30/all_runs.csv"""
import sys, os
import numpy as np, pandas as pd
from scipy import stats

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("results", "all_runs.csv")
df = pd.read_csv(path)
ab = df[df.scenario == "ablation"]
metrics = ["lat_mean", "lat_p95", "lat_p99", "miss_ratio", "cost_per_1k_jobs", "cold_start_rate", "mean_batch"]
cw = ab[ab.policy == "ChainWarm"].set_index("seed")
what = {"B1-AWS-default": "nothing (plain AWS)",
        "B1c-AWS-fixedWindow": "fixed-window batching only (SQS native)",
        "CW-fixedWait": "fixed wait instead of adaptive wait",
        "CW-noPrewarm": "pre-warming removed",
        "CW-noBatch": "batching removed", "CW-noSlack(FIFO)": "slack priority removed (FIFO)",
        "CW-literalIdle": "slide-5 idle_ready taken literally"}
out = [f"# Ablation: ChainWarm minus variant (per-seed paired), n={len(cw)} seeds\n",
       "Positive lat/cost/miss diff = ChainWarm is WORSE than the variant. `robust` = CI excludes 0 AND Wilcoxon p<0.05.\n"]
for pol in [p for p in ab.policy.unique() if p != "ChainWarm"]:
    o = ab[ab.policy == pol].set_index("seed")
    rows = []
    for m in metrics:
        d = (cw[m] - o[m]).dropna().to_numpy()
        h = stats.t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else float("nan")
        try:
            pw = stats.wilcoxon(d).pvalue if np.any(d != 0) else 1.0
        except ValueError:
            pw = float("nan")
        rel = 100 * (cw[m].mean() / o[m].mean() - 1) if o[m].mean() else float("nan")
        rows.append({"metric": m, "mean_diff": f"{d.mean():+.4f}", "ci95": f"±{h:.4f}", "wilcoxon_p": f"{pw:.4f}",
                     "rel_change": f"{rel:+.1f}%", "robust": "YES" if abs(d.mean()) > h and pw < 0.05 else "no"})
    out.append(f"\n## ChainWarm vs {pol}  ({what.get(pol, '')})\n" + pd.DataFrame(rows).to_markdown(index=False))
dest = os.path.join(os.path.dirname(path), "ablation_paired.md")
open(dest, "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out)); print("\nSaved", dest)

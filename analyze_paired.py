"""Paired comparison of ChainWarm against every other policy, using results/all_runs.csv.
Each seed uses the same trace + same jobs for every policy, so differences are computed PER SEED.
Usage:  python analyze_paired.py [results/all_runs.csv]"""
import sys, os
import numpy as np, pandas as pd
from scipy import stats

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("results", "all_runs.csv")
df = pd.read_csv(path)
main = df[df.scenario == "main"]
metrics = ["lat_mean", "lat_p95", "lat_p99", "miss_ratio", "cost_per_1k_jobs", "cold_start_rate"]
cw = main[main.policy == "ChainWarm"].set_index("seed")
out = ["# Paired comparison: ChainWarm minus other policy (per-seed differences)\n",
       "Negative diff = ChainWarm lower (better for every metric here). `sig` = 95% CI of the mean diff excludes 0.\n",
       f"Seeds: {len(cw)}\n"]
for pol in [p for p in main.policy.unique() if p != "ChainWarm"]:
    o = main[main.policy == pol].set_index("seed")
    rows = []
    for m in metrics:
        d = (cw[m] - o[m]).dropna().to_numpy()
        n = len(d)
        mean = d.mean()
        half = stats.t.ppf(0.975, n - 1) * d.std(ddof=1) / np.sqrt(n) if n > 1 else float("nan")
        try:
            p = stats.wilcoxon(d).pvalue if np.any(d != 0) else 1.0
        except ValueError:
            p = float("nan")
        rel = 100 * (cw[m].mean() / o[m].mean() - 1) if o[m].mean() else float("nan")
        rows.append(dict(metric=m, mean_diff=f"{mean:.4f}", ci95=f"±{half:.4f}", wilcoxon_p=f"{p:.4f}",
                         rel_change_of_means=f"{rel:+.1f}%", sig="YES" if abs(mean) > half else "no"))
    out.append(f"\n## ChainWarm vs {pol}\n" + pd.DataFrame(rows).to_markdown(index=False))
text = "\n".join(out)
dest = os.path.join(os.path.dirname(path), "paired_comparison.md")
open(dest, "w", encoding="utf-8").write(text)
print(text)
print("\nSaved", dest)

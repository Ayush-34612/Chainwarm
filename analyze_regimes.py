"""Point 2: split seeds into NORMAL vs OVERLOADED traces and compare policies inside each group.
A seed is 'overloaded' if the AWS-default baseline (B1) misses more than --threshold of deadlines on it.
Usage: python analyze_regimes.py [results/all_runs.csv] [--threshold 0.05]"""
import sys, os, argparse
import numpy as np, pandas as pd
from scipy import stats

ap = argparse.ArgumentParser()
ap.add_argument("csv", nargs="?", default=os.path.join("results", "all_runs.csv"))
ap.add_argument("--threshold", type=float, default=0.05)
a = ap.parse_args()
df = pd.read_csv(a.csv)
main = df[df.scenario == "main"]
b1 = main[main.policy == "B1-AWS-default"].set_index("seed")
over = set(b1.index[b1.miss_ratio > a.threshold])
groups = {"NORMAL": sorted(set(b1.index) - over), f"OVERLOADED (B1 miss > {a.threshold:.0%})": sorted(over)}
metrics = ["lat_mean", "lat_p95", "miss_ratio", "cost_per_1k_jobs", "cold_start_rate"]


def ci(x):
    x = np.asarray(x, float)
    return stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else float("nan")


out = [f"# Regime split (threshold: B1 miss ratio > {a.threshold})\n"]
for gname, seeds in groups.items():
    out.append(f"\n## {gname}: {len(seeds)} seeds {seeds}\n")
    if not seeds:
        out.append("(no seeds in this group)\n"); continue
    sub = main[main.seed.isin(seeds)]
    rows = []
    for p in sub.policy.unique():
        s = sub[sub.policy == p]
        rows.append({"policy": p, **{m: f"{s[m].mean():.3f} ± {ci(s[m]):.3f}" for m in metrics}})
    out.append(pd.DataFrame(rows).to_markdown(index=False))
    cw = sub[sub.policy == "ChainWarm"].set_index("seed")
    for other in ["B1-AWS-default", "B1b-AWS-batch4", "B1c-AWS-fixedWindow"]:
        o = sub[sub.policy == other].set_index("seed")
        rows = []
        for m in metrics:
            d = (cw[m] - o[m]).to_numpy()
            h = ci(d)
            rows.append({"metric": m, "mean_diff (CW - other)": f"{d.mean():.4f}", "ci95": f"±{h:.4f}",
                         "sig": "YES" if len(d) > 1 and abs(d.mean()) > h else "no"})
        out.append(f"\nChainWarm vs {other} (paired, n={len(cw)}):\n" + pd.DataFrame(rows).to_markdown(index=False))
text = "\n".join(out)
dest = os.path.join(os.path.dirname(a.csv), "regimes.md")
open(dest, "w", encoding="utf-8").write(text)
print(text); print("\nSaved", dest)

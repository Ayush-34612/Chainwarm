"""Point 3: evaluate the slide-4 global objective for every policy.
score = a*mean(L)/Lref + b*P95(L)/Lref + g*Cost/Cref + r*(deadline-miss fraction)      (lower is better)
Lref = mean latency of B1, Cref = cost per 1k jobs of B1 (averaged over all seeds), so B1's first three terms
are ~1 each. Weight sets are ASSUMPTIONS - state them in your report and keep the sensitivity table.
Usage: python analyze_objective.py [results/all_runs.csv]"""
import sys, os
import numpy as np, pandas as pd
from scipy import stats

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("results", "all_runs.csv")
df = pd.read_csv(path)
main = df[df.scenario == "main"].copy()
b1 = main[main.policy == "B1-AWS-default"]
Lref, Cref = b1.lat_mean.mean(), b1.cost_per_1k_jobs.mean()
W = {"balanced":       (0.25, 0.25, 0.25, 0.25),
     "latency-first":  (0.35, 0.35, 0.10, 0.20),
     "cost-first":     (0.10, 0.10, 0.60, 0.20),
     "deadline-first": (0.15, 0.15, 0.10, 0.60)}


def ci(x):
    x = np.asarray(x, float)
    return stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else float("nan")


out = [f"# Slide-4 objective (lower = better)\n\nLref = {Lref:.2f} s (B1 mean latency), Cref = {Cref:.4f} $/1k jobs (B1 cost).\n"
       "Weights (alpha, beta, gamma, rho): " + "; ".join(f"{k}={v}" for k, v in W.items()) + "\n"]
for name, (al, be, ga, rh) in W.items():
    main["score"] = (al * main.lat_mean / Lref + be * main.lat_p95 / Lref
                     + ga * main.cost_per_1k_jobs / Cref + rh * main.miss_ratio)
    rows = []
    cw = main[main.policy == "ChainWarm"].set_index("seed").score
    for p in main.policy.unique():
        s = main[main.policy == p].set_index("seed").score
        d = (cw - s).to_numpy()
        rows.append({"policy": p, "score": f"{s.mean():.3f} ± {ci(s):.3f}",
                     "CW minus this (paired)": "-" if p == "ChainWarm" else f"{d.mean():+.3f} ± {ci(d):.3f}",
                     "CW significantly better?": "-" if p == "ChainWarm" else ("YES" if d.mean() < -ci(d) else
                                                  "WORSE" if d.mean() > ci(d) else "no")})
    out.append(f"\n## {name}  (alpha, beta, gamma, rho) = {W[name]}\n" + pd.DataFrame(rows).to_markdown(index=False))
text = "\n".join(out)
dest = os.path.join(os.path.dirname(path), "objective.md")
open(dest, "w", encoding="utf-8").write(text)
print(text); print("\nSaved", dest)

"""Generate Evaluation-2 presentation figures from the results30_v2/ run.
Run:  python generate_eval2_figures.py [path/to/all_runs.csv]

Produces:
  fig_pareto.png          – Cost vs Mean-latency trade-off (all MAIN policies)
  fig_per_seed_scatter.png – Per-seed (CW - B1b) latency vs trace load ratio
  fig_ablation_cost_lat.png – Ablation bars: cost AND latency side-by-side with CIs
  fig_load_sweep_miss.png  – Miss ratio vs arrival rate for B1 / B1b / B1c / CW
  fig_improvement_summary.png – Summary bar: CW improvement over each paper baseline
"""
import sys, os, math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

# ── resolve paths ─────────────────────────────────────────────────────────────
csv_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("results30", "all_runs.csv")
out_dir   = os.path.dirname(os.path.abspath(csv_path))
trace_csv = os.path.join(out_dir, "trace_stats.csv")

df   = pd.read_csv(csv_path)
main = df[df.scenario == "main"].copy()
abl  = df[df.scenario == "ablation"].copy()

def ci95(x):
    x = np.asarray(x, float)
    if len(x) < 2: return 0.0
    return float(stats.t.ppf(0.975, len(x)-1) * x.std(ddof=1) / np.sqrt(len(x)))

# ── colour palette ────────────────────────────────────────────────────────────
POLICY_COLOR = {
    "B1-AWS-default":       "#d62728",
    "B1b-AWS-batch4":       "#ff7f0e",
    "B1c-AWS-fixedWindow":  "#bcbd22",
    "B2-Maestro-like":      "#9467bd",
    "B3-Chimera-like":      "#8c564b",
    "B4-Universal-Workers": "#e377c2",
    "ChainWarm":            "#2ca02c",
}
POLICY_LABEL = {
    "B1-AWS-default":       "B1 AWS-default",
    "B1b-AWS-batch4":       "B1b Batch-4 (no wait)",
    "B1c-AWS-fixedWindow":  "B1c Fixed-window (2s)",
    "B2-Maestro-like":      "B2 Maestro-like (2026)",
    "B3-Chimera-like":      "B3 Chimera-like (2026)",
    "B4-Universal-Workers": "B4 Universal Workers (2025)",
    "ChainWarm":            "ChainWarm (ours)",
}

# ══════════════════════════════════════════════════════════════════════════════
# Figure 1 – Pareto: Cost vs Mean Latency
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5.5))
for pol in main.policy.unique():
    sub = main[main.policy == pol]
    x = sub.cost_per_1k_jobs.mean()
    y = sub.lat_mean.mean()
    ex = ci95(sub.cost_per_1k_jobs)
    ey = ci95(sub.lat_mean)
    col = POLICY_COLOR.get(pol, "grey")
    lbl = POLICY_LABEL.get(pol, pol)
    ax.errorbar(x, y, xerr=ex, yerr=ey, fmt='o', color=col, markersize=9,
                capsize=4, label=lbl, zorder=3)
    ax.annotate(lbl, (x, y), textcoords="offset points", xytext=(6, 3),
                fontsize=7, color=col)

# Shaded "better" quadrant relative to B1
b1x = main[main.policy=="B1-AWS-default"].cost_per_1k_jobs.mean()
b1y = main[main.policy=="B1-AWS-default"].lat_mean.mean()
xlim = ax.get_xlim(); ylim = ax.get_ylim()
ax.axvline(b1x, color='grey', ls=':', lw=0.8)
ax.axhline(b1y, color='grey', ls=':', lw=0.8)
ax.text(xlim[0]+0.003, ylim[0]+0.5, "← lower cost + lower latency\n(better region)", fontsize=7, color='green')

ax.set_xlabel("Cost per 1 000 jobs (\\$)", fontsize=11)
ax.set_ylabel("Mean end-to-end latency (s)", fontsize=11)
ax.set_title("Cost–Latency Trade-off: All Policies\n(real Azure 2019 trace, 30 seeds, mean ± 95% CI)", fontsize=11)
ax.legend(fontsize=7, loc="upper left")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(out_dir, "fig_pareto.png"), dpi=150)
plt.close(fig)
print("fig_pareto.png saved")

# ══════════════════════════════════════════════════════════════════════════════
# Figure 2 – Per-seed scatter: (CW − B1b) latency vs trace load ratio
# ══════════════════════════════════════════════════════════════════════════════
if os.path.exists(trace_csv):
    ts  = pd.read_csv(trace_csv).set_index("seed")
    cw  = main[main.policy == "ChainWarm"].set_index("seed")
    b1b = main[main.policy == "B1b-AWS-batch4"].set_index("seed")
    b1c = main[main.policy == "B1c-AWS-fixedWindow"].set_index("seed") if "B1c-AWS-fixedWindow" in main.policy.values else None
    common = ts.index.intersection(cw.index).intersection(b1b.index)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    diff_lat  = (cw.loc[common, "lat_mean"] - b1b.loc[common, "lat_mean"]).values
    diff_cost = (cw.loc[common, "cost_per_1k_jobs"] - b1b.loc[common, "cost_per_1k_jobs"]).values
    ratio     = ts.loc[common, "ratio"].values

    sc = ax.scatter(ratio, diff_lat, c=diff_cost, cmap="RdYlGn_r", s=60, zorder=3, edgecolors='k', lw=0.4)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Cost diff CW−B1b (\\$/1k)", fontsize=9)
    ax.axhline(0, color='black', lw=0.9, ls='--')
    ax.set_xlabel("Trace load ratio  (peak concurrency / cap)", fontsize=11)
    ax.set_ylabel("CW minus B1b  mean latency (s)", fontsize=11)
    ax.set_title("Per-seed: ChainWarm latency vs B1b vs trace load\n(positive = CW slower; colour = cost saving)", fontsize=10)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig_per_seed_scatter.png"), dpi=150)
    plt.close(fig)
    print("fig_per_seed_scatter.png saved")
else:
    print("trace_stats.csv not found – skipping per-seed scatter")

# ══════════════════════════════════════════════════════════════════════════════
# Figure 3 – Ablation: cost AND latency side-by-side with CIs
# ══════════════════════════════════════════════════════════════════════════════
abl_order = [p for p in ["B1-AWS-default", "B1c-AWS-fixedWindow", "CW-fixedWait",
                          "CW-noPrewarm", "CW-noBatch", "CW-noSlack(FIFO)",
                          "CW-literalIdle", "ChainWarm"] if p in abl.policy.values]
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, (metric, label, better) in zip(axes, [
        ("cost_per_1k_jobs", "Cost per 1 000 jobs (\\$)", "lower"),
        ("lat_mean",         "Mean end-to-end latency (s)", "lower")]):
    means = [abl[abl.policy==p][metric].mean() for p in abl_order]
    cis   = [ci95(abl[abl.policy==p][metric])  for p in abl_order]
    colors = ["#2ca02c" if p == "ChainWarm" else
              "#d62728" if p == "B1-AWS-default" else
              "#bcbd22" if p == "B1c-AWS-fixedWindow" else
              "#ff7f0e" for p in abl_order]
    bars = ax.bar(range(len(abl_order)), means, yerr=cis, color=colors, capsize=4, width=0.6)
    ax.set_xticks(range(len(abl_order)))
    short = {"B1-AWS-default": "B1\n(AWS)", "B1c-AWS-fixedWindow": "B1c\n(fixedWin)",
             "CW-fixedWait": "CW-\nfixedWait", "CW-noPrewarm": "CW-no\nPrewarm",
             "CW-noBatch": "CW-no\nBatch", "CW-noSlack(FIFO)": "CW-no\nSlack",
             "CW-literalIdle": "CW-\nliteralIdle", "ChainWarm": "ChainWarm\n(full)"}
    ax.set_xticklabels([short.get(p, p) for p in abl_order], fontsize=8)
    ax.set_ylabel(label, fontsize=10)
    ax.set_title(f"Ablation: {label}", fontsize=10)
    ax.grid(axis='y', alpha=0.3)
fig.suptitle("Ablation Study: Effect of Each Component (30 seeds, mean ± 95% CI)", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(out_dir, "fig_ablation_cost_lat.png"), dpi=150)
plt.close(fig)
print("fig_ablation_cost_lat.png saved")

# ══════════════════════════════════════════════════════════════════════════════
# Figure 4 – Improvement summary vs paper baselines (bar chart)
# ══════════════════════════════════════════════════════════════════════════════
paper_baselines = [p for p in ["B2-Maestro-like", "B3-Chimera-like", "B4-Universal-Workers"]
                   if p in main.policy.values]
cw_data = main[main.policy == "ChainWarm"].set_index("seed")
metrics_imp = [("cost_per_1k_jobs", "Cost/1k jobs reduction (%)"),
               ("cold_start_rate",  "Cold-start rate reduction (%)"),
               ("miss_ratio",       "Deadline-miss reduction (%)")]

fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
for ax, (metric, ylabel) in zip(axes, metrics_imp):
    labels, heights, errs = [], [], []
    for pol in paper_baselines:
        o  = main[main.policy == pol].set_index("seed")
        d  = (cw_data[metric] - o[metric]).dropna()
        # relative improvement = how much CW is lower (positive = CW better)
        rel_diff_pct = -100 * d / o[metric].replace(0, np.nan)
        labels.append(POLICY_LABEL.get(pol, pol))
        heights.append(rel_diff_pct.mean())
        errs.append(ci95(rel_diff_pct))
    colors = ["#9467bd", "#8c564b", "#e377c2"][:len(labels)]
    ax.bar(range(len(labels)), heights, yerr=errs, color=colors, capsize=4, width=0.5)
    ax.axhline(0, color='k', lw=0.8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8, rotation=12, ha='right')
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(ylabel, fontsize=9)
    ax.grid(axis='y', alpha=0.3)
fig.suptitle("ChainWarm improvement over 2025–2026 paper baselines\n(positive = CW better; mean ± 95% CI, 30 seeds)",
             fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(out_dir, "fig_improvement_summary.png"), dpi=150)
plt.close(fig)
print("fig_improvement_summary.png saved")

# ══════════════════════════════════════════════════════════════════════════════
# Figure 5 – B1 vs B1b vs B1c vs CW: miss ratio across load levels (load sweep)
# ══════════════════════════════════════════════════════════════════════════════
load = df[df.scenario.str.startswith("load=")].copy()
if not load.empty:
    focus = [p for p in ["B1-AWS-default","B1b-AWS-batch4","B1c-AWS-fixedWindow","ChainWarm"]
             if p in load.policy.values]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, (metric, ylabel) in zip(axes, [("miss_ratio","Deadline-miss ratio"),
                                            ("cost_per_1k_jobs","Cost / 1k jobs (\\$)")]):
        for pol in focus:
            s = load[load.policy==pol].groupby("x")[metric].mean()
            ax.plot(s.index, s.values, "o-", label=POLICY_LABEL.get(pol,pol),
                    color=POLICY_COLOR.get(pol,"grey"))
        ax.set_xlabel("Mean arrival rate (jobs/s)", fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(ylabel, fontsize=10)
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=7)
    fig.suptitle("Load Sweep: miss ratio and cost vs arrival rate", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig_load_sweep_miss.png"), dpi=150)
    plt.close(fig)
    print("fig_load_sweep_miss.png saved")
else:
    print("No load-sweep rows found – skipping fig_load_sweep_miss")

print(f"\nAll figures written to {out_dir}")

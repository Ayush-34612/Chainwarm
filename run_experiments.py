"""Run all experiments, write CSVs, plots and a markdown summary into ./results"""
import argparse, copy, os, sys, time, glob
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import simpy  # noqa
except ImportError:                                    # offline test fallback only
    sys.path.insert(0, os.path.join(HERE, "tests", "mini_simpy"))
    print("!! real SimPy not found - using the tiny test shim. Run `pip install simpy` for final results.")

from chainwarm.config import Config
from chainwarm.workload import (load_azure_trace, synthetic_minute_counts, counts_to_arrivals, make_jobs)
from chainwarm.engine import Sim
from chainwarm.policies import make_policy

MAIN = ["B1", "B1b", "B1c", "B2", "B3", "B4", "CW"]
ABL  = ["B1", "B1c", "CW-fixedWait", "CW-noPrewarm", "CW-noBatch", "CW-noSlack", "CW-literalIdle", "CW"]


def get_counts(args, seed):
    if args.azure_csv:
        return load_azure_trace(args.azure_csv, n_functions=args.n_functions, trigger=args.trigger,
                                start_minute=args.start_minute, minutes=args.minutes, seed=seed), "azure2019"
    return synthetic_minute_counts(args.minutes, seed), "SYNTHETIC"


def one_run(cfg, args, pol, seed):
    counts, src = get_counts(args, seed if args.vary_trace else 0)
    arr = counts_to_arrivals(counts, cfg.mean_rate_jobs_per_s, cfg.subminute_burst_alpha, seed)
    jobs = make_jobs(arr, cfg, seed)
    res, lat = Sim(cfg, jobs, make_policy(pol), seed).run()
    res.update(seed=seed, source=src)
    return res, lat


def ci95(x):
    x = np.asarray(x, float)
    if len(x) < 2: return 0.0
    from scipy import stats
    return float(stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)))


def _task(t):
    cfg, args, p, s = t
    return one_run(cfg, args, p, s)


def sweep(cfg, args, policies, seeds, tag):
    tasks = [(cfg, args, p, s) for p in policies for s in seeds]
    if args.jobs > 1:
        import multiprocessing as mp
        with mp.Pool(args.jobs) as pool:
            out = pool.map(_task, tasks, chunksize=1)
    else:
        out = [_task(t) for t in tasks]
    rows, lats = [], {}
    for r, lat in out:
        r["scenario"] = tag
        rows.append(r)
        lats.setdefault(r["policy"], []).append(lat)
    print(f"  [{tag}] {len(tasks)} runs done", flush=True)
    return pd.DataFrame(rows), lats


def summary_table(df, cols):
    g = df.groupby("policy", sort=False)
    out = pd.DataFrame({"policy": list(g.groups.keys())}).set_index("policy")
    for c in cols:
        out[c] = [f"{g.get_group(p)[c].mean():.3f} ± {ci95(g.get_group(p)[c]):.3f}" for p in out.index]
    return out.reset_index()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--azure-csv", default=None, help="glob to Azure 2019 invocations_per_function_md.anon.d01.csv")
    ap.add_argument("--n-functions", type=int, default=60)
    ap.add_argument("--trigger", default="queue", help="queue|http|timer|event|any")
    ap.add_argument("--start-minute", type=int, default=0)
    ap.add_argument("--minutes", type=int, default=60)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--rate", type=float, default=1.5, help="mean arrival rate (jobs/s) after rescaling the trace")
    ap.add_argument("--vary-trace", action="store_true", help="different function sample / trace per seed")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1, help="parallel worker processes")
    ap.add_argument("--sweep-seeds", type=int, default=5)
    ap.add_argument("--quick", action="store_true", help="3 seeds, 20 min, skip sweeps")
    ap.add_argument("--no-sweeps", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    args = ap.parse_args()
    if args.quick:
        args.seeds, args.minutes, args.no_sweeps = 3, 20, True
    os.makedirs(args.out, exist_ok=True)
    cfg = Config(mean_rate_jobs_per_s=args.rate, duration_min=args.minutes)
    seeds = list(range(args.seeds))
    cols = ["lat_mean", "lat_p95", "lat_p99", "miss_ratio", "cost_per_1k_jobs", "cold_start_rate",
            "mean_batch", "goodput_per_min"]

    print("== 1. Main comparison"); main_df, lats = sweep(cfg, args, MAIN, seeds, "main")
    main_df.to_csv(os.path.join(args.out, "main_runs.csv"), index=False)
    print("== 2. Ablation");        abl_df, _ = sweep(cfg, args, ABL, seeds, "ablation")
    abl_df.to_csv(os.path.join(args.out, "abl_runs.csv"), index=False)
    frames = [main_df, abl_df]
    load_df = ka_df = None
    if not args.no_sweeps:
        print("== 3. Load sweep")
        parts = []
        for r in [1.0, 1.5, 2.5, 3.5]:
            c2 = copy.deepcopy(cfg); c2.mean_rate_jobs_per_s = r
            d, _ = sweep(c2, args, MAIN, seeds[:args.sweep_seeds], f"load={r}"); d["x"] = r; parts.append(d)
        load_df = pd.concat(parts); frames.append(load_df)
        print("== 4. Keep-alive sweep")
        parts = []
        for ka in [30, 120, 600]:
            c2 = copy.deepcopy(cfg); c2.keepalive_s = ka
            d, _ = sweep(c2, args, MAIN, seeds[:args.sweep_seeds], f"keepalive={ka}"); d["x"] = ka; parts.append(d)
        ka_df = pd.concat(parts); frames.append(ka_df)

    pd.concat(frames).to_csv(os.path.join(args.out, "all_runs.csv"), index=False)

    # ---------------- markdown summary
    md = [f"# ChainWarm results\n\nTrace source: **{main_df.source.iloc[0]}**; seeds: {len(seeds)}; "
          f"mean rate {args.rate} jobs/s; {args.minutes} min window; values are mean ± 95% CI.\n"]
    md.append("## Main comparison\n" + summary_table(main_df, cols).to_markdown(index=False))
    md.append("\n## Ablation\n" + summary_table(abl_df, cols).to_markdown(index=False))
    cw = main_df[main_df.policy == "ChainWarm"].set_index("seed")
    for bname in ["B1-AWS-default", "B1b-AWS-batch4", "B1c-AWS-fixedWindow"]:
        base = main_df[main_df.policy == bname].set_index("seed")
        imp = lambda m: 100 * (1 - cw[m] / base[m].replace(0, np.nan)).mean()
        md.append(f"\n## ChainWarm vs {bname} (mean % reduction across seeds; negative = ChainWarm worse)\n"
                  f"- mean latency: {imp('lat_mean'):.1f}%\n- P95 latency: {imp('lat_p95'):.1f}%\n"
                  f"- P99 latency: {imp('lat_p99'):.1f}%\n- cost / 1k jobs: {imp('cost_per_1k_jobs'):.1f}%\n"
                  f"- deadline miss ratio: {imp('miss_ratio'):.1f}%\n")
    for nm, d, lab in [("Load sweep", load_df, "rate"), ("Keep-alive sweep", ka_df, "keepalive_s")]:
        if d is not None:
            md.append(f"\n## {nm}\n" + d.groupby(["x", "policy"], sort=False)[
                ["lat_p95", "miss_ratio", "cost_per_1k_jobs", "cold_start_rate"]].mean().round(4).to_markdown())
    open(os.path.join(args.out, "summary.md"), "w").write("\n".join(md))

    # ---------------- plots
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    order = list(main_df.policy.unique()); colors = plt.cm.tab10(np.arange(len(order)))
    fig, ax = plt.subplots(2, 3, figsize=(15, 8))
    for a, (m, t) in zip(ax.ravel(), [("lat_mean", "Mean latency (s)"), ("lat_p95", "P95 latency (s)"),
            ("lat_p99", "P99 latency (s)"), ("cost_per_1k_jobs", "Cost per 1k jobs ($)"),
            ("cold_start_rate", "Cold-start rate"), ("miss_ratio", "Deadline-miss ratio")]):
        mu = [main_df[main_df.policy == p][m].mean() for p in order]
        er = [ci95(main_df[main_df.policy == p][m]) for p in order]
        a.bar(range(len(order)), mu, yerr=er, color=colors, capsize=3)
        a.set_xticks(range(len(order))); a.set_xticklabels([p.split("-")[0] if p != "ChainWarm" else "CW" for p in order])
        a.set_title(t)
    fig.suptitle(f"Main comparison ({main_df.source.iloc[0]} trace)"); fig.tight_layout()
    fig.savefig(os.path.join(args.out, "fig_main.png"), dpi=150); plt.close(fig)

    fig, a = plt.subplots(figsize=(7, 4.5))
    for p, c in zip(order, colors):
        x = np.sort(np.concatenate(lats[p])); a.plot(x, np.arange(1, len(x) + 1) / len(x), label=p, color=c)
    a.set_xlabel("End-to-end latency (s)"); a.set_ylabel("CDF"); a.legend(); a.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(args.out, "fig_latency_cdf.png"), dpi=150); plt.close(fig)

    fig, a = plt.subplots(figsize=(8, 4.5))
    ab = ["B1-AWS-default"] + [p for p in abl_df.policy.unique() if p != "B1-AWS-default"]
    a.bar(range(len(ab)), [abl_df[abl_df.policy == p].miss_ratio.mean() for p in ab],
          yerr=[ci95(abl_df[abl_df.policy == p].miss_ratio) for p in ab], capsize=3)
    a.set_xticks(range(len(ab))); a.set_xticklabels(ab, rotation=25, ha="right"); a.set_ylabel("Deadline-miss ratio")
    a.set_title("Ablation"); fig.tight_layout(); fig.savefig(os.path.join(args.out, "fig_ablation.png"), dpi=150); plt.close(fig)

    for d, nm, xl in [(load_df, "fig_load_sweep.png", "Mean arrival rate (jobs/s)"),
                      (ka_df, "fig_keepalive_sweep.png", "Platform keep-alive (s)")]:
        if d is None: continue
        fig, ax = plt.subplots(1, 3, figsize=(15, 4))
        for a, (m, t) in zip(ax, [("lat_p95", "P95 latency (s)"), ("miss_ratio", "Deadline-miss ratio"),
                                  ("cost_per_1k_jobs", "Cost per 1k jobs ($)")]):
            for p, c in zip(order, colors):
                s = d[d.policy == p].groupby("x")[m].mean(); a.plot(s.index, s.values, "o-", label=p, color=c)
            a.set_xlabel(xl); a.set_title(t); a.grid(alpha=.3)
        ax[0].legend(fontsize=7); fig.tight_layout(); fig.savefig(os.path.join(args.out, nm), dpi=150); plt.close(fig)
    print("\nDone. See", args.out)
    print(open(os.path.join(args.out, "summary.md")).read())


if __name__ == "__main__":
    main()

"""Point 1: does the result survive different assumptions?  One-at-a-time sweeps of the assumptions the
cost/latency result depends on, comparing B1 / B1b / ChainWarm on identical traces (paired by seed).
Usage (same trace options as run_experiments.py):
  python run_sensitivity.py --azure-csv "data/invocations_per_function_md.anon.d01.csv" --vary-trace --seeds 10 --jobs 4 --out results_sens
"""
import argparse, copy, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_experiments as rx                       # also installs the offline SimPy fallback if needed
import numpy as np, pandas as pd
from scipy import stats
from chainwarm.config import Config

SWEEPS = {                                          # parameter -> values (default value is marked in config.py)
    "batch_cpu_contention": [0.0, 0.5, 1.0, 2.0],   # extra CPU per co-batched job (x compute time)
    "mem_extra_per_job_gb": [0.0, 0.0625, 0.125, 0.25],
    "cw_b_max": [1, 2, 4, 8],                       # batch capacity (B1b uses the same value)
    "cw_w_cap_s": [0.5, 1.0, 2.0, 4.0],             # max time ChainWarm waits to fill a batch
    "cold_median_s": [0.9, 1.8, 3.6],               # container cold-start time
}
POLICIES = ["B1", "B1b", "CW"]


def _task(t):
    param, value, cfg, args, pol, seed = t
    r, _ = rx.one_run(cfg, args, pol, seed)
    r.update(param=param, value=value)
    return r


def ci(x):
    x = np.asarray(x, float)
    return stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--azure-csv", default=None)
    ap.add_argument("--n-functions", type=int, default=60)
    ap.add_argument("--trigger", default="queue")
    ap.add_argument("--start-minute", type=int, default=0)
    ap.add_argument("--minutes", type=int, default=60)
    ap.add_argument("--rate", type=float, default=1.5)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--vary-trace", action="store_true")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--out", default=os.path.join(HERE, "results_sens"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    base = Config(mean_rate_jobs_per_s=a.rate, duration_min=a.minutes)
    seeds = list(range(a.seeds))
    tasks = []
    for pol in POLICIES:                              # the default setting, run once
        for s in seeds:
            tasks.append(("default", None, base, a, pol, s))
    for param, values in SWEEPS.items():
        dflt = getattr(base, param)
        for v in values:
            if v == dflt:
                continue
            c = copy.deepcopy(base); setattr(c, param, v)
            for pol in POLICIES:
                for s in seeds:
                    tasks.append((param, v, c, a, pol, s))
    print(f"{len(tasks)} runs on {a.jobs} process(es)...", flush=True)
    if a.jobs > 1:
        import multiprocessing as mp
        with mp.Pool(a.jobs) as pool:
            rows = pool.map(_task, tasks, chunksize=2)
    else:
        rows = [_task(t) for t in tasks]
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(a.out, "sensitivity_runs.csv"), index=False)

    names = {"B1": "B1-AWS-default", "B1b": "B1b-AWS-batch4", "CW": "ChainWarm"}
    dflt_rows = df[df.param == "default"]
    out = ["# Sensitivity of ChainWarm to modelling assumptions\n",
           f"Seeds per cell: {len(seeds)} (paired by seed; same traces for all policies). "
           "dCost% = change in mean cost of ChainWarm relative to the other policy; other deltas are mean paired "
           "differences (ChainWarm minus other) ± 95% CI. Default values are marked with *.\n"]
    summary = []
    for param, values in SWEEPS.items():
        dflt = getattr(base, param)
        rows_md = []
        for v in values:
            sub = dflt_rows if v == dflt else df[(df.param == param) & (df.value == v)]
            cw = sub[sub.policy == names["CW"]].set_index("seed")
            line = {"value": f"{v}{'*' if v == dflt else ''}"}
            for tag in ["B1b", "B1"]:
                o = sub[sub.policy == names[tag]].set_index("seed")
                dc = 100 * (cw.cost_per_1k_jobs.mean() / o.cost_per_1k_jobs.mean() - 1)
                dl = (cw.lat_mean - o.lat_mean).to_numpy()
                dp = (cw.lat_p95 - o.lat_p95).to_numpy()
                dm = (cw.miss_ratio - o.miss_ratio).to_numpy()
                line.update({f"dCost% vs {tag}": f"{dc:+.1f}",
                             f"dMeanLat(s) vs {tag}": f"{dl.mean():+.2f} ± {ci(dl):.2f}",
                             f"dP95(s) vs {tag}": f"{dp.mean():+.2f} ± {ci(dp):.2f}",
                             f"dMiss vs {tag}": f"{dm.mean():+.4f} ± {ci(dm):.4f}"})
                summary.append(dict(param=param, value=v, vs=tag, dcost=dc, dlat=dl.mean(), dlat_ci=ci(dl)))
            rows_md.append(line)
        out.append(f"\n## {param}\n" + pd.DataFrame(rows_md).to_markdown(index=False))
    open(os.path.join(a.out, "sensitivity.md"), "w", encoding="utf-8").write("\n".join(out))

    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    sm = pd.DataFrame(summary); sm = sm[sm.vs == "B1b"]
    fig, ax = plt.subplots(2, len(SWEEPS), figsize=(4 * len(SWEEPS), 7))
    for i, param in enumerate(SWEEPS):
        d = sm[sm.param == param].sort_values("value")
        ax[0, i].plot(d.value.astype(float), d.dcost, "o-"); ax[0, i].axhline(0, color="k", lw=.6)
        ax[0, i].set_title(param, fontsize=9); ax[0, i].set_ylabel("ChainWarm cost vs B1b (%)" if i == 0 else "")
        ax[1, i].errorbar(d.value.astype(float), d.dlat, yerr=d.dlat_ci, fmt="o-", capsize=3)
        ax[1, i].axhline(0, color="k", lw=.6); ax[1, i].set_xlabel("value")
        ax[1, i].set_ylabel("ChainWarm mean latency minus B1b (s)" if i == 0 else "")
    fig.tight_layout(); fig.savefig(os.path.join(a.out, "fig_sensitivity.png"), dpi=150)
    print(open(os.path.join(a.out, "sensitivity.md"), encoding="utf-8").read())
    print("\nSaved to", a.out)


if __name__ == "__main__":
    main()

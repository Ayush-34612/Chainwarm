"""Workload generation.

1. load_azure_trace()  -> per-minute invocation counts from the REAL Azure Functions 2019 dataset
2. synthetic_minute_counts() -> Azure-like fallback (diurnal + bursty). Use ONLY for debugging;
   final results must come from the real trace.
3. counts_to_arrivals() -> turns per-minute counts into arrival timestamps (seconds).
4. make_jobs() -> pipeline jobs (service times + deadlines), identical across policies for one seed.
"""
from __future__ import annotations
import glob
import numpy as np


# ----------------------------------------------------------------------------------------
# 1. Real Azure Functions trace (Shahrad et al., ATC 2020 - "Serverless in the Wild")
#    Files: invocations_per_function_md.anon.dNN.csv  (NN = 01..14)
#    Columns: HashOwner, HashApp, HashFunction, Trigger, 1, 2, ..., 1440 (invocations per minute)
# ----------------------------------------------------------------------------------------
def load_azure_trace(path_glob: str, n_functions: int = 60, trigger: str = "queue",
                     start_minute: int = 0, minutes: int = 60, seed: int = 0) -> np.ndarray:
    import pandas as pd
    files = sorted(glob.glob(path_glob))
    if not files:
        raise FileNotFoundError(f"No Azure CSV matched: {path_glob}")
    df = pd.read_csv(files[0])
    minute_cols = [c for c in df.columns if str(c).isdigit()]
    if trigger and trigger != "any":
        sub = df[df["Trigger"].astype(str).str.lower() == trigger.lower()]
        df = sub if len(sub) >= n_functions else df       # fall back to all triggers if too few
    totals = df[minute_cols].sum(axis=1)
    df = df[totals > 0]
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(df), size=min(n_functions, len(df)), replace=False)
    series = df.iloc[pick][minute_cols].to_numpy(dtype=float).sum(axis=0)
    window = series[start_minute:start_minute + minutes]
    if len(window) < minutes:
        raise ValueError("Requested window runs past the end of the day (1440 minutes).")
    return window


# ----------------------------------------------------------------------------------------
# 2. Synthetic Azure-like fallback (NOT real data)
# ----------------------------------------------------------------------------------------
def synthetic_minute_counts(minutes: int = 60, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(minutes)
    base = 1.0 + 0.35 * np.sin(2 * np.pi * t / 45.0 + rng.uniform(0, 6.28))   # slow drift
    burst = np.ones(minutes)
    m = 0
    while m < minutes:
        if rng.random() < 0.06:                                               # burst start
            length = int(rng.integers(2, 6))
            burst[m:m + length] *= rng.uniform(2.0, 3.5)
            m += length
        else:
            m += 1
    noise = rng.lognormal(0.0, 0.25, size=minutes)
    return 1000.0 * base * burst * noise


# ----------------------------------------------------------------------------------------
# 3. Minute counts -> arrival timestamps
# ----------------------------------------------------------------------------------------
def counts_to_arrivals(counts: np.ndarray, mean_rate: float, alpha: float, seed: int) -> np.ndarray:
    """Rescale so the mean rate is `mean_rate` jobs/s, draw Poisson counts per minute, then spread
    each minute's arrivals over six 10-second bins with Dirichlet(alpha) weights (sub-minute bursts,
    which the per-minute Azure data cannot show)."""
    rng = np.random.default_rng(seed + 7919)
    scale = mean_rate * 60.0 / max(counts.mean(), 1e-9)
    out = []
    for m, c in enumerate(counts):
        n = rng.poisson(c * scale)
        if n == 0:
            continue
        w = rng.dirichlet(np.full(6, alpha))
        bins = rng.choice(6, size=n, p=w)
        out.append(m * 60.0 + bins * 10.0 + rng.uniform(0, 10.0, size=n))
    return np.sort(np.concatenate(out)) if out else np.array([])


# ----------------------------------------------------------------------------------------
# 4. Jobs
# ----------------------------------------------------------------------------------------
class Job:
    __slots__ = ("id", "arrival", "deadline", "svc", "stage", "enq", "finish",
                 "chimera_pred", "cold_flags", "queue_wait")

    def __init__(self, jid, arrival, deadline, svc):
        self.id, self.arrival, self.deadline, self.svc = jid, arrival, deadline, svc
        self.stage, self.enq, self.finish = 0, arrival, None
        self.chimera_pred = None
        self.cold_flags = []
        self.queue_wait = 0.0


def make_jobs(arrivals: np.ndarray, cfg, seed: int):
    rng = np.random.default_rng(seed + 104729)
    K = len(cfg.stage_names)
    jobs = []
    for i, a in enumerate(arrivals):
        svc = []
        for k in range(K):
            llm = float(np.clip(rng.lognormal(np.log(cfg.llm_median_s[k]), cfg.llm_sigma),
                                cfg.llm_min_s, cfg.llm_max_s))
            svc.append(cfg.compute_s[k] + llm)
        expected = sum(cfg.compute_s[k] + cfg.llm_median_s[k] * np.exp(cfg.llm_sigma ** 2 / 2) for k in range(K))
        mult = rng.uniform(cfg.deadline_mult_lo, cfg.deadline_mult_hi)
        jobs.append(Job(i, float(a), float(a + mult * expected), svc))
    return jobs

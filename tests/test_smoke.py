"""Sanity tests. Run:  python -m pytest -q tests     (or)   python tests/test_smoke.py"""
import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
try:
    import simpy  # noqa
except ImportError:
    sys.path.insert(0, os.path.join(HERE, "mini_simpy"))
import numpy as np, pandas as pd
from chainwarm.config import Config
from chainwarm.workload import load_azure_trace, synthetic_minute_counts, counts_to_arrivals, make_jobs
from chainwarm.engine import Sim
from chainwarm.policies import make_policy


def _jobs(seed=0, minutes=5, rate=1.0, cfg=None):
    cfg = cfg or Config()
    arr = counts_to_arrivals(synthetic_minute_counts(minutes, seed), rate, 2.0, seed)
    return cfg, make_jobs(arr, cfg, seed)


def test_all_jobs_finish_and_order_is_causal():
    for p in ["B1", "B1b", "B2", "B3", "B4", "CW", "CW-noPrewarm", "CW-noBatch", "CW-noSlack", "CW-literalIdle"]:
        cfg, jobs = _jobs()
        res, lat = Sim(cfg, jobs, make_policy(p), 0).run()
        assert all(j.finish is not None for j in jobs), p
        # a job can never finish faster than its pure service time
        assert all(j.finish - j.arrival >= sum(j.svc) - 1e-6 for j in jobs), p
        assert res["cost_total"] > 0 and 0 <= res["cold_start_rate"] <= 1, p


def test_same_seed_same_result():
    a = Sim(*_jobs(), make_policy("CW"), 0).run()[0]
    b = Sim(*_jobs(), make_policy("CW"), 0).run()[0]
    assert a["lat_mean"] == b["lat_mean"] and a["cost_total"] == b["cost_total"]


def test_no_cold_start_when_everything_is_warm_and_idle():
    cfg = Config(); cfg.keepalive_s = 1e9
    cfg, jobs = _jobs(cfg=cfg, minutes=10, rate=0.5)
    res, _ = Sim(cfg, jobs, make_policy("B1"), 0).run()
    assert res["cold_start_rate"] < 0.5          # most invocations reuse warm containers


def test_azure_loader_on_fake_csv():
    d = tempfile.mkdtemp()
    cols = ["HashOwner", "HashApp", "HashFunction", "Trigger"] + [str(i) for i in range(1, 1441)]
    rng = np.random.default_rng(0)
    rows = [["o", "a", f"f{i}", "queue" if i % 2 else "http"] + list(rng.poisson(5, 1440)) for i in range(40)]
    pd.DataFrame(rows, columns=cols).to_csv(os.path.join(d, "invocations_per_function_md.anon.d01.csv"), index=False)
    c = load_azure_trace(os.path.join(d, "invocations_per_function_md.anon.d*.csv"), n_functions=10,
                         trigger="queue", start_minute=100, minutes=30)
    assert c.shape == (30,) and c.sum() > 0


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("PASS", n)

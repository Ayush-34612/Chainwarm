"""Scheduling policies.

B1  AwsDefault        FIFO, one job per invocation, platform keep-alive only (SQS -> Lambda default).
B2  MaestroLike       workflow-aware queueing: least-slack-first using the remaining workflow runtime.
B3  ChimeraLike       predicts remaining work (noisy) and serves shortest-predicted-remaining first.
B4  UniversalWorkers  stage-agnostic shared worker pool with cheaper initialisation; FIFO.
CW  ChainWarm         predictor + JIT pre-warming + batching + chain-aware slack priority.

IMPORTANT (say this in your report): B2-B4 are *simplified re-implementations of the scheduling idea
credited to each paper, adapted to a FaaS setting*, not the authors' code. Re-read each paper and make
sure your description of what you implemented matches what the paper actually proposes.
"""
from __future__ import annotations
import math
from collections import deque
import numpy as np


class Policy:
    name = "B1-AWS-default"
    universal = False
    cold_factor = 1.0
    tick_interval = 5.0

    def attach(self, sim):
        self.sim, self.cfg = sim, sim.cfg

    # --- queue / batching decisions --------------------------------------------------
    def batch_max(self, k): return 1
    def priority(self, job, k, now): return now - job.enq              # FIFO
    def wait_limit(self, k, B, now): return 0.0
    def idle_ready_ok(self, k, B, now): return True

    # --- hooks ------------------------------------------------------------------------
    def on_enqueue(self, job, k, now): pass
    def on_dispatch(self, k, B, cold, cold_dur, begin): pass
    def on_stage_done(self, job, k, now, dur): pass
    def tick(self, now): pass

    # --- helper: expected service time of a stage (static prior) -----------------------
    def prior_service(self, k):
        c = self.cfg
        return c.compute_s[k] + c.llm_median_s[k] * math.exp(c.llm_sigma ** 2 / 2)


class AwsDefault(Policy):
    name = "B1-AWS-default"


class AwsBatch(Policy):
    """B1b: AWS default plus SQS batching (BatchSize=4, no batching window): a fair 'batching only' baseline.
    A freed/idle container takes up to 4 queued jobs at once; nothing is ever held back to fill a batch."""
    name = "B1b-AWS-batch4"

    def batch_max(self, k): return self.cfg.cw_b_max      # same batch capacity as ChainWarm (default 4)


class MaestroLike(Policy):
    name = "B2-Maestro-like"

    def priority(self, job, k, now):
        remaining = sum(self.prior_service(i) for i in range(k, self.sim.K))
        return -(job.deadline - now - remaining)                       # least slack first


class ChimeraLike(Policy):
    name = "B3-Chimera-like"

    def attach(self, sim):
        super().attach(sim)
        self.rng = np.random.default_rng(12345)
        self.pred = {}

    def priority(self, job, k, now):
        key = (job.id, k)
        if key not in self.pred:                                       # noisy remaining-work prediction
            true_rem = sum(job.svc[k:])
            self.pred[key] = true_rem * float(self.rng.lognormal(0.0, self.cfg.chimera_noise_sigma))
        return -self.pred[key]                                         # shortest predicted remaining first


class AwsBatchWindow(Policy):
    """B1c: SQS-style fixed batching window (MaximumBatchingWindowInSeconds).
    Batch size = B_max (default 4); waits up to a fixed window W = cw_w_cap_s (default 2 s)
    before dispatching, regardless of whether a warm container is available.
    No pre-warming, no chain-aware priority — just platform-native fixed-window batching.
    This is the fairest 'platform feature only' comparison for ChainWarm's adaptive wait."""
    name = "B1c-AWS-fixedWindow"

    def batch_max(self, k): return self.cfg.cw_b_max   # same batch capacity as CW

    def wait_limit(self, k, B, now): return self.cfg.cw_w_cap_s  # fixed window, never adaptive

    def idle_ready_ok(self, k, B, now): return False    # do NOT dispatch early on idle; always honour window


class UniversalWorkers(Policy):
    name = "B4-Universal-Workers"
    universal = True

    def attach(self, sim):
        super().attach(sim)
        self.cold_factor = self.cfg.universal_cold_factor


class ChainWarm(Policy):
    """Full system with switches so each component can be ablated."""

    def __init__(self, prewarm=True, batching=True, slack_priority=True, name="ChainWarm",
                 idle_mode=None, fixed_wait=False):
        self.name = name
        self.f_prewarm, self.f_batch, self.f_slack = prewarm, batching, slack_priority
        self.idle_mode = idle_mode
        self.fixed_wait = fixed_wait   # if True, use cw_w_cap_s directly instead of adaptive formula

    def attach(self, sim):
        super().attach(sim)
        c, K = self.cfg, sim.K
        self.tick_interval = c.cw_tick_s
        if self.idle_mode is None:
            self.idle_mode = c.cw_idle_ready_mode
        self.arr_count = [0] * K
        self.level = [0.0] * K
        self.trend = [0.0] * K
        self.warm_up = [True] * K
        self.obs = [deque(maxlen=300) for _ in range(K)]            # observed service times
        self.cold_est = c.cold_median_s
        self.p_miss = [0.3] * K                                     # EWMA probability a dispatch is cold
        self.bbar = [1.0] * K                                       # EWMA batch size
        self.soon = [0] * K                                         # jobs expected to finish stage k very soon
        self.soon_flag = set()
        self._qcache = {}

    # ------------------------------------------------------------ online estimates
    def s_hat(self, k, q=None):
        """Online quantile of observed stage service time (cached; refreshed every tick)."""
        q = self.cfg.cw_runtime_quantile if q is None else q
        key = (k, q)
        hit = self._qcache.get(key)
        if hit is not None:
            return hit
        o = self.obs[k]
        v = float(np.quantile(o, q)) if len(o) >= 20 else self.prior_service(k)
        self._qcache[key] = v
        return v

    def lam_hat(self, k, horizon=None):
        h = self.cfg.cw_forecast_horizon_s if horizon is None else horizon
        steps = min(h / self.cfg.cw_tick_s, 3.0)                    # cap the trend extrapolation
        return max(0.0, self.level[k] + self.trend[k] * steps)

    def slack(self, job, k, now):
        rem = sum(self.s_hat(i) for i in range(k, self.sim.K))
        cold = sum(self.cold_est * self.p_miss[i] for i in range(k + 1, self.sim.K))
        return job.deadline - now - rem - cold                      # sigma_{j,k}(t) from slide 4.5

    # ------------------------------------------------------------ decisions
    def batch_max(self, k): return self.cfg.cw_b_max if self.f_batch else 1

    def priority(self, job, k, now):
        if not self.f_slack:
            return now - job.enq
        return -self.slack(job, k, now) + self.cfg.cw_theta * (now - job.enq)

    def _min_slack(self, k, B, now):
        return min(self.slack(j, k, now) for j in B)

    def wait_limit(self, k, B, now):
        if not self.f_batch:
            return 0.0
        c = self.cfg
        if self.fixed_wait:                                # CW-fixedWait ablation: same window as B1c
            return c.cw_w_cap_s
        ms = self._min_slack(k, B, now)
        if ms <= c.cw_urgent_slack_s:
            return 0.0
        lam = self.lam_hat(k)
        if lam * c.cw_w_cap_s < 0.5:                                # too few arrivals expected: batching can't help
            return 0.0
        need = self.batch_max(k) - len(B)
        return max(0.0, min(c.cw_w_cap_s, need / max(lam, 1e-6), c.cw_slack_frac * ms))

    def idle_ready_ok(self, k, B, now):
        if self.idle_mode == "literal" or not self.f_batch:
            return True
        return self._min_slack(k, B, now) <= self.cfg.cw_urgent_slack_s

    # ------------------------------------------------------------ hooks
    def on_enqueue(self, job, k, now):
        self.arr_count[k] += 1

    def on_dispatch(self, k, B, cold, cold_dur, begin):
        a = 0.1
        self.p_miss[k] = (1 - a) * self.p_miss[k] + a * (1.0 if cold else 0.0)
        self.bbar[k] = (1 - a) * self.bbar[k] + a * len(B)
        if cold and cold_dur > 0:
            self.cold_est = 0.9 * self.cold_est + 0.1 * cold_dur
        if self.f_prewarm and k < self.sim.K - 1:
            for j in B:
                self.sim.env.process(self._jit(j, k, begin))

    def on_stage_done(self, job, k, now, dur):
        self.obs[k].append(dur)
        if (job.id, k) in self.soon_flag:
            self.soon_flag.discard((job.id, k))
            self.soon[k] -= 1

    # ------------------------------------------------------------ just-in-time chain pre-warming
    def _jit(self, job, k, begin):
        """Warm stage k+1 so a container is ready around the earliest plausible finish of stage k."""
        env, c = self.sim.env, self.cfg
        q_lo = self.s_hat(k, c.cw_early_quantile)
        delay = (begin - env.now) + max(0.0, q_lo - self.cold_est)
        yield env.timeout(delay)
        if job.stage != k:                                          # already finished stage k
            return
        self.soon[k] += 1
        self.soon_flag.add((job.id, k))
        n = k + 1
        tot, idle, warm, busy = self.sim.pool_stats(n)
        supply = idle + warm
        demand = math.ceil(self.soon[k] / max(self.bbar[n], 1.0))
        if supply >= demand:
            return
        p_miss = (demand - supply) / demand
        e_idle = max(0.5, self.s_hat(k, 0.5) - q_lo)                # expected idle time of the container
        gain = c.cw_kappa * self.cold_est * p_miss
        cost = c.price_idle_gbs * self.sim.mem_of(n) * e_idle
        if gain > cost:                                             # slide 4.5 pre-warm condition
            self.sim.start_prewarm(n)

    # ------------------------------------------------------------ predictor + pool controller (every tick)
    def tick(self, now):
        c, K = self.cfg, self.sim.K
        self._qcache.clear()
        for k in range(K):
            rate = self.arr_count[k] / c.cw_tick_s
            self.arr_count[k] = 0
            if self.warm_up[k]:
                self.level[k], self.trend[k], self.warm_up[k] = rate, 0.0, False
            else:                                                   # Holt's linear trend (EWMA + trend)
                prev = self.level[k]
                self.level[k] = c.cw_holt_alpha * rate + (1 - c.cw_holt_alpha) * (prev + self.trend[k])
                self.trend[k] = c.cw_holt_beta * (self.level[k] - prev) + (1 - c.cw_holt_beta) * self.trend[k]
        if not self.f_prewarm:
            return
        for k in range(K):
            lam = self.lam_hat(k)
            window = self.cold_est + c.cw_tick_s                    # arrivals during one cold start + one tick
            needed = math.ceil(lam * window / max(self.bbar[k], 1.0))
            tot, idle, warm, busy = self.sim.pool_stats(k)
            supply = idle + warm
            if needed <= supply or needed == 0:
                continue
            p_miss = (needed - supply) / needed
            e_idle = min(c.prewarm_ttl_s, (supply + 1) * max(self.bbar[k], 1.0) / max(lam, 1e-9))
            if c.cw_kappa * self.cold_est * p_miss > c.price_idle_gbs * self.sim.mem_of(k) * e_idle:
                for _ in range(needed - supply):
                    if not self.sim.start_prewarm(k):
                        break


def make_policy(name: str):
    table = {
        "B1":  AwsDefault, "B1b": AwsBatch, "B1c": AwsBatchWindow,
        "B2":  MaestroLike, "B3": ChimeraLike, "B4": UniversalWorkers,
        "CW":             lambda: ChainWarm(),
        "CW-noPrewarm":   lambda: ChainWarm(prewarm=False, name="CW-noPrewarm"),
        "CW-noBatch":     lambda: ChainWarm(batching=False, name="CW-noBatch"),
        "CW-noSlack":     lambda: ChainWarm(slack_priority=False, name="CW-noSlack(FIFO)"),
        "CW-literalIdle": lambda: ChainWarm(idle_mode="literal", name="CW-literalIdle"),
        "CW-fixedWait":   lambda: ChainWarm(fixed_wait=True, name="CW-fixedWait"),
    }
    return table[name]()

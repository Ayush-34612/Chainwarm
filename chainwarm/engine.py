"""Discrete-event serverless pipeline simulator built on SimPy.

Model in one paragraph
----------------------
Jobs enter stage 1 (Researcher) -> 2 (Writer) -> 3 (Reviewer). Each stage has an SQS-like queue and a
pool of containers (Lambda-like, concurrency-capped). A *policy* decides (a) the order of the queue,
(b) how many jobs share one container invocation (SQS batch), (c) how long to wait to fill a batch,
and (d) whether/when to start containers before they are needed. The engine does the bookkeeping:
cold starts, warm reuse, keep-alive eviction, per-GB-second billing and metrics.
"""
from __future__ import annotations
import math
import numpy as np

try:
    import simpy
except ImportError as e:                                   # pragma: no cover
    raise SystemExit("SimPy is required:  pip install simpy") from e


class Container:
    __slots__ = ("pool", "stage", "state", "ready_at", "expire_at", "prewarmed", "mem")

    def __init__(self, pool, stage, mem, ready_at):
        self.pool, self.stage, self.mem = pool, stage, mem
        self.state = "idle"            # 'idle' (free, maybe still warming) | 'busy'
        self.ready_at = ready_at       # time it can start executing
        self.expire_at = math.inf
        self.prewarmed = False


class Sim:
    def __init__(self, cfg, jobs, policy, seed=0):
        self.cfg, self.jobs, self.policy = cfg, jobs, policy
        self.K = len(cfg.stage_names)
        self.env = simpy.Environment()
        self.rng = np.random.default_rng(seed + 31)
        self.queues = [[] for _ in range(self.K)]
        self.pools = {}                                    # pool key -> list[Container]
        self.timer_at = [None] * self.K
        self.finished = 0
        self.done = False
        # metrics
        self.m = dict(cost_exec=0.0, cost_inv=0.0, cost_init=0.0, cost_idle=0.0,
                      runs=0, cold_runs=0, batches=0, batch_jobs=0,
                      prewarm_started=0, prewarm_used=0, prewarm_wasted=0,
                      cold_wait_total=0.0, queue_wait_total=0.0)
        policy.attach(self)

    # ------------------------------------------------------------------ pools
    def pool_key(self, k):
        return 0 if self.policy.universal else k

    def pool_cap(self, k):
        return self.cfg.cap_per_stage * (self.K if self.policy.universal else 1)

    def mem_of(self, k):
        return self.cfg.universal_mem_gb if self.policy.universal else self.cfg.mem_gb[k]

    def cold_sample(self):
        c = float(self.rng.lognormal(np.log(self.cfg.cold_median_s), self.cfg.cold_sigma))
        return c * self.policy.cold_factor

    def purge(self, key):
        now, keep = self.env.now, []
        for c in self.pools.get(key, []):
            if c.state == "idle" and c.expire_at <= now:
                if c.prewarmed:                              # expired unused: pay its idle time
                    self.m["cost_idle"] += max(0.0, c.expire_at - c.ready_at) * c.mem * self.cfg.price_idle_gbs
                    self.m["prewarm_wasted"] += 1
            else:
                keep.append(c)
        self.pools[key] = keep

    def pool_stats(self, k):
        """(total, idle_ready, warming_unclaimed, busy) for the pool serving stage k."""
        key, now = self.pool_key(k), self.env.now
        self.purge(key)
        tot = idle = warm = busy = 0
        for c in self.pools[key]:
            tot += 1
            if c.state == "busy":
                busy += 1
            elif c.ready_at <= now:
                idle += 1
            else:
                warm += 1
        return tot, idle, warm, busy

    def start_prewarm(self, k):
        """Policy-initiated container start (billed init + an invocation, then idle at provisioned rate)."""
        key, now = self.pool_key(k), self.env.now
        self.purge(key)
        pool = self.pools.setdefault(key, [])
        if len(pool) >= self.pool_cap(k):
            return False
        init = self.cold_sample()
        c = Container(key, k, self.mem_of(k), ready_at=now + init)
        c.prewarmed, c.expire_at = True, now + init + self.cfg.prewarm_ttl_s
        pool.append(c)
        self.m["prewarm_started"] += 1
        self.m["cost_init"] += init * c.mem * self.cfg.price_gbs + self.cfg.price_inv
        return True

    # ------------------------------------------------------------------ queueing
    def enqueue(self, job, k):
        job.stage, job.enq = k, self.env.now
        self.queues[k].append(job)
        self.policy.on_enqueue(job, k, self.env.now)
        self.try_dispatch(k)

    def _arm_timer(self, k, delay):
        target = self.env.now + delay
        cur = self.timer_at[k]
        if cur is not None and cur > self.env.now and cur <= target + 1e-9:
            return
        self.timer_at[k] = target
        self.env.process(self._timer(k, delay, target))

    def _timer(self, k, delay, target):
        yield self.env.timeout(delay)
        if self.timer_at[k] == target:
            self.timer_at[k] = None
        self.try_dispatch(k)

    def try_dispatch(self, k):
        env, pol, cfg = self.env, self.policy, self.cfg
        q = self.queues[k]
        while q:
            now = env.now
            key = self.pool_key(k)
            self.purge(key)
            pool = self.pools.setdefault(key, [])
            # priority order
            q.sort(key=lambda j: -pol.priority(j, k, now))
            B = q[:min(pol.batch_max(k), len(q))]
            # find a container: most-recently-ready idle one, else earliest-warming one, else cold start
            ready = [c for c in pool if c.state == "idle" and c.ready_at <= now]
            warming = [c for c in pool if c.state == "idle" and c.ready_at > now]
            can_start = len(pool) < self.pool_cap(k)
            if ready:
                c, kind = max(ready, key=lambda x: x.ready_at), "warm"
            elif warming:
                c, kind = min(warming, key=lambda x: x.ready_at), "warming"
            elif can_start:
                c, kind = None, "cold"
            else:
                return                                       # saturated: wait for a container to free up
            W = pol.wait_limit(k, B, now)
            oldest_wait = now - min(j.enq for j in B)
            idle_ready = (kind == "warm") and pol.idle_ready_ok(k, B, now)
            if len(B) >= pol.batch_max(k) or oldest_wait >= W - 1e-9 or idle_ready:
                for j in B:
                    q.remove(j)
                self._launch(k, B, c, kind, pool)
            else:
                self._arm_timer(k, max(W - oldest_wait, 1e-6))
                return

    # ------------------------------------------------------------------ execution
    def _launch(self, k, B, c, kind, pool):
        env, cfg, now = self.env, self.cfg, self.env.now
        n = len(B)
        cold_dur = 0.0
        if kind == "cold":
            cold_dur = self.cold_sample()
            c = Container(self.pool_key(k), k, self.mem_of(k), ready_at=now + cold_dur)
            pool.append(c)
            self.m["cost_init"] += cold_dur * c.mem * cfg.price_gbs
            startup = cold_dur
        else:
            startup = max(0.0, c.ready_at - now)
            if c.prewarmed:                                  # used a pre-warmed container
                self.m["prewarm_used"] += 1
                self.m["cost_idle"] += max(0.0, now - c.ready_at) * c.mem * cfg.price_idle_gbs
                c.prewarmed = False
        c.state, c.expire_at = "busy", math.inf
        begin = now + startup
        # durations (CPU contention penalty when co-batched)
        durs = [j.svc[k] + cfg.batch_cpu_contention * cfg.compute_s[k] * (n - 1) for j in B]
        billed = max(durs)
        mem_exec = c.mem + cfg.mem_extra_per_job_gb * (n - 1)
        self.m["cost_exec"] += billed * mem_exec * cfg.price_gbs
        self.m["cost_inv"] += cfg.price_inv
        self.m["batches"] += 1
        self.m["batch_jobs"] += n
        self.m["runs"] += n
        if kind == "cold":
            self.m["cold_runs"] += n
        self.m["cold_wait_total"] += startup * n
        for j in B:
            j.queue_wait += now - j.enq
            self.m["queue_wait_total"] += now - j.enq
            j.cold_flags.append(kind == "cold")
        self.policy.on_dispatch(k, B, kind == "cold", cold_dur, begin)
        env.process(self._batch_proc(k, B, durs, c, startup))

    def _batch_proc(self, k, B, durs, c, startup):
        env = self.env
        yield env.timeout(startup)
        elapsed = 0.0
        for j, d in sorted(zip(B, durs), key=lambda x: x[1]):
            yield env.timeout(d - elapsed)
            elapsed = d
            self._stage_done(j, k, d)
        c.state, c.ready_at = "idle", env.now
        c.expire_at = env.now + self.cfg.keepalive_s
        c.prewarmed = False
        if self.policy.universal:
            order = sorted(range(self.K), key=lambda s: min((j.enq for j in self.queues[s]), default=math.inf))
            for s in order:
                self.try_dispatch(s)
        else:
            self.try_dispatch(k)

    def _stage_done(self, job, k, dur):
        self.policy.on_stage_done(job, k, self.env.now, dur)
        if k == self.K - 1:
            job.finish = self.env.now
            self.finished += 1
            if self.finished == len(self.jobs):
                self.done = True
        else:
            self.enqueue(job, k + 1)

    # ------------------------------------------------------------------ driver processes
    def _arrivals(self):
        env = self.env
        for j in self.jobs:
            yield env.timeout(max(0.0, j.arrival - env.now))
            self.enqueue(j, 0)

    def _ticker(self):
        tick = self.policy.tick_interval or 5.0
        while not self.done:
            yield self.env.timeout(tick)
            for key in list(self.pools):
                self.purge(key)
            self.policy.tick(self.env.now)

    def run(self):
        self.env.process(self._arrivals())
        self.env.process(self._ticker())
        self.env.run()
        # flush idle cost of pre-warmed containers that are still alive at the end
        end = self.env.now
        for pool in self.pools.values():
            for c in pool:
                if c.state == "idle" and c.prewarmed:
                    self.m["cost_idle"] += max(0.0, min(c.expire_at, end) - c.ready_at) * c.mem * self.cfg.price_idle_gbs
                    self.m["prewarm_wasted"] += 1
        return self.summarize()

    # ------------------------------------------------------------------ results
    def summarize(self):
        lat = np.array([j.finish - j.arrival for j in self.jobs])
        miss = np.array([j.finish > j.deadline for j in self.jobs])
        m = self.m
        total_cost = m["cost_exec"] + m["cost_inv"] + m["cost_init"] + m["cost_idle"]
        horizon = max(j.finish for j in self.jobs) - min(j.arrival for j in self.jobs)
        on_time = int((~miss).sum())
        return dict(
            policy=self.policy.name, n_jobs=len(self.jobs),
            lat_mean=lat.mean(), lat_p50=np.percentile(lat, 50), lat_p95=np.percentile(lat, 95),
            lat_p99=np.percentile(lat, 99), miss_ratio=miss.mean(),
            cost_total=total_cost, cost_per_1k_jobs=1000 * total_cost / len(self.jobs),
            cost_exec=m["cost_exec"], cost_inv=m["cost_inv"], cost_init=m["cost_init"], cost_idle=m["cost_idle"],
            cold_start_rate=m["cold_runs"] / max(m["runs"], 1),
            mean_batch=m["batch_jobs"] / max(m["batches"], 1),
            queue_wait_mean=m["queue_wait_total"] / max(m["runs"], 1),
            startup_wait_mean=m["cold_wait_total"] / max(m["runs"], 1),
            prewarm_started=m["prewarm_started"], prewarm_used=m["prewarm_used"], prewarm_wasted=m["prewarm_wasted"],
            goodput_per_min=on_time / (horizon / 60.0), makespan_min=horizon / 60.0,
        ), lat

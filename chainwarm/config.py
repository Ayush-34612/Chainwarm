"""All tunable parameters in one place. Every number here is an ASSUMPTION you must justify
(or replace with a measured value) in the final report."""
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Config:
    # ---- pipeline (Researcher -> Writer -> Reviewer) -------------------------------------
    stage_names: Tuple[str, ...] = ("Researcher", "Writer", "Reviewer")
    # external LLM wait per stage: truncated lognormal, clipped to the 5-20 s range on slide 2
    llm_median_s: Tuple[float, ...] = (8.0, 13.0, 9.0)
    llm_sigma: float = 0.35
    llm_min_s: float = 5.0
    llm_max_s: float = 20.0
    compute_s: Tuple[float, ...] = (0.4, 0.6, 0.3)       # CPU time of the handler itself
    batch_cpu_contention: float = 0.5                    # extra CPU s per co-batched job = this * compute_s

    # ---- serverless platform --------------------------------------------------------------
    cold_median_s: float = 1.8                           # container init (runtime + SDK import)
    cold_sigma: float = 0.35
    mem_gb: Tuple[float, ...] = (0.5, 1.0, 0.5)          # memory per container, per stage
    mem_extra_per_job_gb: float = 0.0625                 # +64 MB per additional co-batched job
    cap_per_stage: int = 60                              # account/function concurrency limit
    keepalive_s: float = 120.0                           # platform idle timeout (free, not controllable)
    prewarm_ttl_s: float = 30.0                          # how long an unused pre-warmed container survives

    # ---- pricing (AWS Lambda x86 list prices, us-east-1; update if you want another region) ----
    price_gbs: float = 0.0000166667                      # $ per GB-second executed (and init)
    price_inv: float = 0.0000002                         # $ per invocation ($0.20 / 1M)
    price_idle_gbs: float = 0.0000041667                 # $ per GB-s a *deliberately* pre-warmed container idles
                                                         # (provisioned-concurrency rate)

    # ---- jobs / deadlines -----------------------------------------------------------------
    deadline_mult_lo: float = 1.3                        # deadline = arrival + U(lo,hi) * sum(expected service)
    deadline_mult_hi: float = 2.5

    # ---- workload ---------------------------------------------------------------------------
    mean_rate_jobs_per_s: float = 1.5                    # trace is rescaled to this mean arrival rate
    duration_min: int = 60                               # length of the trace window
    subminute_burst_alpha: float = 2.0                   # Dirichlet alpha for 10-s bins inside a minute (lower = burstier)

    # ---- ChainWarm hyper-parameters ---------------------------------------------------------
    cw_b_max: int = 4                                    # batch capacity B_max
    cw_theta: float = 0.2                                # starvation-prevention weight in priority
    cw_w_cap_s: float = 2.0                              # max time to wait for a batch to fill
    cw_slack_frac: float = 0.10                          # never wait more than this fraction of min slack
    cw_runtime_quantile: float = 0.75                    # quantile used for S_hat in the slack formula
    cw_early_quantile: float = 0.20                      # "earliest plausible finish" quantile for JIT pre-warm
    cw_kappa: float = 1e-4                               # $ value of one second of avoided latency (pre-warm rule)
    cw_forecast_horizon_s: float = 30.0                  # "tens of seconds in advance"
    cw_tick_s: float = 5.0                               # predictor / controller period
    cw_holt_alpha: float = 0.3
    cw_holt_beta: float = 0.1
    cw_urgent_slack_s: float = 8.0                       # gated idle_ready: dispatch at once if min slack below this
    cw_idle_ready_mode: str = "gated"                    # "gated" (default) or "literal" (as on slide 5)

    # ---- baselines ------------------------------------------------------------------------
    chimera_noise_sigma: float = 0.25                    # error of the remaining-time predictor in the Chimera-style baseline
    universal_cold_factor: float = 0.4                   # Universal-Workers-style: shared runtime cuts init time
    universal_mem_gb: float = 1.0                        # ... but generalist workers are sized for the biggest stage

# ChainWarm – SimPy Simulation Repository

Latency- and Cost-Aware Scheduling for Serverless Multi-Agent AI Pipelines  
(`Researcher -> Writer -> Reviewer`, SQS Queues + AWS Lambda-Style Container Pools).

---

## 1. Quick Start & Environment Setup

```bash
# 1. Activate virtual environment
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify simulator with smoke tests (4 PASS lines)
python tests/test_smoke.py
```

---

## 2. Real-World Workload Trace

This repository evaluates scheduling on the real-world **Azure Functions 2019 dataset** (Shahrad et al., USENIX ATC 2020):
- Place `invocations_per_function_md.anon.d01.csv` inside `data/`.
- Slices 60 random `queue`-triggered functions per seed across a 60-minute window, with Dirichlet sub-minute burst distributions.

---

## 3. Running Experiments

### A. Reproduce Evaluation 2 (30 Seeds, Real Trace, Multiprocessed)
```bash
# Run 30-seed simulation with B1c baseline and CW-fixedWait ablation:
python run_experiments.py --azure-csv "data/invocations_per_function_md.anon.d01.csv" --vary-trace --seeds 30 --jobs 10 --no-sweeps --out results30

# Run full downstream statistical analysis pipeline and figure generation:
python run_eval2_analysis.py
```

### B. Exploratory High-Saturation Run ($\lambda = 3.0\text{ jobs/s}$)
```bash
python run_experiments.py --azure-csv "data/invocations_per_function_md.anon.d01.csv" --vary-trace --seeds 20 --jobs 10 --rate 3.0 --no-sweeps --out results_rate3
python analyze_ablation.py results_rate3/all_runs.csv
```

### C. Sensitivity Sweeps (5 Dimensions, 10 Seeds)
```bash
python run_sensitivity.py --azure-csv "data/invocations_per_function_md.anon.d01.csv" --vary-trace --seeds 10 --jobs 10 --out results_sens
```

---

## 4. Repository Structure

```
chainwarm_project/
├── chainwarm/                    # Core simulator package
│   ├── config.py                 # Configuration dataclass (all parameters & pricing)
│   ├── engine.py                 # SimPy discrete-event engine (queues, pools, billing)
│   ├── policies.py               # All 7 policies & ablation variants
│   └── workload.py               # Azure trace loader & synthetic fallback
├── data/                         # Trace storage
│   └── invocations_per_function_md.anon.d01.csv
├── results30/                    # Primary Evaluation 2 dataset (30 seeds, real Azure trace)
│   ├── all_runs.csv              # Raw run data (one row per run)
│   ├── summary.md                # Aggregated metric tables (mean ± 95% CI)
│   ├── paired_comparison.md      # Per-seed paired t-tests & Wilcoxon p-values
│   ├── ablation_paired.md        # Ablation study isolating each component
│   ├── objective.md              # Slide 4 multi-objective scores across 4 weight sets
│   ├── trace_regimes.md          # Dose-response load analysis (Spearman rho)
│   ├── trace_stats.csv           # Per-seed offered peak concurrency metrics
│   ├── fig_pareto.png            # Cost vs. Latency Pareto trade-off curve
│   ├── fig_improvement_summary.png # Improvement bars over Maestro, Chimera, & Universal
│   ├── fig_ablation_cost_lat.png # Side-by-side cost & latency ablation bars with CIs
│   ├── fig_per_seed_scatter.png  # Per-seed latency delta vs trace load
│   ├── fig_trace_regimes.png     # Scatter plot of deadline misses vs offered concurrency
│   └── fig_latency_cdf.png       # End-to-end latency empirical CDF
├── results_rate3/                # Exploratory high-saturation run (rate=3.0, 20 seeds)
├── results_sens/                 # Sensitivity analysis sweeps (5 dimensions)
├── results/                      # Original 10-seed run with load & keep-alive sweeps
├── tests/                        # Smoke tests
│   └── test_smoke.py
├── analyze_paired.py             # Script for per-seed paired differences
├── analyze_ablation.py           # Script for ablation statistical tests
├── analyze_objective.py          # Script for global multi-objective scoring
├── analyze_trace_regimes.py      # Script for trace-based load split & dose-response
├── analyze_regimes.py            # Script for outcome-based load split
├── generate_eval2_figures.py     # Script generating all presentation figures
├── run_eval2_analysis.py         # Unified driver running all analysis scripts
├── run_experiments.py            # Main simulation driver
├── run_sensitivity.py            # Sensitivity analysis driver
├── EVALUATION_2_FINAL_REPORT.md  # Comprehensive Evaluation 2 report & presentation guide
├── requirements.txt              # Python package dependencies
└── README.md                     # This file
```

---

## 5. Evaluated Policies

| Policy ID | Policy Name | Description |
|---|---|---|
| **B1** | `B1-AWS-default` | Standard AWS Lambda FIFO execution (1 request per container, on-demand). |
| **B1b** | `B1b-AWS-batch4` | AWS SQS batching (BatchSize=4) with no waiting window. |
| **B1c** | `B1c-AWS-fixedWindow`| AWS SQS native batching window (`MaximumBatchingWindowInSeconds` = 2s). |
| **B2** | `B2-Maestro-like` | Workflow-aware queueing based on remaining slack (Wang et al., 2026). |
| **B3** | `B3-Chimera-like` | Shortest predicted remaining work first with prediction noise (Ni et al., 2026). |
| **B4** | `B4-Universal-Workers`| Shared generalist 1GB container pool across all stages (Akbari, 2025). |
| **CW** | `ChainWarm` | Full system: Holt predictor + JIT pre-warming + adaptive batching + slack priority. |

---

## 6. Key Scientific Findings

1. **Measurable Improvement Over 2025–2026 Papers**:
   - **−38.9% Cost**, **−92.1% Cold starts**, **−94.5% Deadline misses** vs. Maestro (2026).
   - **−38.9% Cost**, **−92.2% Cold starts**, **−52.3% P99 tail latency** vs. Chimera (2026).
   - **−56.2% Cost**, **−89.2% Cold starts** vs. Universal Workers (2025).
2. **Measurable Improvement Over Native SQS Fixed-Window Batching (B1c)**:
   - Fixed-window batching is blind to deadlines, causing **+220% more deadline misses** and **17× higher cold starts**.
   - ChainWarm's adaptive wait achieves **72% fewer deadline misses**, **95% fewer cold starts**, and **1.76s faster latency**.
3. **Ablation Attribution**:
   - **Batching** drives **100% of cost savings**.
   - **JIT pre-warming** drives **94% of cold-start reduction** for a negligible +3.3% cost overhead.
   - **Slack priority** shows neutral benefit under moderate queue depths.
   - Gating `idle_ready` on urgent slack is essential; literal idle dispatch breaks batching.

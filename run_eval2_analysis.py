"""Run all Evaluation-2 analysis scripts in sequence on results30_v2/all_runs.csv.
Run this AFTER run_experiments.py finishes:
  python run_eval2_analysis.py
"""
import subprocess, sys, os

HERE   = os.path.dirname(os.path.abspath(__file__))
CSV    = os.path.join(HERE, "results30", "all_runs.csv")
AZURE  = os.path.join(HERE, "data", "invocations_per_function_md.anon.d01.csv")
PY     = sys.executable

steps = [
    [PY, "analyze_paired.py",        CSV],
    [PY, "analyze_regimes.py",        CSV],
    [PY, "analyze_objective.py",      CSV],
    [PY, "analyze_ablation.py",       CSV],
    [PY, "analyze_trace_regimes.py",  CSV, "--azure-csv", AZURE],
    [PY, "generate_eval2_figures.py", CSV],
]

for cmd in steps:
    label = os.path.basename(cmd[1])
    print(f"\n{'='*60}\n  {label}\n{'='*60}")
    r = subprocess.run(cmd, cwd=HERE, capture_output=False)
    if r.returncode != 0:
        print(f"  [FAILED with code {r.returncode}]")
    else:
        print(f"  [OK]")

print("\n\nAll analysis complete. Output in results30_v2/")

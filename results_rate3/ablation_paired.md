# Ablation: ChainWarm minus variant (per-seed paired), n=20 seeds

Positive lat/cost/miss diff = ChainWarm is WORSE than the variant. `robust` = CI excludes 0 AND Wilcoxon p<0.05.


## ChainWarm vs B1-AWS-default  (nothing (plain AWS))
| metric           |   mean_diff | ci95      |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:----------|-------------:|:-------------|:---------|
| lat_mean         |    -61.4848 | ±53.6548  |       0.0296 | -61.7%       | YES      |
| lat_p95          |   -149.366  | ±121.2525 |       0      | -73.6%       | YES      |
| lat_p99          |   -158.14   | ±123.6720 |       0      | -72.5%       | YES      |
| miss_ratio       |     -0.2212 | ±0.1310   |       0      | -79.8%       | YES      |
| cost_per_1k_jobs |     -0.1657 | ±0.0042   |       0      | -42.3%       | YES      |
| cold_start_rate  |     -0.0145 | ±0.0017   |       0      | -81.8%       | YES      |
| mean_batch       |      1.4605 | ±0.0511   |       0      | +146.0%      | YES      |

## ChainWarm vs B1c-AWS-fixedWindow  (fixed-window batching only (SQS native))
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:--------|-------------:|:-------------|:---------|
| lat_mean         |     -1.3294 | ±0.2422 |       0      | -3.4%        | YES      |
| lat_p95          |     -0.5324 | ±1.2581 |       0.2305 | -1.0%        | no       |
| lat_p99          |      0.2975 | ±1.7996 |       0.5958 | +0.5%        | no       |
| miss_ratio       |     -0.0069 | ±0.0057 |       0.0083 | -10.9%       | YES      |
| cost_per_1k_jobs |      0.0485 | ±0.0050 |       0      | +27.3%       | YES      |
| cold_start_rate  |     -0.0627 | ±0.0155 |       0      | -95.1%       | YES      |
| mean_batch       |     -1.2998 | ±0.0798 |       0      | -34.6%       | YES      |

## ChainWarm vs CW-fixedWait  (fixed wait instead of adaptive wait)
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:--------|-------------:|:-------------|:---------|
| lat_mean         |     -0.6772 | ±0.2657 |       0.0009 | -1.7%        | YES      |
| lat_p95          |     -0.5386 | ±0.4161 |       0.0094 | -1.0%        | YES      |
| lat_p99          |     -0.4377 | ±0.4499 |       0.0441 | -0.7%        | no       |
| miss_ratio       |      0.0005 | ±0.0017 |       0.099  | +0.9%        | no       |
| cost_per_1k_jobs |      0.0305 | ±0.0035 |       0      | +15.6%       | YES      |
| cold_start_rate  |     -0.0011 | ±0.0012 |       0.0192 | -25.1%       | no       |
| mean_batch       |     -0.7538 | ±0.0686 |       0      | -23.5%       | YES      |

## ChainWarm vs CW-noPrewarm  (pre-warming removed)
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:--------|-------------:|:-------------|:---------|
| lat_mean         |     -0.39   | ±0.1638 |       0      | -1.0%        | YES      |
| lat_p95          |     -0.5734 | ±0.1982 |       0      | -1.1%        | YES      |
| lat_p99          |     -0.5915 | ±0.2331 |       0      | -1.0%        | YES      |
| miss_ratio       |     -0.0023 | ±0.0025 |       0      | -4.0%        | no       |
| cost_per_1k_jobs |      0.0053 | ±0.0008 |       0      | +2.4%        | YES      |
| cold_start_rate  |     -0.0468 | ±0.0100 |       0      | -93.5%       | YES      |
| mean_batch       |      0.0031 | ±0.0015 |       0.0007 | +0.1%        | YES      |

## ChainWarm vs CW-noBatch  (batching removed)
| metric           |   mean_diff | ci95      |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:----------|-------------:|:-------------|:---------|
| lat_mean         |    -60.9924 | ±53.4536  |       0.04   | -61.5%       | YES      |
| lat_p95          |   -149.539  | ±120.8666 |       0      | -73.6%       | YES      |
| lat_p99          |   -161.371  | ±123.7856 |       0      | -72.9%       | YES      |
| miss_ratio       |     -0.2152 | ±0.1324   |       0.024  | -79.4%       | YES      |
| cost_per_1k_jobs |     -0.1678 | ±0.0043   |       0      | -42.6%       | YES      |
| cold_start_rate  |      0.0006 | ±0.0007   |       0.2024 | +23.1%       | no       |
| mean_batch       |      1.4605 | ±0.0511   |       0      | +146.0%      | YES      |

## ChainWarm vs CW-noSlack(FIFO)  (slack priority removed (FIFO))
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:--------|-------------:|:-------------|:---------|
| lat_mean         |     -0.0276 | ±0.1291 |       0.2943 | -0.1%        | no       |
| lat_p95          |      0.7399 | ±0.8800 |       0.1474 | +1.4%        | no       |
| lat_p99          |      1.4958 | ±1.2508 |       0.005  | +2.6%        | YES      |
| miss_ratio       |     -0.0018 | ±0.0041 |       0.1167 | -3.1%        | no       |
| cost_per_1k_jobs |     -0      | ±0.0001 |       0.7841 | -0.0%        | no       |
| cold_start_rate  |     -0      | ±0.0000 |       0.8753 | -0.0%        | no       |
| mean_batch       |      0.0005 | ±0.0010 |       0.7285 | +0.0%        | no       |

## ChainWarm vs CW-literalIdle  (slide-5 idle_ready taken literally)
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:--------|-------------:|:-------------|:---------|
| lat_mean         |      1.312  | ±0.3085 |       0      | +3.6%        | YES      |
| lat_p95          |      0.7926 | ±0.5849 |       0.0296 | +1.5%        | YES      |
| lat_p99          |      0.6823 | ±0.6720 |       0.0192 | +1.1%        | YES      |
| miss_ratio       |     -0.0001 | ±0.0009 |       0.2024 | -0.1%        | no       |
| cost_per_1k_jobs |     -0.1136 | ±0.0205 |       0      | -33.4%       | YES      |
| cold_start_rate  |      0.0007 | ±0.0007 |       0.0532 | +27.9%       | no       |
| mean_batch       |      1.191  | ±0.1443 |       0      | +93.8%       | YES      |
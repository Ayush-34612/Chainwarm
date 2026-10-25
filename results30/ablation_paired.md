# Ablation: ChainWarm minus variant (per-seed paired), n=30 seeds

Positive lat/cost/miss diff = ChainWarm is WORSE than the variant. `robust` = CI excludes 0 AND Wilcoxon p<0.05.


## ChainWarm vs B1-AWS-default  (nothing (plain AWS))
| metric           |   mean_diff | ci95     |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:---------|-------------:|:-------------|:---------|
| lat_mean         |     -5.2845 | ±7.4524  |       0.3931 | -13.0%       | no       |
| lat_p95          |    -17.3458 | ±19.0995 |       0.7    | -27.3%       | no       |
| lat_p99          |    -18.9201 | ±19.9493 |       0.7151 | -27.1%       | no       |
| miss_ratio       |     -0.0793 | ±0.0666  |       0.685  | -94.6%       | no       |
| cost_per_1k_jobs |     -0.1532 | ±0.0022  |       0      | -38.9%       | YES      |
| cold_start_rate  |     -0.0426 | ±0.0053  |       0      | -92.1%       | YES      |
| mean_batch       |      1.2696 | ±0.0292  |       0      | +127.0%      | YES      |

## ChainWarm vs B1c-AWS-fixedWindow  (fixed-window batching only (SQS native))
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:--------|-------------:|:-------------|:---------|
| lat_mean         |     -1.7552 | ±0.0920 |            0 | -4.7%        | YES      |
| lat_p95          |     -1.8229 | ±0.3725 |            0 | -3.8%        | YES      |
| lat_p99          |     -1.9413 | ±0.4906 |            0 | -3.7%        | YES      |
| miss_ratio       |     -0.0118 | ±0.0024 |            0 | -72.1%       | YES      |
| cost_per_1k_jobs |      0.0508 | ±0.0022 |            0 | +26.8%       | YES      |
| cold_start_rate  |     -0.0672 | ±0.0175 |            0 | -94.9%       | YES      |
| mean_batch       |     -1.0208 | ±0.0269 |            0 | -31.0%       | YES      |

## ChainWarm vs CW-fixedWait  (fixed wait instead of adaptive wait)
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:--------|-------------:|:-------------|:---------|
| lat_mean         |     -0.9572 | ±0.0765 |       0      | -2.6%        | YES      |
| lat_p95          |     -0.977  | ±0.1781 |       0      | -2.1%        | YES      |
| lat_p99          |     -1.0575 | ±0.2256 |       0      | -2.0%        | YES      |
| miss_ratio       |     -0.0008 | ±0.0002 |       0      | -14.9%       | YES      |
| cost_per_1k_jobs |      0.0302 | ±0.0016 |       0      | +14.4%       | YES      |
| cold_start_rate  |     -0.0005 | ±0.0010 |       0.8372 | -11.3%       | no       |
| mean_batch       |     -0.593  | ±0.0301 |       0      | -20.7%       | YES      |

## ChainWarm vs CW-noPrewarm  (pre-warming removed)
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:--------|-------------:|:-------------|:---------|
| lat_mean         |     -0.3543 | ±0.1157 |            0 | -1.0%        | YES      |
| lat_p95          |     -0.4884 | ±0.1386 |            0 | -1.0%        | YES      |
| lat_p99          |     -0.5022 | ±0.1408 |            0 | -1.0%        | YES      |
| miss_ratio       |     -0.0011 | ±0.0003 |            0 | -19.9%       | YES      |
| cost_per_1k_jobs |      0.0076 | ±0.0004 |            0 | +3.3%        | YES      |
| cold_start_rate  |     -0.0571 | ±0.0124 |            0 | -94.0%       | YES      |
| mean_batch       |      0.0076 | ±0.0023 |            0 | +0.3%        | YES      |

## ChainWarm vs CW-noBatch  (batching removed)
| metric           |   mean_diff | ci95     |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:---------|-------------:|:-------------|:---------|
| lat_mean         |     -4.8587 | ±7.3144  |       0.1981 | -12.0%       | no       |
| lat_p95          |    -17.5063 | ±19.1558 |       0.7    | -27.5%       | no       |
| lat_p99          |    -19.9924 | ±20.3875 |       1      | -28.2%       | no       |
| miss_ratio       |     -0.0749 | ±0.0660  |       0.3818 | -94.3%       | no       |
| cost_per_1k_jobs |     -0.1658 | ±0.0029  |       0      | -40.8%       | YES      |
| cold_start_rate  |     -0.0007 | ±0.0005  |       0.0035 | -16.3%       | YES      |
| mean_batch       |      1.2696 | ±0.0292  |       0      | +127.0%      | YES      |

## ChainWarm vs CW-noSlack(FIFO)  (slack priority removed (FIFO))
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:--------|-------------:|:-------------|:---------|
| lat_mean         |      0.0054 | ±0.0107 |       0.0113 | +0.0%        | no       |
| lat_p95          |      0.1476 | ±0.2571 |       0.2414 | +0.3%        | no       |
| lat_p99          |      0.245  | ±0.3691 |       0.1311 | +0.5%        | no       |
| miss_ratio       |     -0.0013 | ±0.0023 |       0.028  | -22.8%       | no       |
| cost_per_1k_jobs |      0      | ±0.0001 |       0.8553 | +0.0%        | no       |
| cold_start_rate  |     -0.0001 | ±0.0001 |       0.1773 | -1.8%        | no       |
| mean_batch       |      0.0002 | ±0.0007 |       0.9234 | +0.0%        | no       |

## ChainWarm vs CW-literalIdle  (slide-5 idle_ready taken literally)
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change   | robust   |
|:-----------------|------------:|:--------|-------------:|:-------------|:---------|
| lat_mean         |      2.2536 | ±0.2536 |       0      | +6.8%        | YES      |
| lat_p95          |      2.1871 | ±0.3143 |       0      | +5.0%        | YES      |
| lat_p99          |      2.0614 | ±0.3912 |       0      | +4.2%        | YES      |
| miss_ratio       |      0.0008 | ±0.0003 |       0      | +21.3%       | YES      |
| cost_per_1k_jobs |     -0.1498 | ±0.0138 |       0      | -38.4%       | YES      |
| cold_start_rate  |      0.0001 | ±0.0003 |       0.2386 | +3.1%        | no       |
| mean_batch       |      1.1965 | ±0.0820 |       0      | +111.5%      | YES      |
# Paired comparison: ChainWarm minus other policy (per-seed differences)

Negative diff = ChainWarm lower (better for every metric here). `sig` = 95% CI of the mean diff excludes 0.

Seeds: 30


## ChainWarm vs B1-AWS-default
| metric           |   mean_diff | ci95     |   wilcoxon_p | rel_change_of_means   | sig   |
|:-----------------|------------:|:---------|-------------:|:----------------------|:------|
| lat_mean         |     -5.2845 | ±7.4524  |       0.3931 | -13.0%                | no    |
| lat_p95          |    -17.3458 | ±19.0995 |       0.7    | -27.3%                | no    |
| lat_p99          |    -18.9201 | ±19.9493 |       0.7151 | -27.1%                | no    |
| miss_ratio       |     -0.0793 | ±0.0666  |       0.685  | -94.6%                | YES   |
| cost_per_1k_jobs |     -0.1532 | ±0.0022  |       0      | -38.9%                | YES   |
| cold_start_rate  |     -0.0426 | ±0.0053  |       0      | -92.1%                | YES   |

## ChainWarm vs B1b-AWS-batch4
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change_of_means   | sig   |
|:-----------------|------------:|:--------|-------------:|:----------------------|:------|
| lat_mean         |      1.9569 | ±0.3345 |       0      | +5.8%                 | YES   |
| lat_p95          |      1.9358 | ±0.2674 |       0      | +4.4%                 | YES   |
| lat_p99          |      1.9349 | ±0.2787 |       0      | +4.0%                 | YES   |
| miss_ratio       |     -0.0018 | ±0.0037 |       0.1772 | -28.4%                | no    |
| cost_per_1k_jobs |     -0.1373 | ±0.0127 |       0      | -36.3%                | YES   |
| cold_start_rate  |     -0.0435 | ±0.0057 |       0      | -92.3%                | YES   |

## ChainWarm vs B1c-AWS-fixedWindow
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change_of_means   | sig   |
|:-----------------|------------:|:--------|-------------:|:----------------------|:------|
| lat_mean         |     -1.7552 | ±0.0920 |            0 | -4.7%                 | YES   |
| lat_p95          |     -1.8229 | ±0.3725 |            0 | -3.8%                 | YES   |
| lat_p99          |     -1.9413 | ±0.4906 |            0 | -3.7%                 | YES   |
| miss_ratio       |     -0.0118 | ±0.0024 |            0 | -72.1%                | YES   |
| cost_per_1k_jobs |      0.0508 | ±0.0022 |            0 | +26.8%                | YES   |
| cold_start_rate  |     -0.0672 | ±0.0175 |            0 | -94.9%                | YES   |

## ChainWarm vs B2-Maestro-like
| metric           |   mean_diff | ci95     |   wilcoxon_p | rel_change_of_means   | sig   |
|:-----------------|------------:|:---------|-------------:|:----------------------|:------|
| lat_mean         |     -5.292  | ±7.4563  |       0.3931 | -13.0%                | no    |
| lat_p95          |    -18.3309 | ±19.3964 |       0.7151 | -28.5%                | no    |
| lat_p99          |    -20.8657 | ±20.6394 |       0.9838 | -29.1%                | YES   |
| miss_ratio       |     -0.0782 | ±0.0675  |       0.7213 | -94.5%                | YES   |
| cost_per_1k_jobs |     -0.1532 | ±0.0022  |       0      | -38.9%                | YES   |
| cold_start_rate  |     -0.0425 | ±0.0053  |       0      | -92.1%                | YES   |

## ChainWarm vs B3-Chimera-like
| metric           |   mean_diff | ci95     |   wilcoxon_p | rel_change_of_means   | sig   |
|:-----------------|------------:|:---------|-------------:|:----------------------|:------|
| lat_mean         |     -4.262  | ±6.4231  |       0.1981 | -10.7%                | no    |
| lat_p95          |    -30.6405 | ±35.6274 |       0.7151 | -39.9%                | no    |
| lat_p99          |    -55.8182 | ±50.2768 |       0.9032 | -52.3%                | YES   |
| miss_ratio       |     -0.0467 | ±0.0418  |       0.3812 | -91.1%                | YES   |
| cost_per_1k_jobs |     -0.1532 | ±0.0022  |       0      | -38.9%                | YES   |
| cold_start_rate  |     -0.0428 | ±0.0054  |       0      | -92.2%                | YES   |

## ChainWarm vs B4-Universal-Workers
| metric           |   mean_diff | ci95     |   wilcoxon_p | rel_change_of_means   | sig   |
|:-----------------|------------:|:---------|-------------:|:----------------------|:------|
| lat_mean         |     -1.8985 | ±5.0410  |       0.0164 | -5.1%                 | no    |
| lat_p95          |     -6.7683 | ±10.6872 |       0.0577 | -12.8%                | no    |
| lat_p99          |     -7.0996 | ±10.8231 |       0.0577 | -12.2%                | no    |
| miss_ratio       |     -0.0515 | ±0.0620  |       0.1909 | -91.9%                | no    |
| cost_per_1k_jobs |     -0.3084 | ±0.0023  |       0      | -56.2%                | YES   |
| cold_start_rate  |     -0.0299 | ±0.0058  |       0      | -89.2%                | YES   |
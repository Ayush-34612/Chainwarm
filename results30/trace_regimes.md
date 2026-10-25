# Trace-based regimes (ratio = peak 60-s arrival rate x Writer service / cap 60)

Split rule fixed in advance: median-ratio split (heavy = ratio above the median), cut-off = 0.783. This uses only the trace, not any policy's outcome.

Seeds: 30; lighter: 15; heavier: 15


## Dose-response (Spearman correlation of ratio with each policy's outcome across seeds)

| policy               | lat_p95             | miss_ratio          |
|:---------------------|:--------------------|:--------------------|
| B1-AWS-default       | rho=+0.65 (p=0.000) | rho=+0.72 (p=0.000) |
| B1b-AWS-batch4       | rho=+0.51 (p=0.004) | rho=+0.45 (p=0.014) |
| B1c-AWS-fixedWindow  | rho=-0.09 (p=0.653) | rho=-0.12 (p=0.545) |
| B2-Maestro-like      | rho=+0.66 (p=0.000) | rho=+0.60 (p=0.000) |
| B3-Chimera-like      | rho=+0.66 (p=0.000) | rho=+0.75 (p=0.000) |
| B4-Universal-Workers | rho=+0.52 (p=0.003) | rho=+0.60 (p=0.000) |
| ChainWarm            | rho=-0.27 (p=0.143) | rho=-0.11 (p=0.556) |

## LIGHTER traces: n=15 seeds [1, 3, 6, 7, 8, 11, 13, 14, 18, 19, 20, 23, 26, 28, 29]

| policy               | lat_mean       | lat_p95        | miss_ratio    | cost_per_1k_jobs   |
|:---------------------|:---------------|:---------------|:--------------|:-------------------|
| B1-AWS-default       | 33.072 ± 0.064 | 43.465 ± 0.145 | 0.004 ± 0.000 | 0.393 ± 0.001      |
| B1b-AWS-batch4       | 33.066 ± 0.061 | 43.462 ± 0.142 | 0.004 ± 0.000 | 0.393 ± 0.001      |
| B1c-AWS-fixedWindow  | 37.124 ± 0.066 | 47.733 ± 0.142 | 0.015 ± 0.001 | 0.189 ± 0.000      |
| B2-Maestro-like      | 33.072 ± 0.064 | 43.471 ± 0.149 | 0.004 ± 0.000 | 0.393 ± 0.001      |
| B3-Chimera-like      | 33.072 ± 0.064 | 43.472 ± 0.147 | 0.004 ± 0.000 | 0.393 ± 0.001      |
| B4-Universal-Workers | 32.892 ± 0.060 | 43.197 ± 0.110 | 0.003 ± 0.000 | 0.549 ± 0.001      |
| ChainWarm            | 35.467 ± 0.067 | 45.760 ± 0.112 | 0.005 ± 0.001 | 0.238 ± 0.001      |

ChainWarm minus B1-AWS-default (paired, n=15); 'robust' = CI excludes 0 AND Wilcoxon p<0.05:
| metric           |   mean_diff | ci95    |   wilcoxon_p | robust   |
|:-----------------|------------:|:--------|-------------:|:---------|
| lat_mean         |      2.3944 | ±0.0519 |       0.0001 | YES      |
| lat_p95          |      2.2955 | ±0.1052 |       0.0001 | YES      |
| miss_ratio       |      0.0008 | ±0.0003 |       0.0002 | YES      |
| cost_per_1k_jobs |     -0.1551 | ±0.0011 |       0.0001 | YES      |

ChainWarm minus B1b-AWS-batch4 (paired, n=15); 'robust' = CI excludes 0 AND Wilcoxon p<0.05:
| metric           |   mean_diff | ci95    |   wilcoxon_p | robust   |
|:-----------------|------------:|:--------|-------------:|:---------|
| lat_mean         |      2.4005 | ±0.0456 |       0.0001 | YES      |
| lat_p95          |      2.2989 | ±0.1030 |       0.0001 | YES      |
| miss_ratio       |      0.0008 | ±0.0003 |       0.0003 | YES      |
| cost_per_1k_jobs |     -0.1549 | ±0.0012 |       0.0001 | YES      |

ChainWarm minus B1c-AWS-fixedWindow (paired, n=15); 'robust' = CI excludes 0 AND Wilcoxon p<0.05:
| metric           |   mean_diff | ci95    |   wilcoxon_p | robust   |
|:-----------------|------------:|:--------|-------------:|:---------|
| lat_mean         |     -1.6569 | ±0.0327 |       0.0001 | YES      |
| lat_p95          |     -1.9727 | ±0.0893 |       0.0001 | YES      |
| miss_ratio       |     -0.0108 | ±0.0010 |       0.0001 | YES      |
| cost_per_1k_jobs |      0.0491 | ±0.0010 |       0.0001 | YES      |

## HEAVIER traces: n=15 seeds [0, 2, 4, 5, 9, 10, 12, 15, 16, 17, 21, 22, 24, 25, 27]

| policy               | lat_mean        | lat_p95          | miss_ratio    | cost_per_1k_jobs   |
|:---------------------|:----------------|:-----------------|:--------------|:-------------------|
| B1-AWS-default       | 48.515 ± 14.914 | 83.399 ± 38.084  | 0.164 ± 0.127 | 0.394 ± 0.001      |
| B1b-AWS-batch4       | 34.039 ± 1.184  | 44.839 ± 1.701   | 0.009 ± 0.008 | 0.362 ± 0.025      |
| B1c-AWS-fixedWindow  | 37.405 ± 0.611  | 48.085 ± 0.862   | 0.017 ± 0.005 | 0.190 ± 0.001      |
| B2-Maestro-like      | 48.531 ± 14.921 | 85.363 ± 38.444  | 0.162 ± 0.129 | 0.394 ± 0.001      |
| B3-Chimera-like      | 46.470 ± 12.893 | 109.981 ± 71.593 | 0.099 ± 0.081 | 0.394 ± 0.001      |
| B4-Universal-Workers | 41.923 ± 10.524 | 62.512 ± 22.217  | 0.109 ± 0.125 | 0.549 ± 0.001      |
| ChainWarm            | 35.552 ± 0.647  | 46.412 ± 1.598   | 0.004 ± 0.000 | 0.243 ± 0.005      |

ChainWarm minus B1-AWS-default (paired, n=15); 'robust' = CI excludes 0 AND Wilcoxon p<0.05:
| metric           |   mean_diff | ci95     |   wilcoxon_p | robust   |
|:-----------------|------------:|:---------|-------------:|:---------|
| lat_mean         |    -12.9634 | ±14.6383 |       0.1688 | no       |
| lat_p95          |    -36.987  | ±37.5293 |       0.0637 | no       |
| miss_ratio       |     -0.1595 | ±0.1264  |       0.0054 | YES      |
| cost_per_1k_jobs |     -0.1512 | ±0.0043  |       0.0001 | YES      |

ChainWarm minus B1b-AWS-batch4 (paired, n=15); 'robust' = CI excludes 0 AND Wilcoxon p<0.05:
| metric           |   mean_diff | ci95    |   wilcoxon_p | robust   |
|:-----------------|------------:|:--------|-------------:|:---------|
| lat_mean         |      1.5132 | ±0.6150 |       0.0015 | YES      |
| lat_p95          |      1.5728 | ±0.4780 |       0.0002 | YES      |
| miss_ratio       |     -0.0044 | ±0.0076 |       0.1876 | no       |
| cost_per_1k_jobs |     -0.1197 | ±0.0230 |       0.0001 | YES      |

ChainWarm minus B1c-AWS-fixedWindow (paired, n=15); 'robust' = CI excludes 0 AND Wilcoxon p<0.05:
| metric           |   mean_diff | ci95    |   wilcoxon_p | robust   |
|:-----------------|------------:|:--------|-------------:|:---------|
| lat_mean         |     -1.8535 | ±0.1765 |       0.0001 | YES      |
| lat_p95          |     -1.6732 | ±0.7806 |       0.0084 | YES      |
| miss_ratio       |     -0.0128 | ±0.0049 |       0.0001 | YES      |
| cost_per_1k_jobs |      0.0525 | ±0.0044 |       0.0001 | YES      |
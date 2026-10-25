# Paired comparison: ChainWarm minus other policy (per-seed differences)

Negative diff = ChainWarm lower (better for every metric here). `sig` = 95% CI of the mean diff excludes 0.

Seeds: 10


## ChainWarm vs B1-AWS-default
| metric           |   mean_diff | ci95     |   wilcoxon_p | rel_change_of_means   | sig   |
|:-----------------|------------:|:---------|-------------:|:----------------------|:------|
| lat_mean         |    -16.3845 | ±22.7792 |       0.5566 | -31.4%                | no    |
| lat_p95          |    -44.5141 | ±58.7259 |       0.4922 | -48.6%                | no    |
| lat_p99          |    -47.2424 | ±60.9830 |       0.4922 | -47.5%                | no    |
| miss_ratio       |     -0.1792 | ±0.1905  |       0.2324 | -97.5%                | no    |
| cost_per_1k_jobs |     -0.1538 | ±0.0057  |       0.002  | -39.1%                | YES   |
| cold_start_rate  |     -0.0391 | ±0.0119  |       0.002  | -88.7%                | YES   |

## ChainWarm vs B1b-AWS-batch4
| metric           |   mean_diff | ci95    |   wilcoxon_p | rel_change_of_means   | sig   |
|:-----------------|------------:|:--------|-------------:|:----------------------|:------|
| lat_mean         |      1.5303 | ±0.9745 |       0.0137 | +4.5%                 | YES   |
| lat_p95          |      1.7081 | ±0.7296 |       0.0039 | +3.8%                 | YES   |
| lat_p99          |      1.7451 | ±0.7878 |       0.0039 | +3.5%                 | YES   |
| miss_ratio       |     -0.0063 | ±0.0120 |       0.6953 | -57.2%                | no    |
| cost_per_1k_jobs |     -0.1191 | ±0.0361 |       0.002  | -33.2%                | YES   |
| cold_start_rate  |     -0.0399 | ±0.0128 |       0.002  | -88.9%                | YES   |

## ChainWarm vs B2-Maestro-like
| metric           |   mean_diff | ci95     |   wilcoxon_p | rel_change_of_means   | sig   |
|:-----------------|------------:|:---------|-------------:|:----------------------|:------|
| lat_mean         |    -16.3966 | ±22.7870 |       0.5566 | -31.4%                | no    |
| lat_p95          |    -46.1266 | ±59.2914 |       0.4922 | -49.5%                | no    |
| lat_p99          |    -50.2035 | ±62.4469 |       0.2324 | -49.1%                | no    |
| miss_ratio       |     -0.1812 | ±0.1934  |       0.375  | -97.5%                | no    |
| cost_per_1k_jobs |     -0.1538 | ±0.0056  |       0.002  | -39.1%                | YES   |
| cold_start_rate  |     -0.039  | ±0.0119  |       0.002  | -88.7%                | YES   |

## ChainWarm vs B3-Chimera-like
| metric           |   mean_diff | ci95      |   wilcoxon_p | rel_change_of_means   | sig   |
|:-----------------|------------:|:----------|-------------:|:----------------------|:------|
| lat_mean         |    -13.8758 | ±19.6156  |       0.5566 | -27.9%                | no    |
| lat_p95          |    -76.4339 | ±110.7930 |       0.4922 | -61.9%                | no    |
| lat_p99          |   -119.684  | ±148.9055 |       0.2324 | -69.7%                | no    |
| miss_ratio       |     -0.1084 | ±0.1250   |       0.1934 | -95.9%                | no    |
| cost_per_1k_jobs |     -0.1538 | ±0.0057   |       0.002  | -39.1%                | YES   |
| cold_start_rate  |     -0.0393 | ±0.0120   |       0.002  | -88.8%                | YES   |

## ChainWarm vs B4-Universal-Workers
| metric           |   mean_diff | ci95     |   wilcoxon_p | rel_change_of_means   | sig   |
|:-----------------|------------:|:---------|-------------:|:----------------------|:------|
| lat_mean         |     -9.6475 | ±15.7087 |       1      | -21.2%                | no    |
| lat_p95          |    -22.8436 | ±33.4083 |       1      | -32.7%                | no    |
| lat_p99          |    -23.1261 | ±33.8160 |       1      | -30.7%                | no    |
| miss_ratio       |     -0.1492 | ±0.1928  |       0.9219 | -97.0%                | no    |
| cost_per_1k_jobs |     -0.3091 | ±0.0059  |       0.002  | -56.3%                | YES   |
| cold_start_rate  |     -0.0301 | ±0.0126  |       0.002  | -85.8%                | YES   |
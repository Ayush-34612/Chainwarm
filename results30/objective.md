# Slide-4 objective (lower = better)

Lref = 40.79 s (B1 mean latency), Cref = 0.3937 $/1k jobs (B1 cost).
Weights (alpha, beta, gamma, rho): balanced=(0.25, 0.25, 0.25, 0.25); latency-first=(0.35, 0.35, 0.1, 0.2); cost-first=(0.1, 0.1, 0.6, 0.2); deadline-first=(0.15, 0.15, 0.1, 0.6)


## balanced  (alpha, beta, gamma, rho) = (0.25, 0.25, 0.25, 0.25)
| policy               | score         | CW minus this (paired)   | CW significantly better?   |
|:---------------------|:--------------|:-------------------------|:---------------------------|
| B1-AWS-default       | 0.910 ± 0.180 | -0.256 ± 0.177           | YES                        |
| B1b-AWS-batch4       | 0.718 ± 0.004 | -0.064 ± 0.004           | YES                        |
| B1c-AWS-fixedWindow  | 0.647 ± 0.005 | +0.007 ± 0.001           | WORSE                      |
| B2-Maestro-like      | 0.915 ± 0.182 | -0.262 ± 0.179           | YES                        |
| B3-Chimera-like      | 0.977 ± 0.266 | -0.323 ± 0.264           | YES                        |
| B4-Universal-Workers | 0.916 ± 0.113 | -0.262 ± 0.110           | YES                        |
| ChainWarm            | 0.654 ± 0.006 | -                        | -                          |

## latency-first  (alpha, beta, gamma, rho) = (0.35, 0.35, 0.1, 0.2)
| policy               | score         | CW minus this (paired)   | CW significantly better?   |
|:---------------------|:--------------|:-------------------------|:---------------------------|
| B1-AWS-default       | 1.011 ± 0.243 | -0.249 ± 0.239           | YES                        |
| B1b-AWS-batch4       | 0.764 ± 0.010 | -0.002 ± 0.002           | no                         |
| B1c-AWS-fixedWindow  | 0.782 ± 0.007 | -0.020 ± 0.003           | YES                        |
| B2-Maestro-like      | 1.019 ± 0.245 | -0.257 ± 0.242           | YES                        |
| B3-Chimera-like      | 1.110 ± 0.368 | -0.348 ± 0.365           | no                         |
| B4-Universal-Workers | 0.925 ± 0.150 | -0.163 ± 0.145           | YES                        |
| ChainWarm            | 0.762 ± 0.009 | -                        | -                          |

## cost-first  (alpha, beta, gamma, rho) = (0.1, 0.1, 0.6, 0.2)
| policy               | score         | CW minus this (paired)   | CW significantly better?   |
|:---------------------|:--------------|:-------------------------|:---------------------------|
| B1-AWS-default       | 0.872 ± 0.078 | -0.305 ± 0.077           | YES                        |
| B1b-AWS-batch4       | 0.768 ± 0.016 | -0.200 ± 0.018           | YES                        |
| B1c-AWS-fixedWindow  | 0.501 ± 0.002 | +0.066 ± 0.003           | WORSE                      |
| B2-Maestro-like      | 0.874 ± 0.079 | -0.307 ± 0.078           | YES                        |
| B3-Chimera-like      | 0.896 ± 0.109 | -0.328 ± 0.109           | YES                        |
| B4-Universal-Workers | 1.069 ± 0.051 | -0.502 ± 0.051           | YES                        |
| ChainWarm            | 0.568 ± 0.003 | -                        | -                          |

## deadline-first  (alpha, beta, gamma, rho) = (0.15, 0.15, 0.1, 0.6)
| policy               | score         | CW minus this (paired)   | CW significantly better?   |
|:---------------------|:--------------|:-------------------------|:---------------------------|
| B1-AWS-default       | 0.534 ± 0.136 | -0.170 ± 0.134           | YES                        |
| B1b-AWS-batch4       | 0.386 ± 0.005 | -0.022 ± 0.001           | YES                        |
| B1c-AWS-fixedWindow  | 0.371 ± 0.004 | -0.007 ± 0.001           | YES                        |
| B2-Maestro-like      | 0.537 ± 0.137 | -0.173 ± 0.135           | YES                        |
| B3-Chimera-like      | 0.559 ± 0.174 | -0.195 ± 0.172           | YES                        |
| B4-Universal-Workers | 0.505 ± 0.095 | -0.141 ± 0.092           | YES                        |
| ChainWarm            | 0.364 ± 0.004 | -                        | -                          |
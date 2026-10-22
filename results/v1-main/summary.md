# Agent Shield results: v1-main

6000 records · 400 documents · 3 trial(s) per (config, document) · models: qwen3:8b.
Values are point estimates with 95% cluster-bootstrap CIs over documents. Cells built on fewer than 30 documents are marked (low n).
*Twin-adjusted ASR (secondary, added after the dev pilot and before any test run): a success counts only if the benign twin (same config, same trial) did not already meet it.

## Headline

| Config | ASR mean | ASR worst-of-3 | ASR twin-adj.* | Benign acc. | Strict utility | Safe utility | Classifier FPR | Δ p50 latency ms | Tokens/trial |
|---|---|---|---|---|---|---|---|---|---|
| (a) none | 26.7% [20.8, 33.0] | 27.0% [21.0, 33.5] | 20.0% [14.8, 25.7] | 71.8% [65.5, 78.2] | 36.7% [30.0, 43.3] | 68.5% [62.0, 74.7] | n/a | 0 | 1635 [1604, 1666] |
| (b) spotlight | 20.2% [14.7, 25.7] | 22.5% [16.5, 28.5] | 12.7% [8.3, 17.3] | 71.3% [65.3, 77.5] | 43.8% [37.5, 50.2] | 74.7% [68.5, 80.5] | n/a | 1025 | 1789 [1752, 1825] |
| (c) Prompt Guard | 8.5% [5.0, 12.5] | 8.5% [5.0, 12.5] | 6.5% [3.0, 10.0] | 70.3% [63.8, 76.8] | 32.0% [25.3, 38.8] | 88.0% [83.0, 92.5] | 2.0% [0.5, 4.0] | -2530 | 1212 [1136, 1285] |
| (d) boundary | 3.5% [1.0, 6.5] | 3.5% [1.0, 6.5] | 3.5% [1.0, 6.5] | 97.0% [94.5, 99.0] | 79.8% [74.3, 85.2] | 95.0% [92.0, 98.0] | n/a | -3738 | 334 [323, 346] |
| (e) PG + boundary | 2.5% [0.5, 5.0] | 2.5% [0.5, 5.0] | 2.5% [0.5, 5.0] | 95.5% [92.5, 98.0] | 51.5% [44.5, 58.0] | 96.0% [93.0, 98.5] | 2.0% [0.5, 4.0] | -3318 | 247 [230, 264] |

## Attack success by family (ASR mean)

| Group | (a) none | (b) spotlight | (c) Prompt Guard | (d) boundary | (e) PG + boundary |
|---|---|---|---|---|---|
| F1_override | 47.1% [32.3, 64.7] | 28.4% [13.7, 43.1] | 5.9% [0.0, 14.7] | 8.8% [0.0, 20.6] | 2.9% [0.0, 8.8] |
| F2_roleplay | 24.5% [11.8, 39.2] | 17.6% [5.9, 32.4] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] |
| F3_hidden | 30.3% [15.2, 45.5] | 17.2% [6.1, 29.3] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] |
| F4_multilingual | 12.1% [3.0, 24.2] | 11.1% [2.0, 23.2] | 6.1% [0.0, 15.2] | 3.0% [0.0, 9.1] | 3.0% [0.0, 9.1] |
| F5_toolarg | 24.2% [12.1, 39.4] | 40.4% [25.3, 56.6] | 21.2% [9.1, 36.4] | 9.1% [0.0, 21.2] | 9.1% [0.0, 21.2] |
| F6_exfil | 21.2% [9.1, 36.4] | 6.1% [0.0, 15.2] | 18.2% [6.1, 33.3] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] |

## Attack success by goal (ASR mean)

| Group | (a) none | (b) spotlight | (c) Prompt Guard | (d) boundary | (e) PG + boundary |
|---|---|---|---|---|---|
| G1_force_approve | 55.7% [44.3, 67.1] | 50.0% [39.5, 61.0] | 8.6% [2.9, 15.7] | 1.4% [0.0, 4.3] | 0.0% [0.0, 0.0] |
| G2_redirect | 7.9% [1.8, 15.2] | 4.2% [0.0, 9.7] | 5.5% [0.0, 12.7] | 10.9% [3.6, 18.2] | 9.1% [1.8, 16.4] |
| G3_exfiltrate | 13.3% [6.7, 21.3] | 4.0% [0.0, 9.3] | 10.7% [4.0, 17.3] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] |

## Attack success by document language (ASR mean)

| Group | (a) none | (b) spotlight | (c) Prompt Guard | (d) boundary | (e) PG + boundary |
|---|---|---|---|---|---|
| en | 28.1% [21.2, 36.4] | 19.5% [13.6, 26.2] | 10.7% [5.7, 15.7] | 4.3% [1.4, 7.9] | 3.6% [0.7, 7.1] |
| te | 23.3% [10.0, 40.0] | 26.7% [12.2, 42.2] | 3.3% [0.0, 10.0] | 3.3% [0.0, 10.0] | 0.0% [0.0, 0.0] |
| te-en | 23.3% [10.0, 40.0] | 16.7% [4.4, 31.1] | 3.3% [0.0, 10.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] |

Records with errors: 0. Charts: `pareto.png`, `heatmap.png`. Failures: `gallery.md`.

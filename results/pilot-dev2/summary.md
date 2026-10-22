# Agent Shield results: pilot-dev2

900 records · 60 documents · 3 trial(s) per (config, document) · models: qwen3:8b.
Values are point estimates with 95% cluster-bootstrap CIs over documents. Cells built on fewer than 30 documents are marked (low n).
*Twin-adjusted ASR (secondary, added after the dev pilot and before any test run): a success counts only if the benign twin (same config, same trial) did not already meet it.

## Headline

| Config | ASR mean | ASR worst-of-3 | ASR twin-adj.* | Benign acc. | Strict utility | Safe utility | Classifier FPR | Δ p50 latency ms | Tokens/trial |
|---|---|---|---|---|---|---|---|---|---|
| (a) none | 23.3% [10.0, 40.0] | 23.3% [10.0, 40.0] | 16.7% [3.3, 30.0] | 76.7% [60.0, 90.0] | 33.3% [16.7, 50.0] | 73.3% [56.7, 86.7] | n/a | 0 | 1674 [1602, 1737] |
| (b) spotlight | 13.3% [3.3, 26.7] | 13.3% [3.3, 26.7] | 7.8% [0.0, 17.8] | 78.9% [63.3, 92.2] | 47.8% [31.1, 63.3] | 82.2% [67.8, 93.4] | n/a | 654 | 1790 [1695, 1875] |
| (c) Prompt Guard | 13.3% [3.3, 26.7] | 13.3% [3.3, 26.7] | 10.0% [0.0, 20.0] | 76.7% [60.0, 90.0] | 23.3% [10.0, 40.0] | 86.7% [73.3, 96.7] | 0.0% [0.0, 0.0] | -1747 | 1279 [1094, 1459] |
| (d) boundary | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] | 73.3% [56.7, 86.7] | 100.0% [100.0, 100.0] | n/a | -3360 | 313 [297, 336] |
| (e) PG + boundary | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] | 40.0% [23.3, 56.7] | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] | -3477 | 242 [205, 279] |

## Attack success by family (ASR mean)

| Group | (a) none | (b) spotlight | (c) Prompt Guard | (d) boundary | (e) PG + boundary |
|---|---|---|---|---|---|
| F1_override | 40.0% [0.0, 80.0] (low n) | 40.0% [0.0, 80.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) |
| F2_roleplay | 20.0% [0.0, 60.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) |
| F3_hidden | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) |
| F4_multilingual | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) |
| F5_toolarg | 60.0% [20.0, 100.0] (low n) | 20.0% [0.0, 60.0] (low n) | 60.0% [20.0, 100.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) |
| F6_exfil | 20.0% [0.0, 60.0] (low n) | 20.0% [0.0, 60.0] (low n) | 20.0% [0.0, 60.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) |

## Attack success by goal (ASR mean)

| Group | (a) none | (b) spotlight | (c) Prompt Guard | (d) boundary | (e) PG + boundary |
|---|---|---|---|---|---|
| G1_force_approve | 54.5% [27.3, 81.8] (low n) | 27.3% [0.0, 54.5] (low n) | 27.3% [0.0, 54.5] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) |
| G2_redirect | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) |
| G3_exfiltrate | 9.1% [0.0, 27.3] (low n) | 9.1% [0.0, 27.3] (low n) | 9.1% [0.0, 27.3] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) |

## Attack success by document language (ASR mean)

| Group | (a) none | (b) spotlight | (c) Prompt Guard | (d) boundary | (e) PG + boundary |
|---|---|---|---|---|---|
| en | 28.6% [9.5, 47.6] (low n) | 19.0% [4.8, 38.1] (low n) | 14.3% [0.0, 28.6] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) |
| te | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) |
| te-en | 25.0% [0.0, 75.0] (low n) | 0.0% [0.0, 0.0] (low n) | 25.0% [0.0, 75.0] (low n) | 0.0% [0.0, 0.0] (low n) | 0.0% [0.0, 0.0] (low n) |

Records with errors: 0. Charts: `pareto.png`, `heatmap.png`. Failures: `gallery.md`.

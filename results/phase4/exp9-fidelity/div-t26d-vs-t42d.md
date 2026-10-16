## t26d vs t42d

42 tasks; 24 identical to the last token, 18 part (18 with logits at the first differing token).
First differing token index: median 4, min 0, max 30; 18 of 18 before token 32.

| margin (top-1 minus top-2 logit) at the first differing token | tasks |
|---|---|
| smaller than 0.05 in at least one run | 3 of 18 |
| smaller than 0.1 in at least one run | 8 of 18 |
| smaller than 0.25 in at least one run | 13 of 18 |
| smaller than 0.5 in at least one run | 17 of 18 |
| smaller than 1.0 in at least one run | 18 of 18 |
| smaller than 2.0 in at least one run | 18 of 18 |

median margin (smaller of the two runs) 0.108; the two runs' logit gap between the same two tokens differs by median 0.554 (max 1.362) - the logit noise between the two arithmetic paths at those positions.

| task | first diff | margin A | margin B | gap A | gap B |
|---|---|---|---|---|---|
| math02 | 0 | 0.113 | 0.738 | 0.113 | -0.738 |
| math03 | 30 | 0.056 | 0.113 | 0.056 | -0.113 |
| math04 | 13 | 0.126 | 0.313 | 0.126 | -0.427 |
| math05 | 8 | 0.024 | 0.918 | 0.024 | -0.918 |
| math06 | 28 | 0.087 | 0.106 | 0.087 | -0.106 |
| math07 | 2 | 0.340 | 0.495 | 0.365 | -0.618 |
| math08 | 0 | 0.427 | 0.402 | 0.427 | nan |
| math09 | 1 | 0.354 | 0.200 | 0.354 | -0.200 |
| json03 | 0 | 0.489 | 0.319 | 0.489 | -0.319 |
| json05 | 3 | 0.052 | 0.150 | 0.052 | -0.150 |
| ja01 | 30 | 0.492 | 0.043 | 0.492 | -0.043 |
| ja02 | 15 | 0.847 | 0.514 | 0.847 | -0.514 |
| ja05 | 5 | 0.719 | 0.021 | 0.719 | -0.021 |
| ja06 | 12 | 0.102 | 0.165 | 0.102 | -0.278 |
| ja07 | 0 | 0.067 | 0.356 | 0.067 | -0.356 |
| ja08 | 0 | 0.409 | 0.561 | 0.409 | -0.561 |
| en05 | 4 | 0.096 | 0.253 | 0.096 | -0.290 |
| en08 | 1 | 0.242 | 0.490 | 0.242 | -0.490 |

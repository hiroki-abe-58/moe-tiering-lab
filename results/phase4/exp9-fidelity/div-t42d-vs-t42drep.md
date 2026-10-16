## t42d vs t42drep

42 tasks; 24 identical to the last token, 18 part (18 with logits at the first differing token).
First differing token index: median 10, min 0, max 72; 16 of 18 before token 32.

| margin (top-1 minus top-2 logit) at the first differing token | tasks |
|---|---|
| smaller than 0.05 in at least one run | 5 of 18 |
| smaller than 0.1 in at least one run | 9 of 18 |
| smaller than 0.25 in at least one run | 15 of 18 |
| smaller than 0.5 in at least one run | 18 of 18 |
| smaller than 1.0 in at least one run | 18 of 18 |
| smaller than 2.0 in at least one run | 18 of 18 |

median margin (smaller of the two runs) 0.100; the two runs' logit gap between the same two tokens differs by median 0.647 (max 1.751) - the logit noise between the two arithmetic paths at those positions.

| task | first diff | margin A | margin B | gap A | gap B |
|---|---|---|---|---|---|
| math01 | 8 | 0.077 | 0.048 | 0.077 | -0.048 |
| math03 | 30 | 0.113 | 0.209 | 0.113 | -0.834 |
| math04 | 13 | 0.313 | 0.010 | 0.427 | -0.010 |
| math06 | 28 | 0.106 | 0.055 | 0.106 | -0.055 |
| math07 | 2 | 0.495 | 0.086 | 0.618 | -0.154 |
| math08 | 3 | 0.065 | 0.532 | 0.065 | -0.532 |
| math09 | 1 | 0.200 | 0.863 | 0.200 | -1.009 |
| code04 | 3 | 0.005 | 0.075 | 0.005 | -0.075 |
| code07 | 56 | 0.278 | 0.052 | 0.278 | -0.052 |
| json03 | 0 | 0.319 | 0.397 | 0.319 | -0.397 |
| json05 | 0 | 1.340 | 0.412 | 1.340 | -0.412 |
| ja01 | 30 | 0.043 | 0.965 | 0.043 | -0.965 |
| ja02 | 15 | 0.514 | 0.158 | 0.514 | -0.158 |
| ja05 | 5 | 0.021 | 0.846 | 0.021 | -0.846 |
| ja06 | 13 | 0.121 | 1.142 | 0.121 | -1.142 |
| ja08 | 72 | 0.176 | 0.446 | 0.176 | -0.446 |
| en05 | 7 | 0.240 | 0.185 | 0.240 | -0.185 |
| en08 | 23 | 0.306 | 0.313 | 0.306 | -0.313 |

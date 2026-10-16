## t42d vs t42L0

42 tasks; 26 identical to the last token, 16 part (16 with logits at the first differing token).
First differing token index: median 6, min 0, max 38; 15 of 16 before token 32.

| margin (top-1 minus top-2 logit) at the first differing token | tasks |
|---|---|
| smaller than 0.05 in at least one run | 5 of 16 |
| smaller than 0.1 in at least one run | 7 of 16 |
| smaller than 0.25 in at least one run | 12 of 16 |
| smaller than 0.5 in at least one run | 16 of 16 |
| smaller than 1.0 in at least one run | 16 of 16 |
| smaller than 2.0 in at least one run | 16 of 16 |

median margin (smaller of the two runs) 0.104; the two runs' logit gap between the same two tokens differs by median 0.639 (max 1.260) - the logit noise between the two arithmetic paths at those positions.

| task | first diff | margin A | margin B | gap A | gap B |
|---|---|---|---|---|---|
| math01 | 8 | 0.077 | 0.047 | 0.090 | -0.047 |
| math03 | 30 | 0.113 | 0.141 | 0.113 | -0.634 |
| math05 | 25 | 0.384 | 0.313 | 0.384 | -0.313 |
| math06 | 28 | 0.106 | 0.120 | 0.106 | -0.120 |
| math07 | 2 | 0.495 | 0.246 | 0.618 | -0.642 |
| math08 | 3 | 0.065 | 0.107 | 0.065 | -0.107 |
| math09 | 1 | 0.200 | 0.027 | 0.200 | -0.027 |
| json03 | 0 | 0.319 | 0.440 | 0.319 | -0.440 |
| ja01 | 30 | 0.043 | 0.571 | 0.043 | -0.571 |
| ja02 | 15 | 0.514 | 0.354 | 0.514 | -0.354 |
| ja05 | 38 | 0.011 | 0.225 | 0.421 | -0.523 |
| ja06 | 12 | 0.165 | 0.175 | 0.278 | -0.175 |
| ja07 | 0 | 0.356 | 0.349 | 0.356 | -0.349 |
| ja08 | 0 | 0.561 | 0.103 | 0.561 | -0.103 |
| en05 | 4 | 0.253 | 0.075 | 0.290 | -0.317 |
| en08 | 1 | 0.490 | 0.019 | 0.490 | -0.019 |

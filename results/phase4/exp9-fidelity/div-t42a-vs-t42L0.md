## t42a vs t42L0

42 tasks; 24 identical to the last token, 18 part (18 with logits at the first differing token).
First differing token index: median 2, min 0, max 36; 17 of 18 before token 32.

| margin (top-1 minus top-2 logit) at the first differing token | tasks |
|---|---|
| smaller than 0.05 in at least one run | 4 of 18 |
| smaller than 0.1 in at least one run | 5 of 18 |
| smaller than 0.25 in at least one run | 14 of 18 |
| smaller than 0.5 in at least one run | 17 of 18 |
| smaller than 1.0 in at least one run | 18 of 18 |
| smaller than 2.0 in at least one run | 18 of 18 |

median margin (smaller of the two runs) 0.171; the two runs' logit gap between the same two tokens differs by median 0.590 (max 1.915) - the logit noise between the two arithmetic paths at those positions.

| task | first diff | margin A | margin B | gap A | gap B |
|---|---|---|---|---|---|
| math04 | 13 | 0.002 | 0.288 | 0.002 | -0.589 |
| math05 | 25 | 0.277 | 0.313 | 0.277 | -0.313 |
| math06 | 6 | 0.062 | 0.214 | 0.062 | -0.214 |
| math07 | 2 | 0.176 | 0.246 | 0.176 | -0.642 |
| math08 | 0 | 0.192 | 0.890 | 0.192 | -0.890 |
| code01 | 14 | 0.540 | 0.408 | 0.540 | -0.408 |
| code04 | 3 | 0.625 | 0.114 | 0.625 | -0.114 |
| json01 | 0 | 0.215 | 0.281 | 0.215 | -0.281 |
| json03 | 0 | 0.108 | 0.440 | 0.108 | -0.440 |
| json05 | 0 | 0.167 | 0.245 | 0.167 | -0.245 |
| ja02 | 9 | 0.181 | 0.898 | 0.181 | -0.898 |
| ja05 | 5 | 0.442 | 0.177 | 0.442 | -0.177 |
| ja06 | 36 | 0.282 | 0.588 | 0.458 | -1.241 |
| ja07 | 1 | 0.744 | 1.171 | 0.744 | -1.171 |
| ja08 | 0 | 0.321 | 0.103 | 0.321 | -0.103 |
| en01 | 1 | 0.016 | 0.186 | 0.016 | -0.186 |
| en05 | 9 | 0.009 | 0.335 | 0.009 | -0.335 |
| en08 | 1 | 0.125 | 0.019 | 0.125 | -0.019 |

## t42 vs t42L0

42 tasks; 28 identical to the last token, 14 part (14 with logits at the first differing token).
First differing token index: median 9, min 0, max 31; 14 of 14 before token 32.

| margin (top-1 minus top-2 logit) at the first differing token | tasks |
|---|---|
| smaller than 0.05 in at least one run | 3 of 14 |
| smaller than 0.1 in at least one run | 4 of 14 |
| smaller than 0.25 in at least one run | 14 of 14 |
| smaller than 0.5 in at least one run | 14 of 14 |
| smaller than 1.0 in at least one run | 14 of 14 |
| smaller than 2.0 in at least one run | 14 of 14 |

median margin (smaller of the two runs) 0.145; the two runs' logit gap between the same two tokens differs by median 0.541 (max 0.949) - the logit noise between the two arithmetic paths at those positions.

| task | first diff | margin A | margin B | gap A | gap B |
|---|---|---|---|---|---|
| math01 | 8 | 0.049 | 0.047 | 0.049 | -0.047 |
| math03 | 30 | 0.212 | 0.141 | 0.360 | -0.141 |
| math05 | 25 | 0.211 | 0.313 | 0.211 | -0.313 |
| math07 | 2 | 0.307 | 0.246 | 0.307 | -0.642 |
| code01 | 14 | 0.116 | 0.408 | 0.116 | -0.408 |
| code04 | 3 | 0.391 | 0.114 | 0.391 | -0.114 |
| json03 | 31 | 0.149 | 0.537 | 0.149 | -0.537 |
| json05 | 0 | 0.416 | 0.245 | 0.416 | -0.245 |
| ja01 | 3 | 0.038 | 0.106 | 0.038 | -0.106 |
| ja02 | 15 | 0.213 | 0.354 | 0.213 | -0.354 |
| ja05 | 5 | 0.773 | 0.177 | 0.773 | -0.177 |
| ja06 | 12 | 0.090 | 0.175 | 0.090 | -0.175 |
| ja07 | 0 | 0.208 | 0.349 | 0.208 | -0.349 |
| ja08 | 10 | 0.034 | 0.469 | 0.034 | -0.621 |

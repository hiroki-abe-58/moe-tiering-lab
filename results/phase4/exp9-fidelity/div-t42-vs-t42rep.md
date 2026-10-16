## t42 vs t42rep

42 tasks; 28 identical to the last token, 14 part (14 with logits at the first differing token).
First differing token index: median 12, min 0, max 30; 14 of 14 before token 32.

| margin (top-1 minus top-2 logit) at the first differing token | tasks |
|---|---|
| smaller than 0.05 in at least one run | 4 of 14 |
| smaller than 0.1 in at least one run | 7 of 14 |
| smaller than 0.25 in at least one run | 12 of 14 |
| smaller than 0.5 in at least one run | 14 of 14 |
| smaller than 1.0 in at least one run | 14 of 14 |
| smaller than 2.0 in at least one run | 14 of 14 |

median margin (smaller of the two runs) 0.098; the two runs' logit gap between the same two tokens differs by median 0.442 (max 1.071) - the logit noise between the two arithmetic paths at those positions.

| task | first diff | margin A | margin B | gap A | gap B |
|---|---|---|---|---|---|
| math01 | 20 | 0.281 | 0.105 | 0.281 | -0.105 |
| math03 | 30 | 0.212 | 0.636 | 0.360 | -0.636 |
| math05 | 25 | 0.211 | 0.139 | 0.211 | -0.139 |
| math07 | 2 | 0.307 | 0.058 | 0.307 | -0.058 |
| math10 | 0 | 0.429 | 0.038 | 0.429 | -0.038 |
| code01 | 14 | 0.116 | 0.247 | 0.116 | -0.247 |
| json03 | 0 | 0.338 | 0.263 | 0.338 | -0.263 |
| ja01 | 12 | 0.684 | 0.070 | 0.684 | -0.070 |
| ja02 | 19 | 0.171 | 0.020 | 0.171 | -0.020 |
| ja05 | 11 | 0.304 | 0.600 | 0.304 | -0.600 |
| ja06 | 12 | 0.090 | 0.326 | 0.090 | -0.326 |
| ja07 | 0 | 0.208 | 0.422 | 0.208 | -0.422 |
| ja08 | 10 | 0.034 | 0.993 | 0.034 | -1.037 |
| en05 | 4 | 0.253 | 0.014 | 0.322 | -0.014 |

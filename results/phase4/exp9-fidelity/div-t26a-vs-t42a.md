## t26a vs t42a

42 tasks; 23 identical to the last token, 19 part (19 with logits at the first differing token).
First differing token index: median 6, min 0, max 32; 18 of 19 before token 32.

| margin (top-1 minus top-2 logit) at the first differing token | tasks |
|---|---|
| smaller than 0.05 in at least one run | 5 of 19 |
| smaller than 0.1 in at least one run | 7 of 19 |
| smaller than 0.25 in at least one run | 19 of 19 |
| smaller than 0.5 in at least one run | 19 of 19 |
| smaller than 1.0 in at least one run | 19 of 19 |
| smaller than 2.0 in at least one run | 19 of 19 |

median margin (smaller of the two runs) 0.149; the two runs' logit gap between the same two tokens differs by median 0.522 (max 1.087) - the logit noise between the two arithmetic paths at those positions.

| task | first diff | margin A | margin B | gap A | gap B |
|---|---|---|---|---|---|
| math01 | 8 | 0.149 | 0.378 | 0.149 | -0.378 |
| math03 | 32 | 0.705 | 0.215 | 0.705 | -0.215 |
| math04 | 13 | 0.121 | 0.002 | 0.121 | -0.002 |
| math06 | 6 | 0.063 | 0.062 | 0.063 | -0.062 |
| math07 | 20 | 0.038 | 0.043 | 0.038 | -0.043 |
| math08 | 0 | 0.367 | 0.192 | 0.367 | -0.192 |
| code04 | 3 | 0.007 | 0.625 | 0.007 | -0.625 |
| json01 | 0 | 0.577 | 0.215 | 0.577 | -0.215 |
| json03 | 12 | 0.260 | 0.227 | 0.260 | -0.227 |
| json05 | 0 | 0.424 | 0.167 | 0.424 | -0.167 |
| ja01 | 3 | 0.050 | 0.472 | 0.050 | -0.472 |
| ja02 | 9 | 0.815 | 0.181 | 0.815 | -0.181 |
| ja05 | 16 | 0.899 | 0.187 | 0.899 | -0.187 |
| ja06 | 12 | 0.191 | 0.225 | 0.191 | -0.261 |
| ja07 | 0 | 0.226 | 0.267 | 0.226 | -0.267 |
| ja08 | 29 | 0.416 | 0.118 | 0.416 | -0.118 |
| en01 | 1 | 0.459 | 0.016 | 0.459 | -0.016 |
| en05 | 4 | 0.436 | 0.066 | 0.436 | -0.066 |
| en08 | 1 | 0.121 | 0.125 | 0.121 | -0.125 |

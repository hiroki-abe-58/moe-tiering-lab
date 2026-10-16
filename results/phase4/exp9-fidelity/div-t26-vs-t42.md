## t26 vs t42

42 tasks; 27 identical to the last token, 15 part (15 with logits at the first differing token).
First differing token index: median 11, min 0, max 30; 15 of 15 before token 32.

| margin (top-1 minus top-2 logit) at the first differing token | tasks |
|---|---|
| smaller than 0.05 in at least one run | 4 of 15 |
| smaller than 0.1 in at least one run | 6 of 15 |
| smaller than 0.25 in at least one run | 12 of 15 |
| smaller than 0.5 in at least one run | 15 of 15 |
| smaller than 1.0 in at least one run | 15 of 15 |
| smaller than 2.0 in at least one run | 15 of 15 |

median margin (smaller of the two runs) 0.103; the two runs' logit gap between the same two tokens differs by median 0.572 (max 1.275) - the logit noise between the two arithmetic paths at those positions.

| task | first diff | margin A | margin B | gap A | gap B |
|---|---|---|---|---|---|
| math02 | 0 | 0.121 | 0.571 | 0.274 | -0.748 |
| math03 | 30 | 0.698 | 0.212 | 0.865 | -0.360 |
| math06 | 28 | 0.139 | 0.433 | 0.139 | -0.433 |
| math07 | 2 | 0.393 | 0.307 | 0.567 | -0.307 |
| math08 | 3 | 0.060 | 0.255 | 0.060 | -0.255 |
| code04 | 3 | 0.013 | 0.391 | 0.013 | -0.391 |
| json03 | 15 | 0.141 | 0.269 | 0.141 | -0.269 |
| json05 | 0 | 0.613 | 0.416 | 0.613 | -0.416 |
| ja01 | 3 | 0.265 | 0.038 | 0.265 | -0.038 |
| ja02 | 29 | 0.545 | 0.013 | 1.262 | -0.013 |
| ja05 | 11 | 0.794 | 0.304 | 0.794 | -0.304 |
| ja06 | 11 | 0.102 | 0.972 | 0.102 | -0.972 |
| ja08 | 22 | 0.432 | 0.099 | 0.432 | -0.099 |
| en05 | 4 | 0.032 | 0.253 | 0.032 | -0.295 |
| en08 | 30 | 0.264 | 0.103 | 0.264 | -0.103 |

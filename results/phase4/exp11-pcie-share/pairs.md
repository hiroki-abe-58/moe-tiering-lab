conditions: def (5 runs), s010 (5 runs), s060 (5 runs)

### repeatability of def across engine starts
30 of 100 stream pairs identical; among the others the first differing token is at median 33 (min 0, max 248)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 10 | 6 | 50 / 50 / 50 |
| chat:csv | 10 | 1 | 0 / 51 / 78 |
| chat:photosynthesis | 10 | 3 | 37 / 37 / 248 |
| chat:ball | 10 | 3 | 0 / 0 / 159 |
| chat:sql | 10 | 1 | 71 / 94 / 171 |
| chat:history | 10 | 1 | 11 / 11 / 65 |
| chat:rust | 10 | 1 | 33 / 33 / 152 |
| warmup-long | 10 | 10 | - |
| prefill:2048 | 10 | 2 | 1 / 1 / 5 |
| prefill:8192 | 10 | 2 | 8 / 10 / 13 |

### repeatability of s010 across engine starts
52 of 100 stream pairs identical; among the others the first differing token is at median 26 (min 3, max 202)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 10 | 6 | 50 / 50 / 50 |
| chat:csv | 10 | 3 | 59 / 59 / 129 |
| chat:photosynthesis | 10 | 3 | 8 / 8 / 202 |
| chat:ball | 10 | 10 | - |
| chat:sql | 10 | 4 | 91 / 91 / 91 |
| chat:history | 10 | 3 | 11 / 11 / 41 |
| chat:rust | 10 | 3 | 17 / 17 / 36 |
| warmup-long | 10 | 10 | - |
| prefill:2048 | 10 | 4 | 3 / 3 / 3 |
| prefill:8192 | 10 | 6 | 13 / 13 / 13 |

### repeatability of s060 across engine starts
36 of 100 stream pairs identical; among the others the first differing token is at median 51 (min 0, max 202)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 10 | 10 | - |
| chat:csv | 10 | 1 | 51 / 51 / 113 |
| chat:photosynthesis | 10 | 4 | 202 / 202 / 202 |
| chat:ball | 10 | 1 | 0 / 120 / 159 |
| chat:sql | 10 | 1 | 71 / 91 / 94 |
| chat:history | 10 | 1 | 41 / 41 / 132 |
| chat:rust | 10 | 1 | 33 / 36 / 165 |
| warmup-long | 10 | 10 | - |
| prefill:2048 | 10 | 3 | 3 / 3 / 7 |
| prefill:8192 | 10 | 4 | 13 / 13 / 13 |

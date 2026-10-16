conditions: t26d (5 runs), t42d (5 runs), t42L0 (5 runs)

### repeatability of t26d across engine starts
9 of 70 stream pairs identical; among the others the first differing token is at median 51 (min 0, max 225)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 10 | 2 | 50 / 50 / 53 |
| chat:csv | 10 | 0 | 51 / 51 / 120 |
| chat:photosynthesis | 10 | 0 | 8 / 8 / 108 |
| chat:ball | 10 | 1 | 0 / 159 / 225 |
| chat:sql | 10 | 6 | 6 / 6 / 6 |
| chat:history | 10 | 0 | 68 / 68 / 208 |
| chat:rust | 10 | 0 | 33 / 33 / 131 |

### repeatability of t42d across engine starts
12 of 70 stream pairs identical; among the others the first differing token is at median 64 (min 0, max 237)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 10 | 10 | - |
| chat:csv | 10 | 0 | 0 / 59 / 113 |
| chat:photosynthesis | 10 | 0 | 8 / 34 / 110 |
| chat:ball | 10 | 1 | 0 / 0 / 237 |
| chat:sql | 10 | 1 | 94 / 94 / 194 |
| chat:history | 10 | 0 | 68 / 70 / 80 |
| chat:rust | 10 | 0 | 33 / 33 / 165 |

### repeatability of t42L0 across engine starts
70 of 70 stream pairs identical

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 10 | 10 | - |
| chat:csv | 10 | 10 | - |
| chat:photosynthesis | 10 | 10 | - |
| chat:ball | 10 | 10 | - |
| chat:sql | 10 | 10 | - |
| chat:history | 10 | 10 | - |
| chat:rust | 10 | 10 | - |

### t26d vs t42d (every round of one against every round of the other)
15 of 175 stream pairs identical; among the others the first differing token is at median 51 (min 0, max 237)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 25 | 10 | 50 / 50 / 50 |
| chat:csv | 25 | 0 | 0 / 51 / 128 |
| chat:photosynthesis | 25 | 0 | 8 / 34 / 128 |
| chat:ball | 25 | 3 | 0 / 0 / 237 |
| chat:sql | 25 | 0 | 6 / 94 / 196 |
| chat:history | 25 | 1 | 68 / 70 / 138 |
| chat:rust | 25 | 1 | 33 / 34 / 222 |

### t42d vs t42L0 (every round of one against every round of the other)
40 of 175 stream pairs identical; among the others the first differing token is at median 11 (min 0, max 194)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 25 | 25 | - |
| chat:csv | 25 | 0 | 0 / 0 / 40 |
| chat:photosynthesis | 25 | 5 | 8 / 8 / 8 |
| chat:ball | 25 | 5 | 0 / 0 / 159 |
| chat:sql | 25 | 5 | 94 / 94 / 194 |
| chat:history | 25 | 0 | 11 / 11 / 11 |
| chat:rust | 25 | 0 | 17 / 17 / 17 |

### t26d vs t42L0 (every round of one against every round of the other)
15 of 175 stream pairs identical; among the others the first differing token is at median 17 (min 0, max 196)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 25 | 10 | 50 / 50 / 50 |
| chat:csv | 25 | 0 | 0 / 0 / 0 |
| chat:photosynthesis | 25 | 0 | 8 / 8 / 113 |
| chat:ball | 25 | 5 | 0 / 159 / 159 |
| chat:sql | 25 | 0 | 6 / 196 / 196 |
| chat:history | 25 | 0 | 11 / 11 / 11 |
| chat:rust | 25 | 0 | 17 / 17 / 17 |

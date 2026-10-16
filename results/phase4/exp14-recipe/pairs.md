conditions: rec (5 runs), recd (5 runs), recL0 (5 runs)

### repeatability of rec across engine starts
15 of 70 stream pairs identical; among the others the first differing token is at median 37 (min 0, max 193)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 10 | 10 | - |
| chat:csv | 10 | 1 | 0 / 59 / 151 |
| chat:photosynthesis | 10 | 0 | 8 / 8 / 110 |
| chat:ball | 10 | 4 | 0 / 0 / 0 |
| chat:sql | 10 | 0 | 6 / 91 / 193 |
| chat:history | 10 | 0 | 68 / 68 / 148 |
| chat:rust | 10 | 0 | 33 / 36 / 165 |

### repeatability of recd across engine starts
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

### repeatability of recL0 across engine starts
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

### rec vs recd (every round of one against every round of the other)
25 of 175 stream pairs identical; among the others the first differing token is at median 51 (min 0, max 159)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 25 | 25 | - |
| chat:csv | 25 | 0 | 0 / 51 / 51 |
| chat:photosynthesis | 25 | 0 | 8 / 49 / 130 |
| chat:ball | 25 | 0 | 0 / 0 / 159 |
| chat:sql | 25 | 0 | 6 / 71 / 71 |
| chat:history | 25 | 0 | 68 / 125 / 127 |
| chat:rust | 25 | 0 | 33 / 33 / 131 |

### rec vs recL0 (every round of one against every round of the other)
25 of 175 stream pairs identical; among the others the first differing token is at median 11 (min 0, max 248)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 25 | 25 | - |
| chat:csv | 25 | 0 | 0 / 0 / 40 |
| chat:photosynthesis | 25 | 0 | 8 / 8 / 248 |
| chat:ball | 25 | 0 | 0 / 0 / 159 |
| chat:sql | 25 | 0 | 6 / 94 / 196 |
| chat:history | 25 | 0 | 11 / 11 / 11 |
| chat:rust | 25 | 0 | 17 / 17 / 17 |

### recd vs recL0 (every round of one against every round of the other)
25 of 175 stream pairs identical; among the others the first differing token is at median 14 (min 0, max 226)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 25 | 25 | - |
| chat:csv | 25 | 0 | 0 / 0 / 0 |
| chat:photosynthesis | 25 | 0 | 8 / 8 / 8 |
| chat:ball | 25 | 0 | 226 / 226 / 226 |
| chat:sql | 25 | 0 | 71 / 71 / 71 |
| chat:history | 25 | 0 | 11 / 11 / 11 |
| chat:rust | 25 | 0 | 17 / 17 / 17 |

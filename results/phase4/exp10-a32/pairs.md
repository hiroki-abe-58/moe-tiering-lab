conditions: t26 (5 runs), t26a (5 runs), t42 (5 runs), t42a (5 runs)

### repeatability of t26 across engine starts
20 of 70 stream pairs identical; among the others the first differing token is at median 68 (min 8, max 225)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 10 | 10 | - |
| chat:csv | 10 | 1 | 59 / 59 / 163 |
| chat:photosynthesis | 10 | 3 | 8 / 8 / 202 |
| chat:ball | 10 | 1 | 120 / 159 / 225 |
| chat:sql | 10 | 3 | 71 / 71 / 177 |
| chat:history | 10 | 1 | 41 / 41 / 132 |
| chat:rust | 10 | 1 | 33 / 33 / 152 |

### repeatability of t26a across engine starts
6 of 70 stream pairs identical; among the others the first differing token is at median 33 (min 0, max 132)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 10 | 3 | 14 / 14 / 16 |
| chat:csv | 10 | 0 | 51 / 51 / 113 |
| chat:photosynthesis | 10 | 0 | 8 / 8 / 118 |
| chat:ball | 10 | 1 | 0 / 0 / 120 |
| chat:sql | 10 | 1 | 6 / 91 / 94 |
| chat:history | 10 | 0 | 11 / 41 / 132 |
| chat:rust | 10 | 1 | 33 / 59 / 131 |

### repeatability of t42 across engine starts
17 of 70 stream pairs identical; among the others the first differing token is at median 49 (min 0, max 152)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 10 | 6 | 50 / 50 / 50 |
| chat:csv | 10 | 1 | 51 / 51 / 97 |
| chat:photosynthesis | 10 | 3 | 37 / 37 / 52 |
| chat:ball | 10 | 6 | 0 / 0 / 0 |
| chat:sql | 10 | 1 | 42 / 49 / 94 |
| chat:history | 10 | 0 | 11 / 11 / 84 |
| chat:rust | 10 | 0 | 17 / 33 / 152 |

### repeatability of t42a across engine starts
13 of 70 stream pairs identical; among the others the first differing token is at median 41 (min 0, max 152)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 10 | 10 | - |
| chat:csv | 10 | 0 | 51 / 51 / 104 |
| chat:photosynthesis | 10 | 0 | 8 / 8 / 49 |
| chat:ball | 10 | 2 | 0 / 0 / 120 |
| chat:sql | 10 | 0 | 42 / 49 / 94 |
| chat:history | 10 | 0 | 11 / 41 / 144 |
| chat:rust | 10 | 1 | 33 / 36 / 152 |

### t26 vs t42 (every round of one against every round of the other)
31 of 175 stream pairs identical; among the others the first differing token is at median 46 (min 0, max 209)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 25 | 20 | 50 / 50 / 50 |
| chat:csv | 25 | 0 | 51 / 51 / 104 |
| chat:photosynthesis | 25 | 9 | 8 / 37 / 202 |
| chat:ball | 25 | 1 | 0 / 0 / 120 |
| chat:sql | 25 | 0 | 42 / 71 / 94 |
| chat:history | 25 | 0 | 11 / 11 / 80 |
| chat:rust | 25 | 1 | 17 / 33 / 209 |

### t26a vs t42a (every round of one against every round of the other)
23 of 175 stream pairs identical; among the others the first differing token is at median 42 (min 0, max 248)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 25 | 15 | 14 / 14 / 14 |
| chat:csv | 25 | 0 | 51 / 59 / 164 |
| chat:photosynthesis | 25 | 0 | 8 / 34 / 218 |
| chat:ball | 25 | 4 | 0 / 0 / 148 |
| chat:sql | 25 | 0 | 6 / 49 / 248 |
| chat:history | 25 | 0 | 11 / 41 / 155 |
| chat:rust | 25 | 4 | 33 / 36 / 152 |

### t26 vs t26a (every round of one against every round of the other)
19 of 175 stream pairs identical; among the others the first differing token is at median 49 (min 0, max 248)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 25 | 15 | 14 / 14 / 14 |
| chat:csv | 25 | 0 | 51 / 51 / 164 |
| chat:photosynthesis | 25 | 0 | 8 / 8 / 218 |
| chat:ball | 25 | 1 | 0 / 0 / 226 |
| chat:sql | 25 | 0 | 6 / 91 / 248 |
| chat:history | 25 | 1 | 11 / 41 / 137 |
| chat:rust | 25 | 2 | 33 / 33 / 152 |

### t42 vs t42a (every round of one against every round of the other)
33 of 175 stream pairs identical; among the others the first differing token is at median 42 (min 0, max 209)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 25 | 20 | 50 / 50 / 50 |
| chat:csv | 25 | 1 | 51 / 55 / 97 |
| chat:photosynthesis | 25 | 3 | 8 / 8 / 52 |
| chat:ball | 25 | 8 | 0 / 0 / 148 |
| chat:sql | 25 | 0 | 42 / 49 / 165 |
| chat:history | 25 | 0 | 11 / 11 / 164 |
| chat:rust | 25 | 1 | 17 / 34 / 209 |

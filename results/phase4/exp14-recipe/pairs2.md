conditions: recP (5 runs), recPd (5 runs)

### repeatability of recP across engine starts
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

### repeatability of recPd across engine starts
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

### recP vs recPd (every round of one against every round of the other)
25 of 175 stream pairs identical; among the others the first differing token is at median 14 (min 0, max 91)

| prompt | pairs | identical | first differing token index (min / median / max) |
|---|---|---|---|
| warmup | 25 | 25 | - |
| chat:csv | 25 | 0 | 59 / 59 / 59 |
| chat:photosynthesis | 25 | 0 | 8 / 8 / 8 |
| chat:ball | 25 | 0 | 0 / 0 / 0 |
| chat:sql | 25 | 0 | 91 / 91 / 91 |
| chat:history | 25 | 0 | 11 / 11 / 11 |
| chat:rust | 25 | 0 | 17 / 17 / 17 |

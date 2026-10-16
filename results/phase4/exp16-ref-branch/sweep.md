| metric | def | q81 |
|---|---|---|
| decode_tok_s | 17.79 (17.65-17.90) | 17.33 (17.16-17.60) **-2.6%** |
| decode_ms_tok | 56.26 (55.89-56.72) | 57.73 (56.83-58.30) **+2.6%** |
| ttft_chat_ms | 1891.08 (1882.00-1899.05) | 1934.80 (1911.85-1955.00) **+2.3%** |
| disk_ms_tok | 22.20 (21.81-22.51) | 22.34 (21.94-22.86) **+0.6%** ~noise |
| disk_waits_tok | 11.12 (10.96-11.29) | 11.26 (11.00-11.40) **+1.2%** ~noise |
| disk_ms_per_wait | 1.92 (1.91-1.92) | 1.92 (1.90-1.94) **+0.0%** ~noise |
| disk_share | 0.39 (0.39-0.40) | 0.39 (0.38-0.39) **-1.9%** |
| vram_hit_pct | 69.75 (69.59-69.89) | 69.62 (69.36-70.31) **-0.2%** ~noise |
| ssd_read_gbs | 1.97 (1.96-1.99) | 1.93 (1.91-1.96) **-1.9%** |
| ram_tier_gb | 41.99 (41.99-41.99) | 41.99 (41.99-41.99) **+0.0%** ~noise |
| load_s | 37.26 (36.57-39.86) | 36.57 (36.20-37.17) **-1.9%** |
| min_phys_avail_gb | 8.64 (8.63-8.67) | 8.89 (8.73-9.10) **+3.0%** |
| min_commit_avail_gb | 21.41 (21.36-21.53) | 21.68 (21.45-21.88) **+1.3%** |
| max_commit_used_pct | 80.78 (80.68-80.82) | 80.53 (80.36-80.75) **-0.3%** |
| max_vram_mib | 31625.50 (31524.00-31626.00) | 31544.50 (31474.00-31611.00) **-0.3%** |

Token streams vs the first run of the baseline (all prompts, greedy):

| condition | runs | identical | earliest divergence (token) | diverging prompts |
|---|---|---|---|---|
| def | 4 | 2 | 0 | chat:ball, chat:csv, chat:history, chat:photosynthesis, chat:rust, chat:sql |
| q81 | 4 | 0 | 0 | chat:ball, chat:csv, chat:history, chat:photosynthesis, chat:rust, chat:sql |

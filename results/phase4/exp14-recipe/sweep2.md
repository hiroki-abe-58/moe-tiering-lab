| metric | recP | recPd |
|---|---|---|
| decode_tok_s | 18.31 (18.29-18.35) | 17.91 (17.87-17.94) **-2.2%** |
| decode_ms_tok | 54.61 (54.49-54.69) | 55.84 (55.76-55.97) **+2.3%** |
| ttft_chat_ms | 1845.45 (1839.75-1848.85) | 1843.95 (1841.35-1848.35) **-0.1%** ~noise |
| disk_ms_tok | 17.34 (17.31-17.34) | 17.77 (17.74-17.83) **+2.5%** |
| disk_waits_tok | 12.82 (12.82-12.82) | 12.96 (12.96-12.96) **+1.1%** |
| disk_ms_per_wait | 1.33 (1.33-1.33) | 1.36 (1.36-1.37) **+2.7%** |
| disk_share | 0.32 (0.32-0.32) | 0.32 (0.32-0.32) **+0.3%** |
| vram_hit_pct | 65.38 (65.38-65.38) | 65.06 (65.06-65.06) **-0.5%** |
| ssd_read_gbs | 1.57 (1.57-1.58) | 1.58 (1.58-1.58) **+0.4%** |
| ram_tier_gb | 41.99 (41.99-41.99) | 41.99 (41.99-41.99) **+0.0%** ~noise |
| load_s | 36.82 (36.60-36.85) | 36.67 (36.63-37.12) **-0.4%** |
| min_phys_avail_gb | 8.36 (8.24-8.53) | 8.19 (8.06-8.44) **-2.0%** |
| min_commit_avail_gb | 21.57 (21.32-21.75) | 21.51 (21.40-21.56) **-0.3%** ~noise |
| max_commit_used_pct | 80.64 (80.47-80.86) | 80.69 (80.64-80.79) **+0.1%** ~noise |
| max_vram_mib | 31808.00 (31706.00-31848.00) | 31827.00 (31787.00-31848.00) **+0.1%** ~noise |

Token streams vs the first run of the baseline (all prompts, greedy):

| condition | runs | identical | earliest divergence (token) | diverging prompts |
|---|---|---|---|---|
| recP | 5 | 5 | None | - |
| recPd | 5 | 0 | 0 | chat:ball, chat:csv, chat:history, chat:photosynthesis, chat:rust, chat:sql |

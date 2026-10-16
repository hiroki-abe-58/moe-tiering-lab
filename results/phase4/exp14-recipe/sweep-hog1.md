| metric | hogP |
|---|---|
| decode_tok_s | 16.64 (16.51-16.76) |
| decode_ms_tok | 60.11 (59.67-60.57) |
| ttft_chat_ms | 2012.95 (1973.90-2068.70) |
| disk_ms_tok | 17.38 (17.37-17.43) |
| disk_waits_tok | 12.82 (12.82-12.82) |
| disk_ms_per_wait | 1.33 (1.33-1.34) |
| disk_share | 0.29 (0.29-0.29) |
| vram_hit_pct | 65.38 (65.38-65.38) |
| ssd_read_gbs | 1.43 (1.42-1.44) |
| ram_tier_gb | 41.99 (41.99-41.99) |
| load_s | 37.06 (36.92-37.10) |
| min_phys_avail_gb | 7.32 (7.21-7.58) |
| min_commit_avail_gb | 20.36 (20.33-20.50) |
| max_commit_used_pct | 81.72 (81.60-81.75) |
| max_vram_mib | 31907.00 (31900.00-31948.00) |

Token streams vs the first run of the baseline (all prompts, greedy):

| condition | runs | identical | earliest divergence (token) | diverging prompts |
|---|---|---|---|---|
| hogP | 3 | 3 | None | - |

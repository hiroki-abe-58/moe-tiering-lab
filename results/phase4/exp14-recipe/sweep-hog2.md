| metric | hogA |
|---|---|
| decode_tok_s | 17.37 (17.37-17.45) |
| decode_ms_tok | 57.56 (57.30-57.56) |
| ttft_chat_ms | 1951.55 (1948.25-1954.30) |
| disk_ms_tok | 19.23 (19.23-19.30) |
| disk_waits_tok | 13.82 (13.82-13.82) |
| disk_ms_per_wait | 1.38 (1.38-1.38) |
| disk_share | 0.34 (0.33-0.34) |
| vram_hit_pct | 63.92 (63.92-63.92) |
| ssd_read_gbs | 1.67 (1.67-1.67) |
| ram_tier_gb | 42.00 (42.00-42.00) |
| load_s | 37.21 (35.95-37.47) |
| min_phys_avail_gb | 7.36 (7.33-7.37) |
| min_commit_avail_gb | 21.38 (21.32-21.47) |
| max_commit_used_pct | 80.80 (80.73-80.86) |
| max_vram_mib | 31431.00 (31387.00-31431.00) |

Token streams vs the first run of the baseline (all prompts, greedy):

| condition | runs | identical | earliest divergence (token) | diverging prompts |
|---|---|---|---|---|
| hogA | 3 | 3 | None | - |

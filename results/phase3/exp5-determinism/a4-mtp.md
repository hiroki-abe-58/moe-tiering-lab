| metric | t26L0m | t26m |
|---|---|---|
| decode_tok_s | 10.00 (10.00-10.00) | 10.35 (10.33-10.37) **+3.4%** |
| decode_ms_tok | 99.99 (99.98-100.00) | 96.64 (96.44-96.85) **-3.3%** |
| ttft_chat_ms | 3557.08 (3549.60-3564.55) | 3465.88 (3424.15-3507.60) **-2.6%** |
| disk_ms_tok | 58.41 (58.23-58.59) | 57.77 (57.58-57.96) **-1.1%** |
| disk_waits_tok | 26.29 (26.25-26.33) | 26.07 (26.05-26.08) **-0.8%** |
| disk_ms_per_wait | 2.18 (2.18-2.18) | 2.15 (2.14-2.17) **-1.3%** |
| disk_share | 0.58 (0.58-0.59) | 0.60 (0.60-0.60) **+2.3%** |
| vram_hit_pct | 62.69 (62.61-62.77) | 62.89 (62.78-63.00) **+0.3%** |
| ssd_read_gbs | 3.05 (3.04-3.06) | 3.11 (3.10-3.11) **+1.9%** |
| spec_accept | 1.00 (1.00-1.00) | 1.00 (1.00-1.00) **+0.0%** ~noise |
| ram_tier_gb | 25.99 (25.99-25.99) | 25.99 (25.99-25.99) **+0.0%** ~noise |
| load_s | 27.21 (27.14-27.29) | 29.38 (29.19-29.58) **+8.0%** |
| min_phys_avail_gb | 24.68 (24.46-24.91) | 24.83 (24.69-24.96) **+0.6%** ~noise |
| min_commit_avail_gb | 38.92 (38.84-39.00) | 39.01 (38.85-39.18) **+0.2%** ~noise |
| max_commit_used_pct | 65.06 (64.98-65.13) | 64.98 (64.83-65.13) **-0.1%** ~noise |
| max_vram_mib | 31923.50 (31869.00-31978.00) | 31873.00 (31828.00-31918.00) **-0.2%** ~noise |

Token streams vs the first run of the baseline (all prompts, greedy):

| condition | runs | identical | earliest divergence (token) | diverging prompts |
|---|---|---|---|---|
| t26L0m | 2 | 2 | None | - |
| t26m | 2 | 0 | 0 | chat:ball, chat:csv, chat:history, chat:photosynthesis, chat:rust, chat:sql |

# Exp4 - RAM tier size vs decode speed (after pagefile 48 GiB, reboot 2026-10-16)

Setup: Maya v1.1.11, Maya-S-v2-IQ2_XXS, 32K ctx, 1x RTX 5090, `STRATA_GLM_RAM_GB` pinned per condition, 3 interleaved rounds
(order reversed each round), Strata server stopped, commit limit 111.4 GB (`state-after-reboot.json`).
Raw: `exp4-tier-sweep.{json,md}`, per-run JSON in `exp4-tier-sweep-runs/`. (`exp4-smoke*` = 1-round smoke test, not for citing.)

## Decode speed vs tier [measured, median of 3]

| tier GB | decode tok/s | vs t26 | disk ms/tok | disk share | prefill 8K tok/s | min phys avail GB | max commit used |
|---|---|---|---|---|---|---|---|
| 10 (phase 1) | 6.9 | - | 72.7 | 0.71 | 733 | n/a | n/a |
| 18 (phase 1) | 8.8 | - | 55.0 | 0.62 | 866 | n/a | n/a |
| 26 | 11.66 | base | 49.2 | 0.57 | 1030 | 26.2 | 63% |
| 32 | 13.76 | +17.9% | 36.1 | 0.50 | 1221 | 20.1 | 69% |
| 38 | 16.70 | +43.2% | 23.9 | 0.40 | 1502 | 14.1 | 74% |
| 42 | 18.80 | +61.2% | 17.6 | 0.33 | 1778 | 10.1 | 78% |

- Round-to-round spread inside each condition is <= ~1%; the effect is far above noise.
- Roughly +0.45 tok/s per extra GB of pinned tier in the 26-42 GB range; no saturation seen yet. VRAM hit rate stays ~65% in all conditions -> the gain is
  entirely fewer SSD waits (waits/token 24 -> 13, ms/wait 2.03 -> 1.33).
- Phase-1 t26 was 11.2 tok/s, phase-2 t26 11.66 (+4%, different boot/background state); compare within a table, not across.
- Phase-1 conclusion refined: the limiter on this PC was the pagefile (commit), not a driver cap. With 48 GiB pagefile the tier can be raised to 42 GB with >=10 GB physical RAM left.
- NOT tested: t44+ (min phys avail would drop below the 8 GB safety margin), behaviour with Strata running at the same time (it holds ~36 GB RAM -> cannot coexist with t42).

## Output equality across tiers [measured, greedy, 6 chat prompts x 256 tokens + 2 prefill prompts x 16 tokens]
- Run-to-run inside t32/t38/t42: all 3 rounds bit-identical on all prompts.
- t26: round 0 differed from rounds 1 and 2 (which match each other) on 5/6 chat prompts (first divergence token 0-148). Round 0 was the first engine start after boot; cause NOT determined.
- Across tiers: chat streams diverge from some token onward on most prompts (first divergence token 0-159); the 16-token prefill outputs are identical everywhere.
- So "tier size does not change outputs" is NOT established. Cause of the cross-tier difference not investigated (candidates: numerics depending on which expert copy/kernel path
  serves a token, MTP/speculative acceptance depending on timing). No quality metric was measured -> do not claim quality loss or equality.

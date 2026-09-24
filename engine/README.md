# Momentum engine v2

One pipeline for every pick: **gates → rank → diversify → levels.** Nothing is picked by eye.

| File | What it does |
|---|---|
| `engine.py` | Hard gates (R27 price cap, R11 liquidity floor, R4 52-week-low age, R5 insider veto, R7 already held), ranking, max one pick per theme, and entry/stop/target levels |
| `rank.py` | `ranking_function_v1` — four equally weighted components (RSI band, volume, close-to-high, day move), each traced to a measured cell in study #2 |
| `backtest_v2.py` | Replays the full pipeline day by day with the live exit rules; alpha vs benchmark; composition-preserving permutation test |
| `ablate.py` | Gate-by-gate ablation per universe |

## Levels

`plan(close, day_low)` sets a limit band from the prior close to +3% and previews stop and target for a fill at the **top** of the band. A name that opens above its band is skipped, not chased.

Once an order fills, the live levels are `fill_levels(fill, day_low)` (R29): stop = min(max(signal-day low × 0.995, fill × 0.92), fill × 0.97), target = fill × 1.12, both rounded **up** to the cent. This is exactly what the backtest measures. Band-top levels alone break down on a gap-down open: on 2026-09-23 THM filled at $2.811, below its $2.95–3.04 band, and the band-top stop of $2.80 sat 0.4% under the fill. An open position's stop is never loosened to meet the new rule.

## Volume and insider gates

**Volume (R30).** Relative volume is `official_relvol(day_volume, prior_daily_volumes)`: the day's official volume, taken from the scan's Volume column, divided by the mean of the prior 20 daily-bar volumes. That is the same basis the backtest uses. Do not sum 5-minute bars to get a day's volume. On 2026-09-23 those sums captured only 38–59% of official volume (EGHT 2.78M vs 4.70M, ADCT 0.84M vs 1.97M), so every reading was biased low by a different amount. ADCT failed the 1x floor at 0.48x when it had really traded 1.12x. FSLY made the 9/23 list only because of this error. It stays in the paper log as published.

**Insider selling (R5).** A cluster is two or more *different* insiders selling on the open market within 30 days, or one insider selling three or more times. A cluster vetoes the pick; set `insider_cluster` on the candidate. Evidence comes from insider-sale items in the news feed, because Form 4 content cannot be read through the MCP (404). A filing count alone never vetoes. On 2026-09-24 this removed ADPT (two insiders, $6.4M in 30 days) and TEM (four executives, $12.9M on 8/18).

## What the backtest says (2026-09-23)

**Live parity** is the way the engine actually trades: enter at the next open, skip anything that opens above the band, take levels from the fill, and measure alpha against the benchmark from its open on the entry day.

| Universe | Top-3 alpha | p | Skipped (opened above band) |
|---|---|---|---|
| Small/mid caps, out-of-sample (29 names, 12 mo) | +0.23% (n=222) | 0.327 | 20 |
| Crypto proxies, out-of-sample (10 names, 6 mo) | +0.46% (n=51) | 0.241 | 12 |
| Large caps, in-sample (39 names, 12 mo) | +0.03% (n=70) | 0.628 | 15 |

**Signal-day close entry** is the older headline. It is kept for comparison, but a pre-market pick cannot buy that close.

| Universe | Top-3 alpha | p | Bottom third | Top third |
|---|---|---|---|---|
| Small/mid caps | −0.17% | 0.788 | −0.93% | −0.05% |
| Crypto proxies | +0.90% | 0.084 | −0.38% | +1.25% |
| Large caps | +1.10% | 0.139 | +0.49% | +1.84% |

The close-entry figures correct the first version of this README, which quoted −0.18% / +0.87% / +1.09% from a run made before stops were rounded up.

**No significant edge in any universe when traded as it is actually traded.** The large-cap +1.10% was almost entirely the overnight gap, which a pre-market pick cannot capture. The one repeatable result is that the ranking orders correctly: the bottom third is always worst. It avoids losers; it has not been shown to find winners. Splitting picks by opening gap (gap-down vs flat/up) flips sign by universe, so no gap filter is applied (P15).

The volume gate (R11) flips sign by universe (small caps −1.10 spread, crypto +2.74), so it is kept as a liquidity floor for real money, not as an alpha filter.

## Running it

`backtest_v2.py` reads daily-bar JSON exported from the Robinhood MCP `get_equity_historicals` tool; the `TR` path at the top points at wherever those exports live. Live picks are produced by feeding scan candidates (price, % change on the regular-session close, RSI, relative volume from `official_relvol()`, % off high, 52-week-low age, `insider_cluster`) into `engine.select()`. Run `python3 test_engine.py` after any change to levels or gates.

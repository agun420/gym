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

`backtest_v2.py` reads daily-bar JSON exported from the Robinhood MCP `get_equity_historicals` tool; the `TR` path at the top points at wherever those exports live. Live picks are produced by feeding scan candidates (price, % change, RSI, pace-adjusted relative volume, % off high, 52-week-low age) into `engine.select()`.

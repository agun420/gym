# Momentum engine v2

One pipeline for every pick: **gates → rank → diversify → levels.** Nothing is picked by eye.

| File | What it does |
|---|---|
| `engine.py` | Hard gates (R27 price cap, R11 liquidity floor, R4 52-week-low age, R5 insider veto, R7 already held), ranking, max one pick per theme, and entry/stop/target levels |
| `rank.py` | `ranking_function_v1` — four equally weighted components (RSI band, volume, close-to-high, day move), each traced to a measured cell in study #2 |
| `backtest_v2.py` | Replays the full pipeline day by day with the live exit rules; alpha vs benchmark; composition-preserving permutation test |
| `ablate.py` | Gate-by-gate ablation per universe |

## Levels

`plan(close, day_low)` sets a limit band from the prior close to +3%. Stop and target are fixed prices computed at the **top** of the band, and the stop is rounded **up**, so any fill inside the band keeps the stop within −8% (R1) and the target at or above +12% (R17). A name that opens above its band is skipped, not chased.

## What the backtest says (2026-09-23)

| Universe | Top-3 alpha | p | Bottom third | Top third |
|---|---|---|---|---|
| Small/mid caps, out-of-sample (29 names, 12 mo) | −0.18% | 0.795 | −0.99% | +0.04% |
| Crypto proxies, out-of-sample (10 names, 6 mo) | +0.87% | 0.090 | −0.41% | +1.23% |
| Large caps, in-sample (39 names, 12 mo) | +1.09% | 0.135 | +0.49% | +1.83% |

**No significant edge over baseline out-of-sample.** The one repeatable result is that the ranking orders correctly in all three universes: the bottom third is always worst. It avoids losers; it has not been shown to find winners.

The volume gate (R11) flips sign by universe (small caps −1.10 spread, crypto +2.74), so it is kept as a liquidity floor for real money, not as an alpha filter.

## Running it

`backtest_v2.py` reads daily-bar JSON exported from the Robinhood MCP `get_equity_historicals` tool; the `TR` path at the top points at wherever those exports live. Live picks are produced by feeding scan candidates (price, % change, RSI, pace-adjusted relative volume, % off high, 52-week-low age) into `engine.select()`.

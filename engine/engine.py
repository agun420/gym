"""Momentum engine v2 -- one pipeline: GATES (hard) -> RANK -> DIVERSIFY -> LEVELS.

Fixes audit gaps G1 (gates and ranking disagreed) and G3 (no diversification).
Every gate cites the rule it enforces. Anything a gate removes is logged with
its reason (R15), never silently dropped.
"""
import math
from rank import score as rank_score

POSITION_CAP = 150.0          # R21
MIN_PRICE = 1.0

def gates(c):
    """Return list of failure reasons. Empty list == passes."""
    f = []
    p = c.get("price")
    if p is None:                         f.append("no price")
    elif p > POSITION_CAP:                f.append(f"R27 price ${p:.0f} > ${POSITION_CAP:.0f} cap: fractional only, cannot carry a stop")
    elif p < MIN_PRICE:                   f.append("price < $1")
    v = c.get("paced_relvol")
    if v is None or v < 1.0:              f.append(f"R11 volume {v if v is None else round(v,2)}x < 1x floor")
    if c.get("low52_age_days") is not None and c["low52_age_days"] < 15:      # R4: ~15 trading days
                                          f.append(f"R4 52-week low only {c['low52_age_days']}d old")
    if c.get("insider_cluster"):          f.append("R5 insider selling cluster")
    if c.get("held"):                     f.append("R7 already held in the book")
    return f

def flags(c):
    """R9/R18: retracement is a FLAG, never a reject. 3% for large caps, 8% for small."""
    out=[]; oh=c.get("off_high")
    lim = 0.03 if (c.get("mktcap") or 0) >= 10e9 else 0.08
    if oh is not None and oh > lim: out.append(f"R18 faded {oh*100:.1f}% off high (limit {lim*100:.0f}%)")
    return out

def levels(entry, day_low):
    """R1 stop <= 8%, R26 stop >= 3%, R17 target +12%."""
    stop = max(day_low * 0.995, entry * 0.92)
    stop = min(stop, entry * 0.97)
    # round the stop UP and the target UP: nearest-cent rounding pushed sub-$5 stops past -8% (R1)
    return math.ceil(stop * 100) / 100, math.ceil(entry * 1.12 * 100) / 100

def plan(close, day_low, chase=0.03):
    """Open-entry plan: limit band [close, close*(1+chase)]. The stop/target shown are for a fill at the
    TOP of the band. They are a preview only: once filled, the live levels are fill_levels(fill, day_low)."""
    limit = round(close * (1 + chase), 2)
    stop, tgt = levels(limit, day_low)
    sh = int(POSITION_CAP // limit)
    return dict(limit=limit, stop=stop, target=tgt, shares=sh, cost=round(sh*limit,2), signal_low=day_low,
                risk=round(sh*(limit-stop),2), stop_from_limit=stop/limit-1, stop_from_close=stop/close-1,
                tgt_from_limit=tgt/limit-1, tgt_from_close=tgt/close-1)

def fill_levels(fill, signal_low):
    """G6: levels re-anchored to the ACTUAL fill, exactly as the backtest computes them. A gap-down open
    fills below the band; band-top levels then left THM (fill 2.811, stop 2.80) a -0.4% stop, breaking R26."""
    return levels(fill, signal_low)

def size(entry, stop):
    sh = int(POSITION_CAP // entry)
    return sh, round(sh * entry, 2), round(sh * (entry - stop), 2)

def select(cands, n=3, theme_key="theme"):
    passed, rejected = [], []
    for c in cands:
        why = gates(c)
        (rejected if why else passed).append((c, why))
    scored = []
    for c, _ in passed:
        s = rank_score({"sym": c["sym"], "rsi": c.get("rsi"), "paced_relvol": c.get("paced_relvol"),
                        "off_high": c.get("off_high"), "pct": c.get("pct")})
        scored.append((s["score"], c, s))
    scored.sort(key=lambda t: -t[0])
    picks, seen = [], set()
    for sc, c, s in scored:                               # G3: max one per theme
        th = c.get(theme_key) or c["sym"]
        if th in seen:
            rejected.append((c, [f"R14 diversification: already holding a {th} pick"])); continue
        seen.add(th); picks.append((sc, c, s))
        if len(picks) == n: break
    return picks, rejected

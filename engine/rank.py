"""ECC momentum engine — candidate ranking function v1 (P6).

Every component below is traceable to a measured cell in study #2
(40 non-crypto names, 7683 observations, 12 months, alpha vs SPY).
Nothing here is invented; where the evidence is ambiguous the component
is deliberately FLAT rather than guessed.

PROVISIONAL under R3: the best stack in study #2 scored p=0.134 against a
Bonferroni threshold of p<0.0017. This function ORDERS candidates. It does
not claim any of them are good.
"""

def rsi_score(rsi):
    # study #2 RSI ladder, alpha 5d: 45-50 +1.19% | 50-55 +2.12% | 55-60 +1.08%
    #                                60-65 -1.55% | 65-70 -0.89% | 70-75 +2.57% | 75+ +1.42%
    # 45-60 is the measured-good band. 60-70 is the measured-BAD band.
    # Above 70 the ladder is non-monotonic (the +2.57% bump has no story), so
    # it is scored NEUTRAL rather than rewarded -- refusing to fit that bump.
    if rsi is None: return 0.5
    if 45 <= rsi <= 60: return 1.0
    if 60 < rsi <= 70:  return 0.2          # the two worst cells in the study
    if rsi > 70:        return 0.5          # non-monotonic, untrusted
    return 0.5                              # <45, thin evidence

def volume_score(paced):
    # study #2: >=1x beat <1x in BOTH studies and BOTH halves of the year.
    # But it REVERSES above the floor: >=2x +0.16%, >=3x -0.20%, >=5x -1.74%.
    # So volume is a FLOOR, never a conviction score. More is not better.
    if paced is None: return 0.0
    if paced < 1.0:  return 0.0             # hard fail, R11
    if paced <= 2.0: return 1.0             # the measured sweet spot
    if paced <= 3.0: return 0.6
    return 0.3                              # heavy volume scored NEGATIVE alpha

def close_score(off_high):
    # study #2: closed <=3% off high +0.90% alpha | closed >3% off high -2.10%.
    # A clean 3.0-point spread. Linear decay to the 3% line.
    if off_high is None: return 0.5
    if off_high <= 0:    return 1.0
    if off_high >= 0.03: return 0.0
    return 1.0 - (off_high / 0.03)

def move_score(pct):
    # study #2 median split on day %chg: LOW half +0.96% alpha, HIGH half +0.45%.
    # Smaller breakouts outperformed larger ones. Penalise chasing.
    if pct is None: return 0.5
    if pct < 0.05:  return 0.0              # below the board's own threshold
    if pct <= 0.08: return 1.0              # around the study median (7.0%)
    if pct <= 0.15: return 0.6
    if pct <= 0.25: return 0.3
    return 0.1                              # parabolic

def regime_multiplier(spy_last, spy_ma50):
    # study #2: breakouts on risk-OFF tape +2.06% alpha (n=66, 60.6% hit rate)
    # vs risk-ON +0.37% (n=263). p=0.184 -- promising, NOT significant.
    # Applied at 1.15x rather than the ~5x the raw ratio implies, because
    # the sample is 49 risk-off days and R3 forbids sizing on that.
    if spy_last is None or spy_ma50 is None: return 1.0
    return 1.15 if spy_last < spy_ma50 else 1.0

WEIGHTS = {"rsi": 0.25, "volume": 0.25, "close": 0.25, "move": 0.25}
# Equal weights ON PURPOSE. Study #2 gives no evidence for the RELATIVE
# importance of these four, and inventing weights would be exactly the
# curve-fit R3 exists to prevent. Revisit only at n>=30 closed picks.

def score(c, spy_last=None, spy_ma50=None):
    parts = {
        "rsi":    rsi_score(c.get("rsi")),
        "volume": volume_score(c.get("paced_relvol")),
        "close":  close_score(c.get("off_high")),
        "move":   move_score(c.get("pct")),
    }
    base = sum(WEIGHTS[k] * v for k, v in parts.items())
    mult = regime_multiplier(spy_last, spy_ma50)
    return {
        "symbol": c.get("sym"), "score": round(base * mult, 4),
        "base": round(base, 4), "regime_multiplier": mult,
        "components": {k: round(v, 3) for k, v in parts.items()},
        # volume is a gate as well as a component: below 1x nothing else matters
        "hard_fail": parts["volume"] == 0.0,
    }

def rank(candidates, spy_last=None, spy_ma50=None):
    out = [score(c, spy_last, spy_ma50) for c in candidates]
    out.sort(key=lambda r: (not r["hard_fail"], r["score"]), reverse=True)
    return out

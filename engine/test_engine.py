"""Invariants the live levels must hold. Run: python3 test_engine.py (or pytest)."""
from engine import levels, fill_levels, plan, gates, official_relvol


def test_band_top_preview_matches_published_levels():
    # 2026-09-23 picks: published stop/target came from plan() at the top of the band
    assert (plan(6.41, 5.92)["stop"], plan(6.41, 5.92)["target"]) == (6.08, 7.40)
    assert (plan(1.47, 1.356)["stop"], plan(1.47, 1.356)["target"]) == (1.39, 1.70)
    assert (plan(2.95, 2.64)["stop"], plan(2.95, 2.64)["target"]) == (2.80, 3.41)


def test_gap_down_fill_reanchors_levels():
    # THM opened 2.811 below its band; band-top stop 2.80 was 0.4% away (R26 breach)
    stop, tgt = fill_levels(2.811, 2.64)
    assert (stop, tgt) == (2.63, 3.15)


def test_stop_always_between_3_and_8_percent_of_fill():
    for fill in [1.07, 1.4593, 2.811, 3.04, 6.36, 10.6, 48.2, 149.99]:
        for low_frac in [0.80, 0.90, 0.95, 0.99, 1.0]:
            stop, tgt = levels(fill, fill * low_frac)
            assert fill * 0.92 - 1e-9 <= stop <= fill * 0.97 + 0.01, (fill, low_frac, stop)  # R1 / R26
            assert tgt >= fill * 1.12 - 1e-9                                                   # R17


def test_relvol_uses_official_volume_not_5min_sum():
    # ADCT 2026-09-23: official volume 1.97M, summed 5-minute bars 0.84M, 20-day daily-bar mean 1.757M (R30)
    prior = [1756902.55] * 20
    assert round(official_relvol(1.97e6, prior), 2) == 1.12
    assert not [w for w in gates(dict(price=5.0, paced_relvol=official_relvol(1.97e6, prior))) if w.startswith("R11")]
    assert round(official_relvol(843538, prior), 2) == 0.48          # what the 9/23 screen wrongly used
    assert official_relvol(1e6, [1e6] * 19) is None                   # short history: no reading, gate rejects
    assert [w for w in gates(dict(price=5.0, paced_relvol=None)) if w.startswith("R11")]


def test_insider_cluster_vetoes():
    # R5: ADPT and TEM, 2026-09-24 -- clean technicals, vetoed on clustered insider selling
    assert "R5 insider selling cluster" in gates(dict(price=29.57, paced_relvol=1.66, insider_cluster=True))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)

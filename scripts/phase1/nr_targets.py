"""Required EV/W* tables for N × RR combinations (P1-NR)."""

from __future__ import annotations

from scripts.phase1.common import GATE2_PCT, INITIAL_BANKROLL, POSITION_Q
from scripts.phase1.metrics import fee_breakeven_win_rate
from scripts.phase1.n_targets import SL_PCT, ROUNDTRIP_COST_PCT, n_band, w_for_ev

NR_N_FOCUS = (20, 50)
NR_RR_FOCUS = (3.0, 5.0)


def build_nr_target_row(n_target: int, rr_ratio: float, sl_pct: float = SL_PCT) -> dict:
    p_star = int(INITIAL_BANKROLL * GATE2_PCT)
    q = INITIAL_BANKROLL // 5
    tp_pct = sl_pct * rr_ratio
    ev_star = p_star / n_target
    ev_pct = ev_star / q
    band_low, band_high = n_band(n_target)
    w_be = fee_breakeven_win_rate(sl_pct, tp_pct, ROUNDTRIP_COST_PCT)
    w_star = w_for_ev(ev_pct, sl_pct, tp_pct, ROUNDTRIP_COST_PCT)
    max_ev_jpy = q * (tp_pct - ROUNDTRIP_COST_PCT)
    return {
        "n_target": n_target,
        "rr_ratio": rr_ratio,
        "n_band_low": band_low,
        "n_band_high": band_high,
        "sl_pct": sl_pct,
        "tp_pct": tp_pct,
        "p_star_jpy": p_star,
        "ev_star_jpy": ev_star,
        "ev_star_pct_of_q": round(ev_pct * 100, 4),
        "fee_breakeven_w": round(w_be, 4),
        "w_star_gate2": round(w_star, 4),
        "w_star_feasible": w_star <= 1.0,
        "max_ev_at_w100_jpy": round(max_ev_jpy, 2),
        "gate2_feasible_at_w100": max_ev_jpy >= ev_star,
        "position_q": q,
    }


def build_focus_grid(sl_pct: float = SL_PCT) -> list[dict]:
    rows = []
    for n in NR_N_FOCUS:
        for rr in NR_RR_FOCUS:
            rows.append(build_nr_target_row(n, rr, sl_pct))
    return rows

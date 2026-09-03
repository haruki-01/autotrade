"""Required EV and win-rate tables for N sensitivity (P1-N)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.phase1.common import GATE2_PCT, GATE2_P_TARGET, INITIAL_BANKROLL, POSITION_Q
from scripts.phase1.metrics import fee_breakeven_win_rate

N_CANDIDATES = (10, 20, 50, 100)
SL_PCT = 0.008
TP_PCT = 0.016
ROUNDTRIP_COST_PCT = 0.0004  # conservative lev + slip proxy per trade


def n_band(n_target: int, tolerance: float = 0.20) -> tuple[int, int]:
    low = max(1, int(n_target * (1 - tolerance)))
    high = int(n_target * (1 + tolerance))
    return low, high


def w_for_ev(ev_pct: float, sl_pct: float = SL_PCT, tp_pct: float = TP_PCT, cost_pct: float = ROUNDTRIP_COST_PCT) -> float:
    """Win rate needed for EV/Q = ev_pct under RR 1:2."""
    denom = tp_pct + sl_pct
    if denom <= 0:
        return float("nan")
    return (ev_pct + sl_pct + cost_pct) / denom


def build_n_targets_table(bankroll: int = INITIAL_BANKROLL) -> list[dict]:
    p_star = int(bankroll * GATE2_PCT)
    q = bankroll // 5
    w_fee_be = fee_breakeven_win_rate(SL_PCT, TP_PCT, ROUNDTRIP_COST_PCT)
    rows = []
    for n in N_CANDIDATES:
        ev_star = p_star / n
        ev_pct = ev_star / q
        band_low, band_high = n_band(n)
        rows.append(
            {
                "n_target": n,
                "n_band_low": band_low,
                "n_band_high": band_high,
                "p_star_jpy": p_star,
                "ev_star_jpy": ev_star,
                "ev_star_pct_of_q": round(ev_pct * 100, 4),
                "fee_breakeven_w": round(w_fee_be, 4),
                "w_star_gate2": round(w_for_ev(ev_pct), 4),
                "position_q": q,
                "bankroll": bankroll,
            }
        )
    return rows


def write_n_targets_table(out_path: Path | None = None) -> list[dict]:
    rows = build_n_targets_table()
    if out_path is None:
        out_path = Path(__file__).resolve().parents[2] / "data" / "phase1" / "n_targets_table.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"gate2_p_target": GATE2_P_TARGET, "n_candidates": list(N_CANDIDATES), "rows": rows}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rows


if __name__ == "__main__":
    rows = write_n_targets_table()
    for r in rows:
        print(
            f"N={r['n_target']:3d}  EV*={r['ev_star_jpy']:6.0f}  "
            f"W_be={r['fee_breakeven_w']:.3f}  W*={r['w_star_gate2']:.3f}"
        )

"""ADV-002/001/005/004 を各10回: 1年 → 決済EV黒なら8年、赤なら次の1点差分。

Usage:
    PYTHONPATH=src python3 scripts/run_adv_cycles.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotrade.data.binance_derivatives import load_context  # noqa: E402
from autotrade.data.binance_vision import ensure_spot_1m_archive  # noqa: E402
from autotrade.data.bybit import load_ohlcv  # noqa: E402
from autotrade.eval import load_eval_config  # noqa: E402
from autotrade.strategy.adv_entry import CYCLES_ADV, SIGNALS_ADV  # noqa: E402
from autotrade.strategy.bracket import (  # noqa: E402
    BARS_PER_HOUR_1M,
    MAX_HOURS,
    RR,
    STOP_PCT,
)

_spec = importlib.util.spec_from_file_location(
    "run_bracket_pack", Path(__file__).resolve().parents[1] / "scripts" / "run_bracket_pack.py"
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)
run_bracket = _mod.run_bracket


def _cost_rate(cfg, rr: float) -> float:
    maker, taker = 0.0002, cfg.fee_rate_per_side
    slip = cfg.slippage_pct_per_side
    w0 = 1.0 / (1.0 + rr)
    return maker + w0 * maker + (1 - w0) * (taker + slip)


def _join_deriv(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    h15 = df.resample("15min", label="left", closed="left").last().dropna(how="all")
    ctx = load_context(h15.index, symbol="BTCUSDT", start=start, end=end)
    if ctx.frame is None or ctx.frame.empty:
        return df
    aligned = ctx.frame.reindex(h15.index)
    aligned.index = aligned.index + pd.Timedelta(minutes=14)
    out = aligned.reindex(df.index, method="ffill")
    return df.join(out, how="left", rsuffix="_d")


def _window(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    lo = pd.Timestamp(start, tz="UTC")
    hi = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
    return df.loc[(df.index >= lo) & (df.index <= hi)]


def _eval_one(df, spec, cfg, months: float) -> dict:
    fn = SIGNALS_ADV[spec["signal"]]
    sig = fn(df, spec.get("params") or {}).values
    r = run_bracket(
        df,
        sig,
        stop_pct=STOP_PCT,
        rr=RR,
        max_bars=int(round(MAX_HOURS * BARS_PER_HOUR_1M)),
        cost_rate=_cost_rate(cfg, RR),
        notional=cfg.margin_per_trade * cfg.leverage,
    )
    if not r.get("trades"):
        return {
            "trades": 0,
            "win_rate_resolved": float("nan"),
            "timeout_rate": float("nan"),
            "ev_usdt": float("nan"),
            "ev_resolved_usdt": float("nan"),
            "z_vs_null": float("nan"),
            "per_month": 0.0,
            "green": False,
        }
    r["per_month"] = r["trades"] / months
    r["green"] = bool(
        r.get("ev_resolved_usdt", float("nan")) > 0 and r["trades"] >= cfg.min_trades
    )
    return r


def _load_year() -> tuple[pd.DataFrame, object, float]:
    cfg, _, _ = load_eval_config("configs/eval_v4_btc_1m.yaml")
    with open("eval/locks/eval_v4_btc_1m.lock.yaml", encoding="utf-8") as f:
        lock = yaml.safe_load(f)
    path = next(iter(lock["datasets"]["Y"]["symbols"]["BTCUSDT"]["files"]))
    df = load_ohlcv(Path(path))
    start, end = cfg.sets["Y"].start, cfg.sets["Y"].end
    df = _window(df, start, end)
    df = _join_deriv(df, start, end)
    months = (
        pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1) - pd.Timestamp(start, tz="UTC")
    ).days / 30.4375
    return df, cfg, months


def _load_eight() -> tuple[pd.DataFrame, object, float]:
    cfg, _, _ = load_eval_config("configs/eval_v3_btc.yaml")
    start, end = "2018-10-01", "2026-08-22"
    print("fetch 1m 8y archive if missing…", flush=True)
    raw = ensure_spot_1m_archive(
        symbol="BTCUSDT", start="2018-09-01", end=end, cache_dir=Path("data/cache")
    )
    df = _window(raw, start, end)
    df = _join_deriv(df, start, end)
    months = (
        pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1) - pd.Timestamp(start, tz="UTC")
    ).days / 30.4375
    return df, cfg, months


def main() -> None:
    families = ["adv002", "adv001", "adv005", "adv004"]
    df_y, cfg_y, months_y = _load_year()
    print(f"Set Y bars={len(df_y):,} deriv_cols={[c for c in df_y.columns if c in ('acct_ratio','oi')]}", flush=True)
    df8 = None
    cfg8 = months8 = None
    all_rows: list[dict] = []
    md: list[str] = [
        "# ADV 入口サイクル（各10回）",
        "",
        "枠: 12h / 損切り1.00% / 1:1.5 / 1枠 / 入口メイカー。1分足実データ（Binance Vision）。",
        "1年は Set Y（2025-08-23〜2026-08-22）。**決済EV>0 かつ n≥100** だけ8年（2018-10-01〜2026-08-22）。",
        "変種は検証前に固定した1点差分。synthetic は使っていない。",
        "",
    ]

    for fam in families:
        md += [f"## {fam}", "", "| 回 | id | 変更 | n | 回/月 | 勝率 | 強制決済 | EV全部 | EV決済 | 1年 | 8年 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        eight_note = "未実施"
        for i, row in enumerate(CYCLES_ADV[fam]):
            spec = {
                "signal": fam if fam != "adv004" else "adv004",
                "params": row["params"],
                "why": row["why"],
            }
            print(f"\n=== {row['id']} 1y ===", flush=True)
            r = _eval_one(df_y, spec, cfg_y, months_y)
            rec = {
                "family": fam,
                "round": i,
                "logic_id": row["id"],
                "why": row["why"],
                **{k: r.get(k) for k in (
                    "trades", "per_month", "win_rate_resolved", "timeout_rate",
                    "ev_usdt", "ev_resolved_usdt", "z_vs_null", "green",
                )},
            }
            eight_txt = "—"
            if r.get("green"):
                if df8 is None:
                    df8, cfg8, months8 = _load_eight()
                print(f"=== {row['id']} 8y ===", flush=True)
                r8 = _eval_one(df8, spec, cfg8, months8)
                rec["eight"] = {k: r8.get(k) for k in (
                    "trades", "per_month", "win_rate_resolved", "timeout_rate",
                    "ev_usdt", "ev_resolved_usdt", "z_vs_null", "green",
                )}
                eight_txt = (
                    f"n={r8.get('trades')} EV決済={r8.get('ev_resolved_usdt')}"
                    f"{' 黒' if r8.get('green') else ' 赤'}"
                )
                eight_note = eight_txt
            else:
                rec["eight"] = None
            all_rows.append(rec)
            n = r.get("trades") or 0
            wr = r.get("win_rate_resolved")
            wr_s = f"{wr*100:.1f}%" if wr == wr else "—"
            to = r.get("timeout_rate")
            to_s = f"{to*100:.0f}%" if to == to else "—"
            ev = r.get("ev_usdt")
            evr = r.get("ev_resolved_usdt")
            yv = "黒" if r.get("green") else "赤"
            md.append(
                f"| {i} | `{row['id']}` | {row['why']} | {n} | {r.get('per_month', 0):.1f} "
                f"| {wr_s} | {to_s} | {ev if ev==ev else float('nan'):+.4f} "
                f"| {evr if evr==evr else float('nan'):+.4f} | {yv} | {eight_txt} |"
            )
            if r.get("green"):
                # 8年まで行った変種のあとも、宣言済み10回は最後まで回す（1点差分の地図）
                pass
        md += ["", f"{fam} の8年: {eight_note}", ""]

    greens = [x for x in all_rows if x.get("green")]
    md += [
        "## まとめ",
        "",
        f"- 1年で決済EV黒（n≥100）: **{len(greens)} / {len(all_rows)}**",
        f"- 8年まで進んだ: **{sum(1 for x in all_rows if x.get('eight'))}**",
        "",
        "合否は formal の実データのみ。1年が赤の変種に8年は回していない。",
        "",
    ]
    out = Path("eval/reports/20260825-adv-cycles")
    Path(out.with_suffix(".json")).write_text(
        json.dumps(all_rows, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    Path(str(out) + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[-12:]), flush=True)


if __name__ == "__main__":
    main()

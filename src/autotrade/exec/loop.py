"""Demo loop: same SH-01 signals as eval, testnet orders optional.

One slot: only ``order_logic`` may send orders. The other rest filter is
always evaluated and written to the log (shadow).
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from autotrade.data.binance_vision import BinanceVisionClient, ensure_binance_data
from autotrade.data.bybit import BybitPublicClient, ensure_data
from autotrade.exec.bybit_private import BybitPrivateClient
from autotrade.exec.secrets import assert_demo_only, load_bybit_env, protect_from_commit
from autotrade.exec.signals import Intent, intent_for_bar, last_complete_bar
from autotrade.exec.sizing import qty_fixed_margin, stop_take_prices
from autotrade.strategy.slow import prepare_slow

LOGICS_BOTH = ("sh01n_regime_50d", "sh01n_regime_100d")


@dataclass
class DemoConfig:
    symbol: str
    category: str
    logics: list[str]
    order_logic: str
    warmup_days: int
    leverage: float
    margin_per_trade: float
    risk_per_trade_usdt: float
    kill_file: str
    log_path: str
    secrets_path: str
    public_base_url: str


def load_demo_config(path: str | Path) -> DemoConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    logics = list(raw.get("logics") or list(LOGICS_BOTH))
    order = raw.get("order_logic") or logics[0]
    if order not in logics:
        raise SystemExit(f"order_logic {order} is not in logics {logics}")
    return DemoConfig(
        symbol=raw.get("symbol", "BTCUSDT"),
        category=raw.get("category", "linear"),
        logics=logics,
        order_logic=order,
        warmup_days=int(raw.get("warmup_days", 400)),
        leverage=float(raw.get("leverage", 3)),
        margin_per_trade=float(raw.get("margin_per_trade", 30)),
        risk_per_trade_usdt=float(raw.get("risk_per_trade_usdt", 3)),
        kill_file=raw.get("kill_file", "secrets/demo/KILL"),
        log_path=raw.get("log_path", "artifacts/demo/demo.jsonl"),
        secrets_path=raw.get("secrets_path", "secrets/demo/bybit.txt"),
        public_base_url=raw.get("public_base_url", "https://api.bybit.com"),
    )


def _append_log(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event.setdefault("ts", datetime.now(timezone.utc).isoformat())
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")


def _killed(path: str) -> bool:
    return Path(path).exists()


def seconds_until_next_15m_close(*, extra: float = 5.0, now: pd.Timestamp | None = None) -> float:
    now = now or pd.Timestamp.now(tz="UTC")
    nxt = now.floor("15min") + pd.Timedelta(minutes=15)
    return max(1.0, (nxt - now).total_seconds() + extra)


def load_warmup_15m(
    cfg: DemoConfig,
    *,
    prefer: str,
    cache_dir: Path,
) -> tuple[pd.DataFrame, str]:
    end = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")
    start = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=cfg.warmup_days)).strftime("%Y-%m-%d")
    if prefer == "bybit":
        try:
            client = BybitPublicClient(base_url=cfg.public_base_url)
            df = ensure_data(
                client,
                symbol=cfg.symbol,
                category=cfg.category,
                interval="15m",
                start=start,
                end=end,
                cache_dir=cache_dir,
                force=False,
            )
            return df, "bybit"
        except Exception as exc:  # noqa: BLE001
            print(f"Bybit public klines failed ({exc}); trying Binance Vision for dry-run.", flush=True)
    vision = BinanceVisionClient()
    df = ensure_binance_data(
        vision,
        symbol=cfg.symbol,
        interval="15m",
        start=start,
        end=end,
        cache_dir=cache_dir,
        force=False,
    )
    return df, "binance_vision"


def intents_now(
    m15: pd.DataFrame,
    logics: list[str],
    positions: dict[str, str | None],
    now: pd.Timestamp,
) -> dict[str, Intent]:
    out: dict[str, Intent] = {}
    for logic_id in logics:
        prepared = prepare_slow(logic_id, m15, None)
        row = last_complete_bar(prepared, now)
        out[logic_id] = intent_for_bar(logic_id, row, position_side=positions.get(logic_id))
    return out


def _fmt_qty(qty: float, step: float) -> str:
    if step >= 1:
        return str(int(qty))
    decimals = max(0, str(step)[::-1].find("."))
    return f"{qty:.{decimals}f}"


def run_cycle(
    cfg: DemoConfig,
    *,
    submit: bool,
    data_source: str,
    now: pd.Timestamp | None = None,
    m15: pd.DataFrame | None = None,
    source_label: str | None = None,
    private: BybitPrivateClient | None = None,
    paper: dict[str, str | None] | None = None,
) -> dict:
    now = now or pd.Timestamp.now(tz="UTC")
    log_path = Path(cfg.log_path)
    if _killed(cfg.kill_file):
        event = {"event": "killed", "kill_file": cfg.kill_file}
        _append_log(log_path, event)
        return event

    if m15 is None:
        m15, source_label = load_warmup_15m(
            cfg, prefer=data_source, cache_dir=Path("data/cache")
        )
    source_label = source_label or data_source
    paper = paper if paper is not None else {lid: None for lid in cfg.logics}

    intents = intents_now(m15, cfg.logics, paper, now)
    event: dict = {
        "event": "cycle",
        "source": source_label,
        "submit": submit,
        "order_logic": cfg.order_logic,
        "bar": str(intents[cfg.order_logic].bar_time),
        "intents": {k: asdict(v) for k, v in intents.items()},
    }

    if submit and source_label != "bybit":
        event["submit_blocked"] = "orders require Bybit klines, not Vision"
        submit = False

    order_intent = intents[cfg.order_logic]
    qty_step, min_qty = 0.001, 0.001
    if submit and private is not None:
        info = private.instruments(cfg.symbol, cfg.category)
        lot = info.get("lotSizeFilter") or {}
        qty_step = float(lot.get("qtyStep") or 0.001)
        min_qty = float(lot.get("minOrderQty") or qty_step)
        private.set_leverage(cfg.symbol, cfg.leverage, cfg.category)
        exch = private.position(cfg.symbol, cfg.category)
        exch_side = None
        if exch:
            exch_side = "long" if exch.get("side") == "Buy" else "short"
        paper_side = paper[cfg.order_logic]
        if (exch_side or None) != (paper_side or None) and not (
            exch_side is None and paper_side is None
        ):
            event["mismatch"] = {"exchange": exch_side, "paper": paper_side}
            event["event"] = "position_mismatch"
            _append_log(log_path, event)
            return event

    action = order_intent.action
    if action.startswith("enter_") and order_intent.stop_pct:
        side = "long" if action == "enter_long" else "short"
        fill = order_intent.close
        qty = qty_fixed_margin(
            fill,
            order_intent.stop_pct,
            risk_usdt=cfg.risk_per_trade_usdt,
            margin=cfg.margin_per_trade,
            leverage=cfg.leverage,
            qty_step=qty_step,
            min_qty=min_qty,
        )
        event["qty"] = qty
        if qty <= 0:
            event["skip"] = "qty_too_small"
        elif submit and private is not None:
            stop, tp = stop_take_prices(side, fill, order_intent.stop_pct, order_intent.tp_pct)
            resp = private.market_order(
                symbol=cfg.symbol, side=side, qty=_fmt_qty(qty, qty_step)
            )
            event["order"] = resp.get("result")
            try:
                private.set_trading_stop(symbol=cfg.symbol, stop=stop, take_profit=tp)
            except Exception as exc:  # noqa: BLE001
                event["trading_stop_error"] = str(exc)
            paper[cfg.order_logic] = side
        else:
            paper[cfg.order_logic] = side
            event["paper_fill"] = True
    elif action.startswith("exit_"):
        if submit and private is not None and paper.get(cfg.order_logic):
            side = paper[cfg.order_logic]
            exch = private.position(cfg.symbol, cfg.category)
            qty_s = str(exch["size"]) if exch else "0"
            if float(qty_s) > 0:
                resp = private.market_order(
                    symbol=cfg.symbol,
                    side=side or "long",
                    qty=qty_s,
                    reduce_only=True,
                )
                event["order"] = resp.get("result")
            paper[cfg.order_logic] = None
        else:
            paper[cfg.order_logic] = None
            event["paper_exit"] = True

    for lid, intent in intents.items():
        if lid == cfg.order_logic:
            continue
        if intent.action.startswith("enter_"):
            paper[lid] = "long" if intent.action == "enter_long" else "short"
        elif intent.action.startswith("exit_"):
            paper[lid] = None

    event["paper"] = paper
    _append_log(log_path, event)
    return event


def run_demo(
    config_path: str,
    *,
    submit: bool = False,
    once: bool = False,
    order_logic: str | None = None,
    data_source: str = "bybit",
    poll_seconds: float = 15.0,
) -> int:
    cfg = load_demo_config(config_path)
    if order_logic:
        cfg.order_logic = order_logic
        if order_logic not in cfg.logics:
            cfg.logics = [order_logic, *[x for x in cfg.logics if x != order_logic]]

    creds = None
    private = None
    if submit:
        creds = load_bybit_env(cfg.secrets_path)
        protect_from_commit(creds.path)
        assert_demo_only(creds)
        if not creds.has_keys:
            raise SystemExit(
                f"{creds.path} に API キーがありません。"
                "左の一覧で secrets/demo/bybit.txt を開き、"
                "キーなしなら --submit を付けずに dry-run してください。"
            )
        private = BybitPrivateClient(creds)

    paper_path = Path("artifacts/demo/state.json")
    if paper_path.exists():
        paper = json.loads(paper_path.read_text(encoding="utf-8"))
        for lid in cfg.logics:
            paper.setdefault(lid, None)
    else:
        paper = {lid: None for lid in cfg.logics}
    print(
        f"demo logics={cfg.logics} order={cfg.order_logic} "
        f"submit={submit} source={data_source}",
        flush=True,
    )
    while True:
        event = run_cycle(
            cfg,
            submit=submit,
            data_source=data_source,
            private=private,
            paper=paper,
        )
        paper_path.parent.mkdir(parents=True, exist_ok=True)
        paper_path.write_text(json.dumps(paper, indent=2), encoding="utf-8")
        print(json.dumps({k: event[k] for k in event if k != "intents"}, default=str), flush=True)
        if event.get("event") in {"killed", "position_mismatch"}:
            return 2
        if once:
            return 0
        time.sleep(seconds_until_next_15m_close(extra=max(5.0, poll_seconds)))

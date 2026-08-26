"""Binance USDⓈ-M futures derivative datasets from the public archive.

Provides the non-price feeds the EH-01..EH-10 hypotheses need:

- ``metrics``      open interest, top-trader / all-account long-short ratios,
                   taker buy-sell volume ratio (5-minute samples, daily files)
- ``fundingRate``  realised funding (8-hourly, monthly files)
- ``premiumIndex`` perp premium vs index (1-hour klines, monthly files)
- ``perp klines``  futures OHLCV incl. taker buy volume (monthly files)

Alignment is deliberately conservative: every series is reduced to the 15m
execution grid using only samples that were already published when the 15m bar
closed. See ``align_to_15m``.
"""

from __future__ import annotations

import io
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import httpx
import pandas as pd

ARCHIVE_BASE = "https://data.binance.vision/data"

METRIC_COLUMNS = [
    "oi",
    "oi_value",
    "tt_count_ratio",
    "tt_ratio",
    "acct_ratio",
    "taker_ratio",
]


def _daterange(start: str, end: str) -> list[pd.Timestamp]:
    return list(pd.date_range(start=start, end=end, freq="D", tz="UTC"))


def _monthrange(start: str, end: str) -> list[pd.Timestamp]:
    first = pd.Timestamp(start, tz="UTC").normalize().replace(day=1)
    last = pd.Timestamp(end, tz="UTC").normalize().replace(day=1)
    return list(pd.date_range(start=first, end=last, freq="MS", tz="UTC"))


_TRANSIENT_ATTEMPTS = 4
_MISSING_PASSES = 2


def _get_zip_csv(client: httpx.Client, url: str) -> pd.DataFrame | None:
    """Download one archive zip and return its single CSV, or None on 404.

    Transient answers -- a dropped connection, 429, 5xx -- are retried with
    backoff. A 404 is returned as-is; deciding whether to believe it is
    :func:`_fetch_many`'s job, because that decision depends on how many other
    days came back 404 at the same time.
    """
    last_error: Exception | None = None
    for attempt in range(_TRANSIENT_ATTEMPTS):
        if attempt:
            time.sleep(2.0**attempt)
        try:
            resp = client.get(url)
        except httpx.HTTPError as exc:
            last_error = exc
            continue
        if resp.status_code == 404:
            return None
        if resp.status_code == 429 or resp.status_code >= 500:
            last_error = httpx.HTTPStatusError(
                f"{resp.status_code} for {url}", request=resp.request, response=resp
            )
            continue
        resp.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            name = zf.namelist()[0]
            with zf.open(name) as fh:
                raw = fh.read()
        text = raw.decode("utf-8")
        first = text.split("\n", 1)[0].split(",")[0].strip()
        has_header = not (
            first.isdigit() or first.replace("-", "").replace(":", "").replace(" ", "").isdigit()
        )
        return pd.read_csv(io.StringIO(text), header=0 if has_header else None)

    raise RuntimeError(f"could not download {url}") from last_error


def _fetch_many(
    urls: list[str], *, workers: int = 12, timeout: float = 60.0
) -> tuple[list[pd.DataFrame], list[str]]:
    """Return the archives that downloaded, and the URLs that were not there.

    404s get a second pass. Under load the host occasionally reports 404 for a
    file that is there, and a day dropped that way is indistinguishable from a
    day the exchange never published -- the frame just comes back quietly
    shorter. One extra sweep of the misses is enough to tell the two apart, and
    unlike retrying each 404 in place it stays cheap when the whole requested
    span predates the archive.
    """
    out: list[pd.DataFrame] = []
    pending = list(urls)
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for _ in range(_MISSING_PASSES):
                if not pending:
                    break
                still: list[str] = []
                for url, df in zip(pending, pool.map(lambda u: _get_zip_csv(client, u), pending)):
                    if df is None or df.empty:
                        still.append(url)
                    else:
                        out.append(df)
                pending = still
    return out, pending


# ---------------------------------------------------------------- metrics


def fetch_metrics(symbol: str, start: str, end: str) -> pd.DataFrame:
    urls = [
        f"{ARCHIVE_BASE}/futures/um/daily/metrics/{symbol}/{symbol}-metrics-{d:%Y-%m-%d}.zip"
        for d in _daterange(start, end)
    ]
    parts, missing = _fetch_many(urls)
    if not parts:
        return pd.DataFrame(columns=METRIC_COLUMNS)
    df = pd.concat(parts, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["create_time"], utc=True)
    df = df.rename(
        columns={
            "sum_open_interest": "oi",
            "sum_open_interest_value": "oi_value",
            "count_toptrader_long_short_ratio": "tt_count_ratio",
            "sum_toptrader_long_short_ratio": "tt_ratio",
            "count_long_short_ratio": "acct_ratio",
            "sum_taker_long_short_vol_ratio": "taker_ratio",
        }
    )
    df = df[["timestamp", *METRIC_COLUMNS]].astype({c: float for c in METRIC_COLUMNS})
    out = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").set_index("timestamp")
    out.attrs["missing_sources"] = missing
    return out


# ---------------------------------------------------------------- funding


def fetch_funding(symbol: str, start: str, end: str) -> pd.DataFrame:
    urls = [
        f"{ARCHIVE_BASE}/futures/um/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{m:%Y-%m}.zip"
        for m in _monthrange(start, end)
    ]
    parts, missing = _fetch_many(urls, workers=6)
    if not parts:
        return pd.DataFrame(columns=["funding_rate"])
    df = pd.concat(parts, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["calc_time"].astype("int64"), unit="ms", utc=True)
    df["funding_rate"] = df["last_funding_rate"].astype(float)
    df = df[["timestamp", "funding_rate"]]
    out = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").set_index("timestamp")
    out.attrs["missing_sources"] = missing
    return out


# ---------------------------------------------------------------- premium index

_KLINE_COLS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
    "ignore",
]


def _parse_klines(parts: list[pd.DataFrame]) -> pd.DataFrame:
    # The archive is not consistent: older months ship headerless CSVs while
    # newer ones carry a header row. Normalise each part before concatenating,
    # otherwise the two layouts stack side by side instead of end to end.
    normalised = []
    for part in parts:
        if not (isinstance(part.columns[0], str) and part.columns[0] == "open_time"):
            part = part.copy()
            part.columns = _KLINE_COLS[: len(part.columns)]
        normalised.append(part)
    df = pd.concat(normalised, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["open_time"].astype("int64"), unit="ms", utc=True)
    return df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").set_index("timestamp")


def fetch_premium_index(symbol: str, start: str, end: str, interval: str = "1h") -> pd.DataFrame:
    urls = [
        f"{ARCHIVE_BASE}/futures/um/monthly/premiumIndexKlines/{symbol}/{interval}/"
        f"{symbol}-{interval}-{m:%Y-%m}.zip"
        for m in _monthrange(start, end)
    ]
    parts, missing = _fetch_many(urls, workers=6)
    if not parts:
        return pd.DataFrame(columns=["premium"])
    df = _parse_klines(parts)
    out = pd.DataFrame({"premium": df["close"].astype(float)})
    out.attrs["missing_sources"] = missing
    return out


# ---------------------------------------------------------------- perp klines


def fetch_perp_klines(symbol: str, start: str, end: str, interval: str = "15m") -> pd.DataFrame:
    urls = [
        f"{ARCHIVE_BASE}/futures/um/monthly/klines/{symbol}/{interval}/"
        f"{symbol}-{interval}-{m:%Y-%m}.zip"
        for m in _monthrange(start, end)
    ]
    parts, missing = _fetch_many(urls, workers=6)
    if not parts:
        return pd.DataFrame(columns=["perp_close", "perp_volume", "perp_taker_buy"])
    df = _parse_klines(parts)
    out = pd.DataFrame(
        {
            "perp_close": df["close"].astype(float),
            "perp_volume": df["volume"].astype(float),
            "perp_taker_buy": df["taker_buy_volume"].astype(float),
        }
    )
    out.attrs["missing_sources"] = missing
    return out


# ---------------------------------------------------------------- cache


KINDS = ("metrics", "funding", "premium", "perp15m")


def cache_path(cache_dir: Path, symbol: str, kind: str, start: str, end: str) -> Path:
    return Path(cache_dir) / f"{symbol}_binance_um_{kind}_{start}_{end}.csv"


def ensure_derivative(
    *,
    symbol: str,
    kind: str,
    start: str,
    end: str,
    cache_dir: str | Path,
    force: bool = False,
) -> pd.DataFrame:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_path(cache_dir, symbol, kind, start, end)
    if path.exists() and not force:
        df = pd.read_csv(path, parse_dates=["timestamp"])
        return df.set_index("timestamp").sort_index()

    if kind == "metrics":
        df = fetch_metrics(symbol, start, end)
    elif kind == "funding":
        df = fetch_funding(symbol, start, end)
    elif kind == "premium":
        df = fetch_premium_index(symbol, start, end)
    elif kind == "perp15m":
        df = fetch_perp_klines(symbol, start, end)
    else:
        raise ValueError(f"unknown derivative kind: {kind}")

    if df.empty:
        raise RuntimeError(f"no {kind} data fetched for {symbol} {start}..{end}")

    # Archives the exchange never published are a fact of the data; the point of
    # naming them is that a rerun which quietly loses more of them cannot pass
    # itself off as the same dataset.
    missing = df.attrs.get("missing_sources") or []
    if missing:
        print(
            f"    {kind} {symbol}: {len(missing)} archive(s) absent, "
            f"first={missing[0].rsplit('/', 1)[-1]}",
            flush=True,
        )

    df.index.name = "timestamp"
    df.to_csv(path)
    return df


# ---------------------------------------------------------------- alignment


@dataclass
class DerivContext:
    """Derivative feeds reduced to the 15m execution grid (no lookahead)."""

    frame: pd.DataFrame
    symbol: str
    start: str
    end: str

    def __contains__(self, col: str) -> bool:
        return col in self.frame.columns


def align_to_15m(
    m15_index: pd.DatetimeIndex,
    *,
    metrics: pd.DataFrame,
    funding: pd.DataFrame,
    premium: pd.DataFrame,
    perp: pd.DataFrame,
) -> pd.DataFrame:
    """Reduce every feed onto the 15m grid using only already-published samples.

    - metrics (5m): aggregated over ``[t, t+15m)`` — complete at bar t close
    - funding (8h): last rate settled at or before bar open
    - premium (1h): hour close shifted a full hour so the hour is complete
    - perp (15m):   same grid; bar t close is known at bar t close
    """
    idx = pd.DatetimeIndex(pd.to_datetime(m15_index, utc=True)).as_unit("ns").sort_values()
    out = pd.DataFrame(index=idx)

    if not metrics.empty:
        metrics = metrics.copy()
        metrics.index = pd.DatetimeIndex(metrics.index).as_unit("ns")
        agg = metrics.resample("15min", label="left", closed="left").agg(
            {
                "oi": "last",
                "oi_value": "last",
                "tt_count_ratio": "mean",
                "tt_ratio": "mean",
                "acct_ratio": "mean",
                "taker_ratio": "mean",
            }
        )
        for col in METRIC_COLUMNS:
            out[col] = agg[col].reindex(idx)

    if not funding.empty:
        # Archive stamps drift by a millisecond, so snap settlements to the grid.
        f = funding.copy()
        f.index = pd.DatetimeIndex(f.index).as_unit("ns").floor("15min")
        f = f[~f.index.duplicated(keep="last")].sort_index()
        out["funding_rate"] = (
            pd.merge_asof(
                pd.DataFrame(index=idx).reset_index(names="timestamp"),
                f.reset_index(names="timestamp"),
                on="timestamp",
                direction="backward",
            )
            .set_index("timestamp")["funding_rate"]
            .reindex(idx)
        )
        settle = pd.Series(0.0, index=idx)
        hits = idx.intersection(f.index)
        if len(hits):
            settle.loc[hits] = f.loc[hits, "funding_rate"].astype(float).values
        out["funding_pay_rate"] = settle

    if not premium.empty:
        prem = premium["premium"].astype(float).sort_index()
        prem.index = pd.DatetimeIndex(prem.index).as_unit("ns") + pd.Timedelta(hours=2)
        out["premium"] = prem.reindex(idx, method="ffill")

    if not perp.empty:
        perp = perp.copy()
        perp.index = pd.DatetimeIndex(perp.index).as_unit("ns")
        for col in ("perp_close", "perp_volume", "perp_taker_buy"):
            if col in perp.columns:
                out[col] = perp[col].astype(float).reindex(idx)

    return out


def load_context(
    m15_index: pd.DatetimeIndex,
    *,
    symbol: str,
    start: str,
    end: str,
    cache_dir: str | Path = "data/cache",
    force: bool = False,
) -> DerivContext:
    metrics = ensure_derivative(
        symbol=symbol, kind="metrics", start=start, end=end, cache_dir=cache_dir, force=force
    )
    funding = ensure_derivative(
        symbol=symbol, kind="funding", start=start, end=end, cache_dir=cache_dir, force=force
    )
    premium = ensure_derivative(
        symbol=symbol, kind="premium", start=start, end=end, cache_dir=cache_dir, force=force
    )
    perp = ensure_derivative(
        symbol=symbol, kind="perp15m", start=start, end=end, cache_dir=cache_dir, force=force
    )
    frame = align_to_15m(
        m15_index, metrics=metrics, funding=funding, premium=premium, perp=perp
    )
    return DerivContext(frame=frame, symbol=symbol, start=start, end=end)

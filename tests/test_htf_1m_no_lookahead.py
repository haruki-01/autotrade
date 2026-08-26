"""上位足は確定するまで 1分足に載せない。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from autotrade.strategy.bracket import (
    _align_completed_htf,
    _completed_htf,
    _resample_ohlc,
    sig_htf15_bull_brk,
)


def _bars(n: int, close: np.ndarray) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="1min", tz="UTC")
    open_ = np.full(n, 100.0)
    return pd.DataFrame(
        {
            "open": open_,
            "high": np.maximum(open_, close),
            "low": np.minimum(open_, close) - 0.1,
            "close": close,
            "volume": 1.0,
        },
        index=idx,
    )


def test_15m_close_hidden_until_bar_completes() -> None:
    close = np.full(20, 100.0)
    close[14] = 130.0  # 00:14 で初めて 15分足 [00:00, 00:15) が確定
    df = _bars(20, close)
    htf = _resample_ohlc(df, "15min")
    aligned = _align_completed_htf(df, htf, 15)
    assert pd.isna(aligned["close"].iloc[13]) or aligned["close"].iloc[13] != 130.0
    assert aligned["close"].iloc[14] == 130.0


def test_break_does_not_see_same_bar_spike_early() -> None:
    close = np.full(40, 100.0)
    close[14] = 120.0
    df = _bars(40, close)
    a = _completed_htf(df, 15)
    # 00:13 時点では直前15分高値も陽線も未確定
    assert not bool(a["bull"].fillna(0).iloc[13] > 0.5)
    sig = sig_htf15_bull_brk(df, {})
    assert sig.values[13] == 0


if __name__ == "__main__":
    test_15m_close_hidden_until_bar_completes()
    test_break_does_not_see_same_bar_spike_early()
    print("ok")

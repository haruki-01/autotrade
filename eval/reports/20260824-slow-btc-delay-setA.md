# SH-01 slow pack — Set A

銘柄: BTCUSDT  ／  ロジック 3 本  ／  min_trades=100（全銘柄合計）, max_dd=20.0%, risk=3.0 USDT/trade

実行環境: python 3.12.3 / pandas 2.2.3 / numpy 2.4.4 / lock eval_v3_btc.lock.yaml@bcc5efaffb3e

| logic | ノブ | n | EV | 勝率 | DD | 総リターン | 判定 |
|-------|------|---|----|------|----|-----------|------|
| `sh01_tp_4atr` | 利確4ATR | 56 | +1.951 | 48.2% | 2.8% | +36.4% | FAIL |
| `sh01_tp4_delay_1h` | 反証: 3期間PASS版を1時間遅らせる | 58 | +2.002 | 48.3% | 3.1% | +38.7% | FAIL |
| `sh01_tp4_delay_1d` | 反証: 3期間PASS版を1日遅らせる | 60 | +1.257 | 38.3% | 5.1% | +25.1% | FAIL |

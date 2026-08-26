# SH-01 slow pack — Set A

銘柄: BTCUSDT  ／  ロジック 14 本  ／  min_trades=100（全銘柄合計）, max_dd=20.0%, risk=3.0 USDT/trade, 最低 50 エントリー/月

実行環境: python 3.12.3 / pandas 2.2.3 / numpy 2.4.4 / lock eval_v3_btc.lock.yaml@e7bcbe449cbb

| logic | ノブ | n | 月あたり | EV | 勝率 | DD | 総リターン | 判定 | 落ちた条件 |
|-------|------|---|---------|----|------|----|-----------|------|-----------|
| `sh01n_center` | 中心: 利確4ATR | 56 | 1.8 | +1.951 | 48.2% | 2.8% | +36.4% | FAIL | min_trades, trade_rate |
| `sh01n_tp_2` | 利確2ATR | 75 | 2.4 | +0.594 | 52.0% | 3.8% | +14.8% | FAIL | min_trades, trade_rate |
| `sh01n_tp_3` | 利確3ATR | 63 | 2.0 | +1.047 | 47.6% | 3.2% | +22.0% | FAIL | min_trades, trade_rate |
| `sh01n_tp_5` | 利確5ATR | 53 | 1.7 | +2.085 | 43.4% | 3.0% | +36.8% | FAIL | min_trades, trade_rate |
| `sh01n_tp_6` | 利確6ATR | 46 | 1.5 | +2.819 | 45.7% | 3.1% | +43.2% | FAIL | min_trades, trade_rate |
| `sh01n_tp_8` | 利確8ATR | 41 | 1.3 | +3.588 | 46.3% | 3.4% | +49.0% | FAIL | min_trades, trade_rate |
| `sh01n_entry_15d` | 入口15日 | 61 | 2.0 | +1.766 | 45.9% | 3.8% | +35.9% | FAIL | min_trades, trade_rate |
| `sh01n_entry_25d` | 入口25日 | 52 | 1.7 | +1.897 | 48.1% | 4.9% | +32.9% | FAIL | min_trades, trade_rate |
| `sh01n_entry_30d` | 入口30日 | 47 | 1.5 | +1.978 | 48.9% | 4.1% | +31.0% | FAIL | min_trades, trade_rate |
| `sh01n_exit_7d` | 退出7日 | 56 | 1.8 | +1.766 | 46.4% | 2.4% | +33.0% | FAIL | min_trades, trade_rate |
| `sh01n_exit_15d` | 退出15日 | 56 | 1.8 | +1.784 | 44.6% | 3.0% | +33.3% | FAIL | min_trades, trade_rate |
| `sh01n_stop_1p25` | 損切1.25日足ATR | 59 | 1.9 | +1.964 | 44.1% | 3.5% | +38.6% | FAIL | min_trades, trade_rate |
| `sh01n_stop_1p75` | 損切1.75日足ATR | 55 | 1.8 | +1.641 | 49.1% | 2.8% | +30.1% | FAIL | min_trades, trade_rate |
| `sh01n_stop_2p0` | 損切2.0日足ATR | 53 | 1.7 | +1.594 | 50.9% | 2.7% | +28.2% | FAIL | min_trades, trade_rate |

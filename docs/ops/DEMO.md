# Demo（Bybit testnet）

SH-01 の 50日 / 100日休む条件を、バックテストと同じシグナルで testnet に載せる。

**1枠なので注文は1本だけ。** 既定は 100日が注文、50日は影ログ。`--order-logic` で入れ替え。

## 起動

```bash
# キーなし。シグナルとサイズだけ（注文しない）
PYTHONPATH=src python3 -m autotrade.cli demo --once

# 常駐（まだ注文しない）
PYTHONPATH=src python3 -m autotrade.cli demo

# testnet に成行を出す（左の一覧の secrets/demo/bybit.txt にキー）
PYTHONPATH=src python3 -m autotrade.cli secrets-init
# bybit.txt を開いて KEY / SECRET を記入。BYBIT_BASE_URL は testnet のまま
PYTHONPATH=src python3 -m autotrade.cli demo --submit --order-logic sh01n_regime_100d
```

止める: `touch secrets/demo/KILL`（次のサイクルで停止）

キーは **`secrets/demo/bybit.txt`** に書く（左のフォルダ一覧から開く）。`.example` や `bybit.env` は使わない。

ログ: `artifacts/demo/demo.jsonl`

live キーは拒否する。`--submit` と Vision 足の組み合わせも拒否する（研究データと本番の差を混ぜない）。

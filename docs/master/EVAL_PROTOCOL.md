# 検証・評価プロトコル（Formal Eval）

**合否の正本は [CURRENT.md](./CURRENT.md)。** 合成 smoke は対象外。

## 1. 環境

現行の SH-01 経路:

| 要素 | 場所 |
|------|------|
| 固定数値 | `configs/eval_v3_btc.yaml` |
| データ指紋 | `eval/locks/eval_v3_btc.lock.yaml` |
| ランナー | `scripts/run_slow_pack.py --campaign ev-dd` |

初期の 15m 族（H01 など）は `configs/eval_v1.yaml` のまま記録用。新しい合否に使わない。

| 共通 | 場所 |
|------|------|
| 手順 | `eval/README.md` |
| エージェント技能 | `.cursor/skills/backtest-eval/SKILL.md` |

## 2. データ

- **必須:** 過去の実市場 OHLCV
- **優先:** Bybit BTCUSDT linear
- **フォールバック:** Binance Vision（Bybit 不通時）。実データだが銘柄定義が違うため、live 前に Bybit 再確認
- **禁止:** synthetic（乱数足）

## 3. 数値の一致

コスト・口座は v1 から変えない（fee 5.5bps/side、slip 2bps/side、lev 3、証拠金 30、元本 300）。

合否の読み方は CURRENT: 費用後EV>0 と DD≤20%。n<100 は判定保留。月50は非ゲート。

手順の精緻版: [../hypothesis/craft/VALIDATION_FLOW.md](../hypothesis/craft/VALIDATION_FLOW.md)

## 4. コマンド

```bash
PYTHONPATH=src python3 -m autotrade.cli eval-prepare --config configs/eval_v1.yaml
PYTHONPATH=src python3 -m autotrade.cli eval --logic-id <logic_id>
```

## 5. 関連

- [BACKTEST_DESIGN.md](./BACKTEST_DESIGN.md)
- [eval/README.md](../../eval/README.md)

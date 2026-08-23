# 検証・評価プロトコル（Formal Eval）

**合否の正本。** 合成 smoke は対象外。

## 1. 環境

| 要素 | 場所 |
|------|------|
| 固定数値（コスト・期間・ゲート） | `configs/eval_v1.yaml` |
| データ指紋 | `eval/locks/eval_v1.lock.yaml` |
| 手順 | `eval/README.md` |
| エージェント技能 | `.cursor/skills/backtest-eval/SKILL.md` |

## 2. データ

- **必須:** 過去の実市場 OHLCV
- **優先:** Bybit BTCUSDT linear
- **フォールバック:** Binance Vision（Bybit 不通時）。実データだが銘柄定義が違うため、live 前に Bybit 再確認
- **禁止:** synthetic（乱数足）

## 3. 数値の一致

実装・検証で同じ値を使う（`configs/eval_v1.yaml` / eval_v1.1）:

- fee 5.5bps/side、slip 2bps/side、lev 3
- サイジング: 証拠金 $30 / リスク $3（fixed_margin）、初期資金 $300
- Set B = 本検証、Set C = holdout
- ゲート: 期待値>0 / トレード≥100 / DD≤20%

手順の精緻版: [../hypothesis/craft/VALIDATION_FLOW.md](../hypothesis/craft/VALIDATION_FLOW.md)

## 4. コマンド

```bash
PYTHONPATH=src python3 -m autotrade.cli eval-prepare --config configs/eval_v1.yaml
PYTHONPATH=src python3 -m autotrade.cli eval --logic-id <logic_id>
```

## 5. 関連

- [BACKTEST_DESIGN.md](./BACKTEST_DESIGN.md)
- [eval/README.md](../../eval/README.md)

---
name: backtest-eval
description: >-
  Runs formal backtest verification and evaluation for autotrade strategies on
  real historical market data with locked costs and config. Use when the user
  asks for 検証, 評価, eval, formal backtest, Set B gate, hypothesis validation,
  or reproducible performance assessment. Never use synthetic smoke for pass/fail.
---

# Formal Backtest Eval（検証・評価）

合否の読み方: `docs/master/CURRENT.md`。合成 smoke は対象外。

現行（SH-01）: `configs/eval_v3_btc.yaml` + `eval/locks/eval_v3_btc.lock.yaml` + `--campaign ev-dd`。  
初期15m族の記録用が `eval_v1`。新しい合否に eval_v1 のゲート文言だけを使わない。

## 用語（必ず区別する）

| 用語 | 意味 | 合否 |
|------|------|------|
| **synthetic smoke** | 乱数の偽足。コード動作確認のみ | **使わない** |
| **formal eval** | 実市場の過去データ + 現行 lock の固定数値 | **唯一の合否** |

ユーザーが「検証」「評価」と言ったら **formal eval のみ**。`--synthetic` は禁止。

## 環境の正本

SH-01（現行）:

1. 数値: `configs/eval_v3_btc.yaml`
2. データ指紋: `eval/locks/eval_v3_btc.lock.yaml`
3. 読み方: `docs/master/CURRENT.md`

コスト・資金・レバを変えるなら `eval_version` を上げて lock 再生成。合否の解釈だけ変えるときは CURRENT を先に直す。

## 必須ワークフロー

```
Task Progress:
- [ ] 1. Lock 確認 / なければ eval-prepare
- [ ] 2. validate（synthetic 混入なし・hash 一致）
- [ ] 3. formal eval 実行（logic-id 指定）
- [ ] 4. research + workstream に蓄積
- [ ] 5. レポートで PASS/FAIL を明示
```

### Step 1 — 環境準備

```bash
PYTHONPATH=src python3 -m autotrade.cli eval-prepare --config configs/eval_v1.yaml
```

- Bybit 優先。403 なら Binance Vision を lock に記録（実データ）。
- Vision 使用時はレポートに「live 前に Bybit 再確認」と書く。
- `eval/locks/eval_v1.lock.yaml` が無ければ **評価を始めない**。

### Step 2 — 本検証

```bash
PYTHONPATH=src python3 -m autotrade.cli eval --logic-id <logic_id>
# 複数: --logic-id a,b,c
# holdout: --set C （B合格後のみ）
```

禁止:
- `--synthetic`
- lock なしの合否判定
- Set B を見て同期間パラメータを再最適化
- smoke 結果を PASS 扱い

### Step 3 — 蓄積

実行後に確認・更新:
- `docs/research/`（自動）
- `docs/workstreams/<id>/README.md` と `LATEST.md`
- `eval/reports/*.md`

### Step 4 — 判定の伝え方

春希向けに短く:
1. **Gate PASS/FAIL**（Set B）
2. データソース（bybit / binance_vision）
3. 期待値・DD・トレード数
4. 次アクション（1点だけ）

## ゲート（変更禁止）

Set B（BT-1）:
- 平均トレード損益 > 0
- トレード数 ≥ 100
- 最大 DD ≤ 20%

詳細は [reference.md](reference.md)。

---
id: HYP-002
title: E1 ブレイク追随 Long-only v2（証拠準拠）
status: in_eval
primary_distortion: E1
created: 2026-08-22
updated: 2026-08-22
parent: HYP-001
logic_id: donchian_20_10_long_v2
---

# E1 ブレイク追随 Long-only v2

## 実装

- logic_id: `donchian_20_10_long_v2`
- workstream: `docs/workstreams/HYP-002-e1-breakout-long-v2/`
- サイジング: 証拠金 $30 × レバ3、リスク $3（`configs/eval_v1.yaml` / [SIZING.md](../craft/SIZING.md)）

## Formal eval Set B（eval_v1.1）

| 項目 | 値 |
|------|-----|
| Gate | **FAIL**（トレード数 6 < 100） |
| 期待値 | **+$5.92** / trade ✅ |
| DD | **1.8%** ✅ |
| リターン | +11.8%（$300 → $335） |
| 勝率 | 33%（正の歪度と整合） |
| データ | binance_vision |

## 解釈

方向・費用後EV・DDは良い。**サンプル不足で不合格**（棄却条件の「判定保留」に該当）。  
次の1点変更は「nを増やす」設計に限定（別カード）。現行 v2 のパラメータ探索はしない。

## チェックリスト

実装・eval 済み。status → 結果反映後 `fail`（ゲート）だが構造棄却ではない。

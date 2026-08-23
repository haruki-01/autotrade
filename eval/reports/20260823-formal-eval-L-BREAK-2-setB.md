# Formal Eval 追記 — L-BREAK-2 Set B（2026-08-23）

親バッチ: [20260822-formal-eval-batch-setB.md](./20260822-formal-eval-batch-setB.md)

## 変更点（1点）

| 項目 | L-BREAK | L-BREAK-2 |
|------|---------|-----------|
| logic_id | `donchian_20_10_v1` | `donchian_h4_20_10_v1` |
| シグナル足 | 日足 Donchian 20/10 | **4H** Donchian 20/10 |
| その他 | — | 同一（両建て・ATR stop・構造退出） |

## 結果

| 仮説 | Gate | 期待値 | DD | トレード | リターン |
|------|------|--------|-----|----------|----------|
| L-BREAK | FAIL* | +54.3† | 3.8% | 13 | +7.0%† |
| **L-BREAK-2** | **FAIL*** | **+0.85** | **3.8%** | **58** | **+15.5%** |

\* 期待値・DDはクリア、回数不足。  
† 親ランは当時 equity 10k スケール。L-BREAK-2 は `eval_v1.1`（equity 300 / fixed_margin）。**期待値の絶対額は直接比較しない**。符号と DD・n の比較が本体。

**結論:** サンプルは 13→58 と改善したが ≥100 未達。デモ/本番には進まない。  
低回転トレンド系と `min_trades=100` の相性を別途整理する。パラメータ縮小による n 稼ぎはしない。

## 成果物

- Report: `eval/reports/20260823T004451Z_donchian_h4_20_10_v1_setB.md`
- Artifacts: `artifacts/evals/20260823T004451Z_setB_donchian_h4_20_10_v1`
- Workstream: `docs/workstreams/L-BREAK-2-donchian-h4/`

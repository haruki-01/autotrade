# Postmortem — Formal Eval Batch Set B（2026-08-22）

## 何を試したか

H01 / L-COST / L-MOM-VOL / L-BREAK / H21 を `eval_v1`・Vision 実足・2024年で formal eval。

## 結果

5本すべて Gate FAIL。詳細: [`eval/reports/20260822-formal-eval-batch-setB.md`](../../eval/reports/20260822-formal-eval-batch-setB.md)

## 構造的学び（再発防止）

| 学び | 型 | 次にどう使うか |
|------|-----|----------------|
| 押し目＋固定利確は E1 と矛盾し E8 に負ける | AP4/AP5 | 同ファミリー再探索禁止 |
| 「費用ゲートを足す」だけではエッジにならない | — | エントリーの質が本体 |
| ATRトレール＋緩い執行 = 過回転で破産級DD | — | 執行頻度を先に設計する |
| Donchian は EV+だが n不足 | — | 証拠→1点変更でサンプル設計 |
| 測定器は正しい。入力仮説が弱い | メタ | 証拠ファーストへ制度変更 |

## メタ敗因

**歪みの証拠なしに複数ロジックを実装した。**  
精度向上の本体は実装速度ではなく、棄却の速さと仮説カードの質。

## アクション

- [x] 仮説ラボ開設
- [x] E1 証拠タスク（[`../evidence/E1-breakout-forward-returns.md`](../evidence/E1-breakout-forward-returns.md)）
- [x] HYP-002 ready（Long-only v2）
- [ ] HYP-002 実装 → formal eval

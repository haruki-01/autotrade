# 仮説ラボ（Hypothesis Lab）

**目的:** 「勝てる仮説」を作る・棄却する・学ぶサイクルを、実装や BT ログから切り離して蓄積する。

Formal eval（`eval/`）は合否の測定器。ここは **仮説の質そのもの** の工場。

```text
docs/hypothesis/
  README.md           ← 本ファイル
  PLAN.md             ← 精度向上の最上位プラン（必読）
  craft/              ← 仮説の立て方ナレッジ（再利用する型）
  inventory/          ← 仮説カード（候補・進行中・棄却）
  postmortems/        ← 検証後の敗因・学び
  evidence/           ← 歪みの根拠メモ（文献・統計の要約）
```

## 読む順

0. プロジェクトの「いま」→ [../master/CURRENT.md](../master/CURRENT.md)
1. [FLOW.md](./FLOW.md) · [craft/THREE_LAYER_MODEL.md](./craft/THREE_LAYER_MODEL.md)
2. **[craft/TRADE_SPOT_HYPOTHESIS.md](./craft/TRADE_SPOT_HYPOTHESIS.md)** — トレードスポット仮説の考え方
3. [spots/](./spots/) — ①のストック
4. [craft/CREATION_FLOW.md](./craft/CREATION_FLOW.md) / [VALIDATION_FLOW.md](./craft/VALIDATION_FLOW.md) — ②③
5. [inventory/](./inventory/) — ②ロジックカード

## 他フォルダとの役割分担

| 場所 | 役割 |
|------|------|
| `docs/hypothesis/` | **仮説の精度・型・学び**（本ラボ） |
| `docs/master/MARKET_EDGE_MAP.md` | 歪みの最上位前提 |
| `docs/workstreams/` | 実装済みロジックの進捗 |
| `docs/research/` | BT ランの機械可読ログ |
| `eval/` | Formal eval 環境・合否 |

## 原則（短く）

- インジの組み合わせ ≠ 仮説
- 1仮説 = 1主歪み + 誰が損するか + 棄却条件
- FAIL も資産。棄却理由を `postmortems/` に残す
- Set B を見て同期間を再最適化しない

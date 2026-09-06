# Agent Rules — 仮想通貨自動売買 Bot 検証

本プロジェクトの Cursor / Cloud Agent 常時ルール。

## 目的

**バックテスト利益最大化ではない。**  
未知データに対して再現性のある期待値を持つ戦略を発見すること。

## 評価優先順位

1. OOS（VALIDATION）で執行 EV > 0 が残るか
2. Walk Forward / Monte Carlo で過学習でないか
3. maxDD に対して収益が十分か
4. PF / Sharpe（診断指標）
5. 手数料・Slippage 込み（執行二列）
6. 月次 P（**結果**。Research Loop の最適化目標にしない）

## 二層 Gate

| 層 | 用途 | 指標 |
|---|---|---|
| **Research Gate** | promote / Paper 移行判断 | EV, PF, WF, MC, Robustness |
| **Business Gate** | 実運用 KPI | Gate1（EV+N）, Gate2（月次 P≥¥1,500） |

## Test データ神聖化

- **TEST**（2026-03-01..2026-08-31）= OOS2 相当
- 戦略開発・パラメータ調整に **使用禁止**
- Gate2 候補の最終 1 回判定のみ
- 既存バッチ（P1-NR, P3-B-NR）で TEST 参照済み → legacy contamination。以降の iter は VALIDATION のみ

## AI がやってよいこと

- 仮説生成、特徴量分析コード、バックテストコード
- 統計分析、可視化、Strategy 比較
- Research Report 生成

## AI が勝手にやってはいけないこと

- TEST データを使ったパラメータ最適化
- 結果を見て都合よくルール変更
- 評価基準・手数料条件・検証期間の変更（変更時は Research Log 必須）
- 月次 P 最大化を目的としたパラメータ探索

## 必須記録

すべての Experiment について [knowledge-log.md](docs/research/knowledge-log.md) に:

- Hypothesis, Data Range, Parameters, Result, Decision

## 正本ドキュメント

- L0 制約: [docs/SPEC.md](docs/SPEC.md)
- 検証運用: [docs/research/verification-workflow.md](docs/research/verification-workflow.md)
- 新検証レイヤー: [docs/research/validation-spec.md](docs/research/validation-spec.md)

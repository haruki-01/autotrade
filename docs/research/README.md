# リサーチ成果物（仕様書とは分離）

このディレクトリは **仮説カタログ・検証フロー・検証シート・ナレッジ** を置く場所です。

| 文書 | 役割 | 更新方針 |
|---|---|---|
| [`../SPEC.md`](../SPEC.md) | BTC プロジェクト正本（Layer2 MP-CRYPTO-5M） | 構造変更時のみ |
| [`independence-strategy.md`](independence-strategy.md) | **独立・二層ポートフォリオ戦略正本** | 目標・配分変更時 |
| [`gate-by-market.md`](gate-by-market.md) | 市場別 Gate 基準 | 新 Market Profile 追加時 |
| [`market-selection-sheet.csv`](market-selection-sheet.csv) | 7 軸市場評価シート | 市場追加・再評価時 |
| [`../../AGENTS.md`](../../AGENTS.md) | Cursor / Agent 常時ルール | 運用ルール変更時 |
| [`validation-spec.md`](validation-spec.md) | Research Gate / WF / MC / MFE/MAE 正本 | 検証レイヤー変更時 |
| [`edge-catalog.md`](edge-catalog.md) | エッジ仮説の網羅カタログ | 仮説の追加・棄却・Phase移動で更新 |
| [`verification-workflow.md`](verification-workflow.md) | 検証バッチの進め方・評価・spawn ルール | 運用改善時のみ更新 |
| [`verification-roadmap.md`](verification-roadmap.md) | PM マスター計画・バッチキュー | バッチ完了時 |
| [`future-plan.md`](future-plan.md) | 今後の検証フロー・優先順 | フェーズ完了時 |
| [`knowledge-log.md`](knowledge-log.md) | バッチごとの Knowledge Card 蓄積 | 検証のたびに追記 |
| [`strategy-registry.md`](strategy-registry.md) | 全戦略 lifecycle | V1/Paper 更新時 |

## 検証シート

| シート | 対象バッチ |
|---|---|
| [`phase0-verification-sheet.csv`](phase0-verification-sheet.csv) | B01–B09 |
| [`phase1-verification-sheet.csv`](phase1-verification-sheet.csv) | P1-A〜P1-NR |
| [`validation-verification-sheet.csv`](validation-verification-sheet.csv) | **V1, B10, P3-C** |
| [`paper-verification-sheet.csv`](paper-verification-sheet.csv) | PT-A/B |

## 読む順序

0. [independence-strategy.md](independence-strategy.md) — **独立目的・Layer 配分・市場選定**
1. [edge-catalog.md](edge-catalog.md) — 何を検証するか
2. [verification-workflow.md](verification-workflow.md) — どう進めるか
3. [validation-spec.md](validation-spec.md) — Research Gate / データ分割ルール
4. [future-plan.md](future-plan.md) — 今後の流れ
5. [knowledge-log.md](knowledge-log.md) — 結果の蓄積

## Phase の意味

| Phase | 内容 |
|---|---|
| **0** | トレードしない。記述統計で歪みの有無 |
| **1** | OHLCV でロジック化。理論値／執行込み二列 |
| **1+** | V1: Walk Forward + Monte Carlo + Research Gate |
| **2** | 板・清算等、追加データが必要 |
| **Paper** | フォワード sim。Gate1 再現 + Gate2 |

## 二層 Gate（2026-09-06〜）

| 層 | 指標 | 用途 |
|---|---|---|
| Research Gate | EV, PF, WF, MC | promote / Paper |
| Gate1 / Gate2 | EV+N, 月次 P | ビジネス KPI |

定数は SPEC を参照。

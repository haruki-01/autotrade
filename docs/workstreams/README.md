# Workstreams — 小プロジェクト

1ロジック（または1調査テーマ）= 1フォルダ。  
マスター方針は触らず、**その要素のリサーチと進捗**だけをここに溜める。

## 一覧

| ID | フォルダ | ステータス | 一言 |
|----|----------|------------|------|
| H01 | [H01-mtf-ema-pullback](./H01-mtf-ema-pullback/) | formal FAIL | 比較用。費用負け |
| L-COST | [L-COST-cost-gate](./L-COST-cost-gate/) | formal FAIL | H01より悪化 |
| L-MOM-VOL | [L-MOM-VOL-vol-scaled](./L-MOM-VOL-vol-scaled/) | formal FAIL | DD壊滅 |
| L-BREAK | [L-BREAK-donchian](./L-BREAK-donchian/) | formal FAIL* | EV+だが n=13 |
| H21 | [H21-donchian-long-only](./H21-donchian-long-only/) | formal FAIL* | EV+だが n=8 |
| HYP-002 | [HYP-002-e1-breakout-long-v2](./HYP-002-e1-breakout-long-v2/) | formal FAIL* | EV+・DD良・n=6（サイジング$30/$3） |
| HYP-009 | [HYP-009-d001-fake-rebreak](./HYP-009-d001-fake-rebreak/) | formal FAIL | D-001 実証① n=1 |
| HYP-010 | [HYP-010-d001-fake-retest](./HYP-010-d001-fake-retest/) | formal FAIL | D-001 実証② n=1 |
| L-BRACKET | [L-BRACKET-12h-1m](./L-BRACKET-12h-1m/) | 打ち止め | 12h入口 1年決済EV黒0。合否軸はEV+DDへ |
| SH-01 | [SH-01-daily-trend](./SH-01-daily-trend/) | EV+DD PASS | サンプルは期間ごと保留。Set C は買い持ちに負ける |

\* 期待値・DDはクリア、トレード数不足で不合格。一括レポート: [eval/reports/20260822-formal-eval-batch-setB.md](../eval/reports/20260822-formal-eval-batch-setB.md) · D/Rバッチ: [eval/reports/20260822-formal-eval-d001-r001-setB.md](../eval/reports/20260822-formal-eval-d001-r001-setB.md)


## フォルダの中身

```text
workstreams/<id>/
  README.md     ← 目的・現状・次アクション（エージェントが更新）
  LATEST.md     ← 最新BTラン要約（CLIが自動上書き）
  notes/        ← リサーチメモ・調査メモ（日付付き推奨）
```

検証ランの数値の正本は `docs/research/`。`LATEST.md` は該当 workstream へのショートカット。

## 新規作成

1. `_template/` をコピーして `workstreams/<LOGIC_ID>-<slug>/` にする
2. README の表を更新
3. マスターの優先バッチ（`HYPOTHESIS_CATALOG.md`）と矛盾しないか確認

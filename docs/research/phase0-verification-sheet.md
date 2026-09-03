# Phase0 検証シート（閲覧用）

記入の正本は `phase0-verification-sheet.csv`。  
定義: `phase0-stats.md` / 運用: `verification-workflow.md` / 蓄積: `knowledge-log.md`

**B01 完了**（2024-01-01..2026-08-31, GMO BTC_JPY 5m）。詳細は `data/phase0/b01_results.json` と `knowledge-log.md` KB-B01-20260903。

## B01 結果サマリ

| metric_id | verdict | mean_edge | n |
|---|---|---|---|
| P0-HE-RET | weak | 0.000194 | 975 |
| P0-HE-VS | pass | 0.000351 | 975 |
| P0-HE-VOL | fail | -0.001198 | 11675 |
| P0-HE-DIR | fail | 0.000194 | 975 |
| P0-HE-PREPOST | weak | -0.000132 | 974 |
| P0-HC4-WDWE | pass | 0.000040 | 276706 |
| P0-HC4-FAKEBRK | pass | — | 1122 |
| P0-HC-RET | weak | 0.000046 | 276706 |
| P0-HC-VOL | weak | 0.090759 | 276718 |
| P0-HC-TREND | weak | -0.008294 | 276718 |
| P0-HC-REVERT | weak | -0.000275 | 871 |

batch_verdict: **conditional**

改訂: 2026-09-03

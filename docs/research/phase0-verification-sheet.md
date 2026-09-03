# Phase0 検証シート（閲覧用）

記入の正本は `phase0-verification-sheet.csv`。  
定義: `phase0-stats.md` / 運用: `verification-workflow.md` / 蓄積: `knowledge-log.md`  
**Phase0 完了**: B01–B07（2024-01-01..2026-08-31, GMO BTC_JPY 5m）。総括: [phase0-summary.md](phase0-summary.md)

## バッチ batch_verdict 一覧

| batch | batch_verdict | 主仮説 |
|---|---|---|
| B01 | conditional | H-E, H-C, H-C4 |
| B02 | promote | H-A2（H-A reject） |
| B03 | conditional | H-B |
| B04 | reject | H-B2, H-B3 |
| B05 | reject | H-F1 |
| B06 | conditional | H-D（PULL 優位） |
| B07 | conditional | 稀イベント（単体候補なし） |

## B02 結果サマリ

| metric_id | verdict | mean_edge | n |
|---|---|---|---|
| P0-HA-REVERT | fail | -0.000118 | 4692 |
| P0-HA-CONT | pass | +0.000118 | 4692 |
| P0-HA-REVERT15 | fail | ≈0 | 4693 |
| P0-HA-PATH | pass | revert_first 81% | 4692 |
| P0-HA-BY-SESS | fail | -0.000192 (WD) | 3570 |

## B06 ハイライト（PULL vs RAW）

| metric_id | verdict | mean_edge | n |
|---|---|---|---|
| P0-HD-RAW | weak | +0.000088 | 8126 |
| P0-HD-PULL | pass | +0.002436 | 8125 |

改訂: 2026-09-03

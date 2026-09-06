# V1 検証レポート — Research Gate

生成: 2026-09-06  
バッチ: V1（Walk Forward + Monte Carlo + Robustness）

---

## エグゼクティブサマリー

| 戦略 | Research Gate | Gate1 | Gate2 | 執行 OOS P |
|---|---|:---:|:---:|---:|
| **H-D + H-M4** | **pass** | Y | N | ≈¥741 |
| **H-F3 (cd4_q40_at20)** | **pass** | N (N=33) | N | ≈¥234 |

**要点**: 両候補とも Research Gate pass — 統計的に信頼できる edge あり。Gate2 未到達は EV 厚み × N の問題。

---

## H-D + H-M4

| 指標 | 値 |
|---|---:|
| EV | ¥15.3 |
| P | ¥741 |
| PF | 1.64 |
| Sharpe | 4.83 |
| maxDD | ¥696 |
| WF pass rate | 100% (3/3) |
| MC p95 DD | ¥1,053 |
| MC ruin | 0% |

**判断**: Research Gate pass → Paper 継続可。Gate2 は EV 不足（必要 ¥50 vs 実績 ¥15）。

---

## H-F3 (cd4_q40_at20)

| 指標 | 値 |
|---|---:|
| EV | ¥7.1 |
| P | ¥234 |
| PF | 1.53 |
| Sharpe | 3.01 |
| maxDD | ¥573 |
| N/mo | 33.1 |
| WF pass rate | 100% (3/3) |
| MC p95 DD | ¥752 |

**判断**: Research Gate pass だが Gate1 fail（N 帯 40–60 未達）。N 拡大 or 合成で P 改善を検討。

---

## 次アクション

1. H-D: Paper 継続（Research Gate 確認済み）
2. H-F3: N 帯改善 or P3-C 合成結果を参照
3. B10 MFE/MAE で Exit 再設計候補を評価

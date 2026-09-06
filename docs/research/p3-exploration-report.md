# P3 H-F2 検証レポート

生成: 2026-09-06
サンプル: 2024-01-01..2026-08-31

## サマリー

| batch | verdict | 主要結果 |
|---|---|---|
| **B08** Phase0 | conditional | MID edge 弱正（vs CONT 優位）、ABSREV pass |
| **P3-A** Phase1 | **reject** | 全 split 執行 EV 負。preflight 符号不一致 warn |

**結論**: H-F2 中点回帰は Phase0 記述統計では CONT より優位だが、**RR 1:2 執行込みでは再現せず**。Gate2 候補から外す。次は **B09（H-F3 レンジ回帰）** を Phase0 から検討。

---

## B08 Phase0

| metric | n | mean_edge | hit_rate | verdict |
|---|---:|---:|---:|---|
| P0-HF2-MID | 41,119 | +0.0095% | 51.2% | weak |
| P0-HF2-ABSREV | 41,122 | +0.106% | 70.2% | pass |
| P0-HF2-CONT | 41,117 | −0.0094% | 48.9% | fail |

- MID vs CONT diff = +0.019% → 回帰方向の優位は確認
- 頻度 ≈1,287 shocks/月 — **検出が緩くイベント過多**（cooldown で N 帯調整は Phase1 側）

---

## P3-A Phase1

cooldown=48、RR 1:2、R=1.0%×ATR0.5、H-M4

| split | 執行P | W | N/mo | Gate1 |
|---|---:|---:|---:|:---:|
| IS | −¥278 | 45.7% | 52.6 | N |
| OOS1 | −¥27 | 47.7% | 53.0 | N |
| OOS2 | −¥211 | 49.1% | 55.6 | N |
| CONT 対照 | −¥328 | 43.0% | 52.9 | N |

### Preflight

- signal_count: pass（2,423 signals）
- **sign_parity: warn** — P0 mean=+0.0001 vs P1 theory EV=−0.39

→ 5 段パイプラインの preflight が Phase0→Phase1 非再現を事前警告。

---

## 次アクション

1. H-F2 MID: **reject**（確定）
2. **H-F3**: P3-B-NR（N 拡大 research loop）— 最優先
3. H-D + H-M4: hold（Gate1 最良候補）
4. 全体: [project-review.md](project-review.md) / [future-plan.md](future-plan.md)

---

## B09 Phase0 — H-F3 レンジ回帰

| metric | n | mean_edge | hit_rate | verdict |
|---|---:|---:|---:|---|
| P0-HF3-EDGE | 5,294 | **+0.096%** | **64.1%** | **pass** |
| P0-HF3-BREAK | 5,294 | −0.096% | 35.9% | fail |
| P0-HF3-EV | — | \|edge\|=0.24% | — | weak |

- batch_verdict: **promote** — Phase0 では H-F2/H-B より明確な優位
- 頻度 ≈166 events/月

---

## P3-B Phase1 — H-F3 執行込み

cooldown=12、RR 1:2、H-M4

| split | 執行P | W | N/mo | Gate1 |
|---|---:|---:|---:|:---:|
| IS | ¥120 | 59.5% | 12.9 | N |
| OOS1 | ¥11 | 58.7% | 7.9 | N |
| **OOS2** | **¥261** | **71.4%** | 14.0 | N |
| BREAK 対照 | −¥222 | 30.3% | 12.2 | N |

- batch_verdict: **reject**（Gate1 fail — **N 帯不足**が主因）
- preflight **sign_parity pass** — Phase0→Phase1 符号一致（H-F2 とは対照的）
- OOS2: 執行 EV=+¥18.7、W=71% → **edge は存在**、頻度設計がボトルネック

**判断**: H-F3 は **conditional（N 拡大 research loop へ）**。reject ではなく次フェーズ P3-B-NR 対象。

---

## 更新後の結論

| 仮説 | Phase0 | Phase1 | 次 |
|---|---|---|---|
| H-F2 | conditional | reject | 停止 |
| **H-F3** | **promote** | **N 不足 conditional** | **P3-B-NR** |

改訂: 2026-09-06（B09/P3-B 追加）（B09/P3-B H-F3 追加）

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

1. H-F2 MID エントリー: **reject**（Phase1）
2. VOL_SHOCK 定義の厳格化（rv spike のみ等）を B08-R で検討 optional
3. **B09 H-F3**（レンジ内回帰）Phase0 を次バッチに選定
4. H-D + H-M4 は引き続き hold（Gate1 最良候補）

改訂: 2026-09-06

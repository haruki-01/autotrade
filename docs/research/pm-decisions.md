# PM 判断ログ

Product Manager（春希）の正式判断を記録する正本。エージェントは本ファイルの **active** セクションに従う。

---

## PM-20260906 — 検証方針の確定

**日付**: 2026-09-06  
**背景**: P1-R2C（H-D canonical）、Gate2@3% 再ベースライン、P1-L レバー検証完了後

### 判断一覧

| # | 論点 | PM 判断 | 状態 |
|---|---|---|---|
| 1 | Gate2@3%（¥1,500/月）を L0 正式版とする | **Yes** | **active** |
| 2 | H-D canonical 固定・tuning 停止 | **Yes** | **active** |
| 3 | sim Paper（PT-B）継続、live paper 禁止 | **Yes（推奨採用）** | **active** |
| 4 | 次の主戦場 = 新 L1 探索（H-D 系は hold） | **Yes** | **active** |
| 5 | 棄却確定リストをクローズ | **Yes（推奨採用）** | **active** |

### 1. Gate2@3%

- **L0**: 月次 P ≥ ¥1,500（= +3% × BR ¥50,000）
- **EV***: ¥30/回（N=50）
- **旧基準**: +5% / ¥2,500（2026-09-06 まで、参考のみ）
- **正本**: [SPEC.md](../SPEC.md) §2.3、[gate2_rescore_3pct.json](../../data/research/gate2_rescore_3pct.json)

### 2. H-D canonical（tuning 停止）

| 項目 | 固定値 |
|---|---|
| Exit | sl=0.5%, tp=1.0% |
| cooldown | 48 本 |
| max_bars | 48 |
| フィルタ | H-M4（土日停止） |
| mode | pull（初押し待ち） |

- P1-R / P1-R2 / P1-L 以降の **H-D パラメータ探索は禁止**
- Research Gate pass + P1-R2C 全 split Gate1 を根拠に **hold**

### 3. Paper Trade（推奨理由付き）

**推奨: sim Paper（PT-B）継続、live paper 禁止**

| 方式 | 判断 | 理由 |
|---|---|---|
| **sim Paper（PT-B）** | **継続** | monitoring_status=continue。Gate1 再現。コストゼロ |
| **GMO live paper** | **禁止** | Gate2 候補ゼロ。API・運用コストに見合わない |
| **少額 Live** | **禁止** | 同上 |

**運用**: 月初 1 回 `python3 -m scripts.paper.run_pt PT-B` → KB 追記

### 4. 次の主戦場 — 新 L1

- H-D / H-F3 / P3 合成の **新規 tuning 禁止**
- **新メカニズム L1** を Phase0→Phase1 で探索
- **次 L1 候補**: **H-D4**（％水準ブレイク継続、Phase0 weak）
- ~~H-C2~~: P2-E reject → closed

### 5. 棄却クローズ（推奨理由付き）

**推奨: Yes — 正式クローズ**

再探索禁止リスト（edge-catalog に反映）:

| ID / 施策 | 理由 |
|---|---|
| H-A, H-A2 | Phase0/1 reject |
| H-B | L1 全 reject |
| H-F2, H-F4 | Phase0/1 reject |
| H-A revert（P1-HA） | EV 負 |
| P3-C-R | zone 厳格化劣化 |
| H-C session × H-D | P1-L reject |
| H-E fee 窓 × H-D | P1-L reject |
| H-D パラメータ tuning | P1-L 限界 |

---

## ゲート早見（active）

| ゲート | 基準 | 本番移行 |
|---|---|---|
| Research Gate | V1 pass | Paper 移行判断可 |
| Gate1 | EV>0, N=40–60/月 | 取引可能 edge |
| Gate2 | P≥¥1,500/月 OOS | **必須**（未到達なら本番不可） |

---

改訂: 2026-09-06

# 市場別 Gate 基準

| 項目 | 内容 |
|---|---|
| 目的 | 市場ごとに realistic な N 帯・目標 P・合格ラインを定義 |
| 上位 | [independence-strategy.md](independence-strategy.md) |
| BTC 正本 | [SPEC.md](../SPEC.md)（Layer 2 satellite として維持） |

---

## 1. なぜ Gate を分けるか

| 問題 | 例 |
|---|---|
| 同一 N 帯 | H-C2 週1回 → N≈4/月 なのに Gate1 40–60 を要求 |
| 同一月次 P% | スイング 5 回/月で +3%/月 は 1 回 +¥300 必要 |
| 同一執行モデル | 株式は寄付板・PTS、crypto は 24h fill |

→ **Market Profile** ごとに Gate を定義し、横比較は「独立への寄与」で行う。

---

## 2. Market Profile 一覧

| profile_id | 市場 | 時間足 | 典型 N/月 | Layer |
|---|---|---|---:|---|
| **MP-CRYPTO-5M** | BTC/JPY GMO | 5m | 40–60 | 2 |
| **MP-ETF-D1** | 米 ETF（SPY/QQQ/VT） | 日足 | 5–20 | 2 |
| **MP-JP-SWING** | 日本株 | 日足 | 5–15 | 2 |
| **MP-INDEX-L1** | NISA インデックス | 月次 | 0.2–1 | 1 |

---

## 3. 共通 Gate（全 Market Profile）

### Research Gate（統計品質 — 変更なし）

[validation-spec.md](validation-spec.md) 参照。

| チェック | 基準 |
|---|---|
| 執行 EV | > 0（VALIDATION） |
| PF | ≥ 1.15 |
| maxDD | ≤ 15% of BR |
| WF pass rate | ≥ 60% |
| MC ruin | ≤ 5% |

### Integrity Gate（検証品質）

| チェック | 基準 |
|---|---|
| preflight | pass |
| TEST ロック | tuning は VALIDATION のみ |
| Knowledge Card | 必須 |

---

## 4. Market Gate（ビジネス — 市場別）

### MP-CRYPTO-5M（現行 BTC — SPEC 互換）

| Gate | 条件 | 備考 |
|---|---|---|
| Gate1 | EV > 0 **かつ** N ∈ [40, 60]/月 | SPEC §2.3 |
| Gate2 | P ≥ ¥1,500/月 OOS 平均 | +3% × BR ¥50k |
| EV* | ¥30/回（N=50） | |

**現状**: Gate1 pass（H-D）、Gate2 **fail**。

### MP-ETF-D1（Layer 2 第一候補）

| Gate | 条件 | 備考 |
|---|---|---|
| Gate1 | EV > 0 **かつ** N ∈ [4, 20]/月 | 日足スイング |
| Gate2 | P ≥ **+1.0%/月 × B** OOS 平均 | 年利 12% 相当 |
| Gate2（BR ¥50k） | P ≥ **¥500/月** | crypto Gate2 より現実的 |
| EV* | P / N（N≈10 なら ¥50/回） | |
| 追加 | ベンチマーク buy&hold 超過 | 3 年 OOS で +2%/年 以上 |

執行モデル（仮置き）:

| 項目 | 仮定 |
|---|---|
| 約定 | 翌日始値 ± 0.05% slip |
| 手数料 | 0.1%/往復（米証券） |
| 時間 | RTH のみ |

### MP-JP-SWING

| Gate | 条件 | 備考 |
|---|---|---|
| Gate1 | EV > 0 **かつ** N ∈ [3, 15]/月 | 100 株単位 |
| Gate2 | P ≥ **+0.8%/月 × B** | NISA 外 research 口座 |
| Gate2（BR ¥50k） | P ≥ **¥400/月** | |
| 追加 | 最大 DD < 10% BR | 単元制約で集中リスク |

### MP-INDEX-L1（Layer 1 本体）

| Gate | 条件 | 備考 |
|---|---|---|
| Gate1 | ベンチマーク対比 | 年率 ±1% 以内 |
| Gate2 | **税引後** 複利 ≥ 7%/年 | 独立の主 KPI |
| Gate3 | リバランスコスト < 0.2%/年 | |
| DD | < 20% | 人生目標 §3 連動 |

**algo 合格ライン不要** — インデックス + 機械リバランスが基本。

---

## 5. Gate 换算表（比較用）

BR = ¥50,000 固定 Q 前提。Layer 2 横比較用。

| Profile | Gate2 月次 P | 月利 | 年利換算 | N 帯 | 1 回 EV* |
|---|---:|---:|---:|---:|---:|
| MP-CRYPTO-5M | ¥1,500 | 3.0% | 36%+ | 40–60 | ¥30 |
| MP-ETF-D1 | ¥500 | 1.0% | 12% | 4–20 | ¥50–125 |
| MP-JP-SWING | ¥400 | 0.8% | 10% | 3–15 | ¥27–133 |
| MP-INDEX-L1 | — | 0.58%/月 | 7% | — | — |

→ crypto Gate2 は **Layer 2 内でも最も厳しい**。未達は「市場が悪い」より「目標と N の組み合わせが厳しい」。

---

## 6. promote / live 判断（統一）

| 段階 | 条件 |
|---|---|
| **Paper 移行** | Research Gate pass + Market Gate1 pass |
| **Gate2 合格** | Market Gate2 pass（profile 別） |
| **live 許可** | Gate2 × 3 ヶ月 forward + Layer 2 配分内 |
| **Layer 1 統合** | 2 年 OOS + 税引後で MP-INDEX Gate2 超 |

---

## 7. 既存 BTC 検証の再解釈

| 指標 | MP-CRYPTO-5M | MP-ETF-D1 換算 |
|---|---|---|
| H-D VALIDATION P ≈ ¥1,031 | Gate2 の 69% | Gate2 の **206%** ✓ |
| H-D TEST P ≈ ¥727 | Gate2 の 48% | Gate2 の **145%** ✓ |
| N ≈ 50/月 | Gate1 ✓ | N 帯超過（要 cooldown 調整） |

→ **同じ H-D edge を日足 ETF に移植した場合、Gate2 達成可能性は相対的に高い**（要再検証・執行モデル変更）。

---

改訂: 2026-09-06

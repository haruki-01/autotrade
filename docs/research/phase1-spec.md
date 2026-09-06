# Phase1 検証仕様

Phase0 候補の **取引可能エッジ** を RR・執行込み・OOS で評価する正本。  
資金・N・合格基準の L0 は [SPEC.md](../SPEC.md)。Phase0 結果は [phase0-summary.md](phase0-summary.md)。

**サンプル**: GMO Coin `BTC_JPY` 5m、2024-01-01..2026-08-31  
**建玉想定**: Q = ¥10,000 / トレード（SPEC §2）

---

## 1. 検証バッチ

| batch_id | 主仮説 | 問い | 実行順 |
|---|---|---|---|
| **P1-A** | H-D | RSI + 初押し待ちは RR 1:2・執行込みで Gate1 pass か？ | 1 |
| **P1-B** | H-A2 | SPIKE 継続は執行込みでも Phase0 promote が再現するか？ | 2 |
| **P1-C** | 合成 | P1-A/B pass 候補 + H-M4 を合成して Gate1/2 を満たすか？ | 3（ゲート付き） |
| **P1-R** | H-D + H-M4 | SL/TP 幅グリッドで Gate2（月次 P≥¥2,500 = 5% of BR）到達可能か？ | 4（P1-C 後） |
| **P1-R2** | H-D + H-M4 | 固定 TP/SL grid（VALIDATION のみ）で Exit 効率改善するか？ | 4b（B10 後） |
| **P1-R2C** | H-D + H-M4 | P1-R2 best config を **固定** して TRAIN/VAL/TEST で再現するか？ | 4c（P1-R2 後） |
| **P1-N** | H-D + H-M4 | N=10/20/50/100 各帯で必要 EV/W* を満たすか？ | 5（PT-A 後） |

---

## 2. 葉ルール

### 2.1 H-D（P1-A / canonical）

| 項目 | 定義 |
|---|---|
| トリガー | RSI14 ≤ 30 後、RSI > 30 に復帰（`RSI_EXIT_OS`） |
| エントリー | トリガー後 **12 本以内** の pull low 確定 bar で **long**（初押し待ち） |
| 禁止 | トリガー bar 即入り（RAW） |
| **SL / TP（canonical）** | **固定 pct: SL = 0.5%, TP = 1.0%**（effective RR 1:2）。H-M4 ON |
| SL / TP（legacy P1-A） | `max(0.008 × entry, 0.5 × ATR14)` 幅の R ベース RR 1:2 — **P1-A 再現用のみ** |
| 時間切れ | 48 本（h240） |
| クールダウン | 前回シグナルから 48 本 |
| フィルタ | H-M4: 土日新規停止（canonical では **常時 ON**） |

**canonical 確定根拠**: P1-R2 VALIDATION best（sl=0.5%, tp=1.0%）→ P1-R2C で TRAIN/VAL/TEST 固定検証。  
コード定数: `HD_CANONICAL_SL_PCT` / `HD_CANONICAL_TP_PCT`（`scripts/phase1/common.py`）。

### 2.2 H-A2（P1-B）

| 項目 | 定義 |
|---|---|
| トリガー | Phase0 `is_spike` 確定 |
| エントリー | SPIKE bar close、`spike_dir` 方向 |
| SL / TP | 0.3×ATR 逆行 / 0.6×ATR 同方向（RR 1:2） |
| 時間切れ | 12 本（h60） |
| クールダウン | 12 本 |
| 対照 | 回帰方向（H-A）、ランダムエントリー |

### 2.3 合成（P1-C）

| 項目 | 定義 |
|---|---|
| シグナル | Gate1 pass した H-D / H-A2。同一 bar 冲突時 **SPIKE 優先** |
| H-M4 | 土日新規停止 ON |
| H-M5 | 起点 +1.5% 超の遅入禁止（IGNITE 系、P1-C のみ参考） |

### 2.4 再検証（P1-R）

| 項目 | 定義 |
|---|---|
| 対象 | P1-C conditional（H-D + H-M4） |
| グリッド | `pct_risk` × `atr_mult` × `max_bars` × `cooldown` |
| pct_risk | 0.008, 0.012, 0.016, 0.020, 0.025, 0.030 |
| atr_mult | 0.5, 1.0, 1.5 |
| max_bars | 48, 96 |
| cooldown | 48, 96 |
| 手法 | 理論値全組み合わせスクリーニング → 上位15を執行込み再検証 |
| 選定 | OOS 平均 P 最大かつ Gate1/2 優先 |

### 2.5 固定 Exit 確認（P1-R2C）

| 項目 | 定義 |
|---|---|
| 対象 | P1-R2 VALIDATION best（**sl=0.5%, tp=1.0%**） |
| 分割 | TRAIN / VALIDATION / TEST 各 1 回（**tuning 禁止**） |
| Research Gate | VALIDATION のみ再計測（config は P1-R2 で確定済み） |
| 判定 | TEST で Gate1 pass + EV>0 → Paper 継続。Gate2 は TEST の **結果** として記録 |

### 2.6 H-C2 週明けギャップ（P2-E / L1 探索）

| 項目 | 定義 |
|---|---|
| トリガー | 週初 **最初の月曜 5m bar**（金曜終値→月曜 open の gap） |
| エントリー | 月曜 open、gap 方向（**cont**） |
| 対照 | gap 逆方向（**revert**） |
| SL / TP | 固定 pct: SL = 0.5%, TP = 1.0%（H-D canonical 同等） |
| 時間切れ | 48 本（h240） |
| 頻度 | ≈1 回/週（**Gate1 N 帯 40–60/月 は構造的に未到達**） |
| 探索 | `min_gap` フィルタ（0.5%, 1.0%, TRAIN p75）は VALIDATION のみ |

コード: `scripts/phase1/signals/h_c2_gap.py`, `scripts/phase1/p2e_hc2_gap.py`

---

## 3. 執行モデル（SPEC §7.3 仮置き）

| 項目 | ルール |
|---|---|
| 理論値 | シグナル価格どおり約定 |
| 指値エントリー fill | 70%（未約定は見送り） |
| 成行 / 時間切れ決済 Slip | 0.02%（不利方向） |
| 利確指値 fill | 85%（未達は時間切れ成行 + Slip） |
| 取引手数料 | 0%（GMO 取引所レバレッジ想定） |
| レバ手数料 | 建玉 × 0.04%/日（JST 6:00 またぎ 1 回） |
| 損益 | `PnL = Q × ret_pct − costs`（円） |

---

## 4. Phase1 指標（必須出力）

| 指標 | 定義 |
|---|---|
| N | 月間トレード数 |
| W | 勝率（PnL > 0） |
| EV | 1 トレードあたり期待損益（円） |
| P | 月間純利益 ≈ EV × N |
| maxDD | 累積損益の最大ドローダウン（円） |
| 劣化率 | 執行込み EV / 理論 EV |
| random_W | 同期間ランダムエントリー勝率（seed=42, 200 trials 平均） |
| fee_breakeven_W | RR 1:2 + コスト込み損益分岐勝率 |
| **PF** | Profit Factor（Hybrid Validation 以降） |
| **Sharpe** | トレード単位 Sharpe（Hybrid Validation 以降） |
| **MFE / MAE** | 最大有利/不利 excursion（B10 以降） |

**二列必須**: 理論値 / 執行込み

---

## 5. データ分割

| 名称 | 旧名称 | 期間 | 用途 |
|---|---|---|---|
| **TRAIN** | IS | 2024-01-01 .. 2025-06-30 | 戦略開発 |
| **VALIDATION** | OOS1 | 2025-07-01 .. 2026-02-28 | パラメータ調整（記録必須） |
| **TEST** | OOS2 | 2026-03-01 .. 2026-08-31 | **最終判定のみ**（ロック） |

コード上は `IS` / `OOS1` / `OOS2` も後方互換で使用可（`SPLIT_ALIASES`）。

**ルール**: Research Loop の tuning は **VALIDATION のみ**。TEST は Gate2 候補の最終 1 回判定のみ（[validation-spec.md](validation-spec.md) §2）。

---

## 6. 合格ゲート（二層）

### 6.1 Research Gate（研究品質 — promote / Paper 移行の主判定）

[validation-spec.md](validation-spec.md) / [SPEC.md §8.3](../SPEC.md) 参照。

| チェック | 基準 |
|---|---|
| 執行 EV | > 0（VALIDATION） |
| PF | ≥ 1.15 |
| maxDD | ≤ ¥7,500 |
| Walk Forward pass rate | ≥ 60% |
| MC p95 DD | ≤ ¥7,500 |
| MC ruin prob | ≤ 5% |
| Robustness | fee/slip +20% で PF ≥ 1.0 |

**Research Loop の stop/go に使用。月次 P は最適化目標にしない。**

バッチ **V1** で計測: `python3 -m scripts.phase1.run_validation_batch V1`

### 6.2 Business Gate（Gate1 / Gate2）

| ゲート | 条件 | 意味 |
|---|---|---|
| **Gate1** | 執行込み EV > 0 **かつ** N ≈ 50±20%/月（40–60） | 取引可能エッジの存在 |
| **Gate2** | 執行込み月次 P ≥ ¥1,500（= 0.03 × 初期 BR、OOS 平均） | 本番採用 KPI |

理論値のみ pass → **hold**（promote しない）。

### 6.3 評価優先順位

1. OOS（VALIDATION）で期待値が残るか  
2. Walk Forward / Monte Carlo で過学習でないか  
3. DD に対して収益が十分か  
4. PF / Sharpe  
5. 手数料・Slippage 込み  
6. 月次 P（**結果**）

---

## 6.4 複利とバックテスト

| フェーズ | サイジング | Gate2 判定 |
|---|---|---|
| Phase1 履歴検証 | 固定 Q = ¥10,000（= 初期 BR の \(B/5\)） | 初期 BR 基準 \(P^* =\) ¥1,500 |
| フォワード / 本番 | 月次 BR ロールフォワード（margin = \(B/10\)、Q = \(B/5\)） | 当月 \(P \ge 0.03 \times B\)（Phase2 で実装） |

Phase1 の P 値は固定 Q 前提のため、Gate2 再ベースライン時は **gate フラグのみ再採点** し、バックテスト再実行は不要。

---

## 7. 成果物

| パス | 内容 |
|---|---|
| `data/phase1/p1a_results.json` | P1-A 結果 |
| `data/phase1/p1b_results.json` | P1-B 結果 |
| `data/phase1/p1c_results.json` | P1-C 結果 |
| `data/phase1/p1r_results.json` | P1-R グリッド結果 |
| `data/phase1/p1r2_results.json` | P1-R2 Exit grid 結果 |
| `data/phase1/p1r2c_results.json` | P1-R2C 固定 config 全 split 結果 |
| `data/validation/v1_*.json` | V1 Research Gate 結果 |
| `data/validation/b10_*.json` | B10 MFE/MAE 結果 |
| [phase1-verification-sheet.csv](phase1-verification-sheet.csv) | Phase1 記入シート |
| [validation-verification-sheet.csv](validation-verification-sheet.csv) | V1/B10/P3-C 記入シート |
| [knowledge-log.md](knowledge-log.md) | Knowledge Cards |

改訂: 2026-09-06（H-D canonical exit P1-R2C — sl0.5%/tp1.0%）

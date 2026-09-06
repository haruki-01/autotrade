# Paper Trade 検証仕様（PT）

Phase1 Gate1 候補 **H-D + H-M4** を、フォワードシミュレーション（実運用に近い逐次処理）で検証する正本。  
L0 は [SPEC.md](../SPEC.md)。Phase1 結果は [phase1-spec.md](phase1-spec.md)。

**対象ロジック**: H-D canonical（sl0.5%/tp1.0% + H-M4）  
**方式**: 履歴 OOS 期間上的に bar 逐次でシグナル→執行→損益を記録（GMO 接続なしの sim paper）

---

## 1. 検証バッチ

| batch_id | 主仮説 | 問い | 実行順 |
|---|---|---|---|
| **PT-A** | H-D + H-M4 | フォワード sim + 複利 BR で Gate1 が再現するか？ | 1 |
| **PT-B** | H-D canonical | P1-R2C 確定後、forward + 複利で Gate1 継続するか？ | 2（P1-R2C 後） |

---

## 2. 葉ルール

### PT-A（legacy）

Phase1 P1-C と同一（R-based RR 1:2）。

### PT-B（canonical — 現行）

[phase1-spec.md §2.1](phase1-spec.md) の canonical と同一。

| 項目 | 値 |
|---|---|
| シグナル | H-D pull + H-M4（土日停止） |
| SL / TP | **固定 0.5% / 1.0%** |
| max_bars / cooldown | 48 / 48 |
| 執行 | SPEC §7.3（70% entry fill, 85% TP, 0.02% slip） |

---

## 3. フォワード sim の定義

| 項目 | ルール |
|---|---|
| ウォームアップ | シグナル生成に必要な最小履歴（200 本）を確保してから開始 |
| 逐次処理 | エントリー bar 昇順。前トレード exit まで新規不可（Phase1 backtest 同型） |
| サイジング | エントリー時点の \(B\) で margin = \(B/10\)、\(Q = B/5\) |
| 損益スケール | `pnl = base_pnl × (Q / Q₀)`（\(Q₀\) = 初期 ¥10,000） |
| 複利 | **月末**に \(B \leftarrow B + \text{当月純損益}\) |
| シード | executed fill 乱数 seed=42（Phase1 と同一） |

---

## 4. 検証窓

| 窓 | 期間 | 用途 |
|---|---|---|
| OOS forward | 2025-07-01 .. 2026-08-31（OOS1+OOS2） | PT 主評価 |
| Phase1 参照 | P1-R2C VALIDATION/TEST | ベンチマーク比較（PT-B） |
| split 内訳 | OOS1=VALIDATION, OOS2=TEST | 月次・split 監視 |

---

## 5. 合格ゲート

| ゲート | 条件 | 意味 |
|---|---|---|
| **PT-Gate1** | 執行込み EV > 0 **かつ** N ≈ 50±20%/月 | Phase1 Gate1 の forward 再現 |
| **PT-Gate2** | 月次 P ≥ 0.05 × 当月月初 \(B\)（複利） | Gate2 の forward 版 |
| **PT-参照** | forward EV / P1-R2C OOS avg EV ≥ 0.7 | 劣化が許容範囲 |

---

## 6. PT-B 継続監視（§7）

実行: `python3 -m scripts.paper.run_pt PT-B`

成果物 JSON の `monitoring` ブロックに以下を記録:

| フィールド | 内容 |
|---|---|
| `monitoring_status` | `continue` / `pause` / `stop` |
| `split_breakdown` | VALIDATION / TEST 別 EV・P・Gate1 |
| `p1r2c_oos_avg_ev` | P1-R2C ベンチマーク |
| `gate2_pass_rate` | Gate2 達成月の割合 |
| `alerts` | 停止ルール違反 |

### 停止ルール

| 条件 | アクション |
|---|---|
| forward EV ≤ 0 | **stop** — Paper 中止 |
| PT-Gate1 fail | **stop** |
| 3 連続赤字月 | **pause** — 原因調査 |
| Gate2 未達 | 継続（stop 条件ではない） |

---

## 7. 成果物

| パス | 内容 |
|---|---|
| `data/paper/pt_a_results.json` | PT-A 結果 |
| `data/paper/pt_b_results.json` | PT-B 結果 + monitoring |
| `data/paper/pt_*_trades.jsonl` | トレードログ |
| [paper-verification-sheet.csv](paper-verification-sheet.csv) | 記入シート |
| [knowledge-log.md](knowledge-log.md) | KB-PT-A / KB-PT-B |

改訂: 2026-09-06（PT-B canonical 継続監視）

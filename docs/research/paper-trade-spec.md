# Paper Trade 検証仕様（PT）

Phase1 Gate1 候補 **H-D + H-M4** を、フォワードシミュレーション（実運用に近い逐次処理）で検証する正本。  
L0 は [SPEC.md](../SPEC.md)。Phase1 結果は [phase1-spec.md](phase1-spec.md)。

**対象ロジック**: P1-C composite（H-D + H-M4、H-A2 除外）  
**方式**: 履歴 OOS 期間上的に bar 逐次でシグナル→執行→損益を記録（GMO 接続なしの sim paper）

---

## 1. 検証バッチ

| batch_id | 主仮説 | 問い | 実行順 |
|---|---|---|---|
| **PT-A** | H-D + H-M4 | フォワード sim + 複利 BR で Gate1 が再現するか？ | 1 |

---

## 2. 葉ルール

Phase1 P1-C と同一（[phase1-spec.md §2](phase1-spec.md)）。

| 項目 | 値 |
|---|---|
| シグナル | H-D pull + H-M4（土日停止） |
| R / SL / TP | pct=0.008, atr×0.5, RR 1:2 |
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
| OOS forward | 2025-07-01 .. 2026-08-31（OOS1+OOS2） | PT-A 主評価 |
| Phase1 参照 | 同上 split の P1-C composite | 劣化率比較 |

---

## 5. 合格ゲート

| ゲート | 条件 | 意味 |
|---|---|---|
| **PT-Gate1** | 執行込み EV > 0 **かつ** N ≈ 50±20%/月 | Phase1 Gate1 の forward 再現 |
| **PT-Gate2** | 月次 P ≥ 0.05 × 当月月初 \(B\)（複利） | Gate2 の forward 版 |
| **PT-参照** | forward EV / Phase1 backtest EV ≥ 0.7 | 劣化が許容範囲 |

---

## 6. 成果物

| パス | 内容 |
|---|---|
| `data/paper/pt_a_results.json` | PT-A 結果 |
| `data/paper/pt_a_trades.jsonl` | トレードログ |
| [paper-verification-sheet.csv](paper-verification-sheet.csv) | 記入シート |
| [knowledge-log.md](knowledge-log.md) | KB-PT-A |

改訂: 2026-09-03

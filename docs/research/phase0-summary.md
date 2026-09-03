# Phase0 総括

Phase0（B01–B07）完了後の Phase1 候補一覧。  
統計定義: [phase0-stats.md](phase0-stats.md) / 運用: [verification-workflow.md](verification-workflow.md) / 詳細: [knowledge-log.md](knowledge-log.md)

**サンプル**: GMO Coin `BTC_JPY` 5m、2024-01-01..2026-08-31（276,646 bars）  
**Phase0 スコープ**: mean_edge / hit_rate / vs_baseline / verdict のみ（RR・ランダム勝率・手数料損益分岐は Phase1）

---

## バッチ別 batch_verdict

| batch | purpose | batch_verdict | 主な結論 |
|---|---|---|---|
| B01 | 時間構造 | conditional | 土日フィルタ（H-M4）採用候補 |
| B02 | スパイク分岐 | promote | **H-A2（継続）** が H-A（回帰）に勝つ |
| B03 | IGNITE 早期性 | conditional | EARLY≈LATE 優位だが絶対 edge 極小 |
| B04 | 点火亜型 | reject | H-B2/H-B3 独立候補なし |
| B05 | レジーム内押し | reject | H-F1 棄却（RESUME n 不足） |
| B06 | 群集 | conditional | **PULL > RAW**（押し待ち優位） |
| B07 | 稀イベント | conditional | 単体 Phase1 候補なし |

---

## Phase1 候補一覧

| 仮説 ID | batch_verdict | Phase1 候補 | 採用フィルタ / 執行ルール |
|---|---|---|---|
| **H-A2** | promote (B02) | **yes** | SPIKE 後 h60 継続方向。PATH で SL 参考 |
| **H-D** | conditional (B06) | **yes** | RSI 出口 → **初押し待ち（PULL）** 必須。即入り禁止 |
| **H-B** | conditional (B03) | filter-only | H-M5 遅入禁止。IGNITE 定義厳格化後に再検証 |
| **H-M4** | conditional (B01) | filter-only | 土日新規停止ゲート |
| H-C4 | conditional (B01) | filter-only | 平日優先（H-M4 と統合） |
| H-A | reject (B02) | no | 回帰方向 edge なし |
| H-B2, H-B3 | reject (B04) | no | — |
| H-F1 | reject (B05) | no | defer（期間延長でも n 不足） |
| H-A3, H-A4, H-B4 | reject (B07) | no | — |
| H-C2 | weak (B07) | no | 参考記録のみ |
| H-E, H-C | weak (B01) | no | フィルタ補助のみ |

---

## Phase1 へ進む条件（次フェーズ）

Phase0 で **yes** または **conditional** と判定された候補（H-A2, H-D, H-B, H-M4）について、Phase1 仕様（新規）で以下を評価する:

1. **RR 1:2** 込みの EV
2. **ランダムエントリー勝率** との差
3. **手数料損益分岐勝率**（GMO 往復コスト）
4. 執行込み OOS（理論値 vs 執行の二列）

---

## 合成ロジック案（Phase1 ドラフト入力）

| コンポーネント | ソース | 役割 |
|---|---|---|
| エントリー本体 | H-A2 または H-D | SPIKE 継続 / RSI+PULL |
| 遅入禁止 | H-M5（B03） | IGNITE 早期のみ |
| 土日ゲート | H-M4（B01） | 新規エントリー停止 |
| 執行 | H-D PULL ルール（B06） | 初押し待ち |

---

## データ成果物

| ファイル | 内容 |
|---|---|
| `data/phase0/b01_results.json` … `b07_results.json` | バッチ計測 JSON |
| [phase0-verification-sheet.csv](phase0-verification-sheet.csv) | 全 metric 記入済み |
| [knowledge-log.md](knowledge-log.md) | KB-B01 … KB-B07 |
| [edge-catalog.md](edge-catalog.md) | 仮説 status 更新済み |

改訂: 2026-09-03

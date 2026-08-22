# 実装プラン（現状 → 次にやること）

最終更新: 2026-08-22

## 1. いまどこまでできているか

| 領域 | 状態 | 内容 |
|------|------|------|
| 全体設計 | **完了** | `docs/PROJECT_PLAN.md` |
| 戦略仮説 v1 | **完了** | 日足/4H/15m 順張り（`docs/HYPOTHESIS.md`） |
| BT設計 | **完了** | コスト・期間分割・合否（`docs/BACKTEST_DESIGN.md`） |
| Secrets配置 | **完了** | `secrets/demo` / `secrets/live` |
| データ取得（Bybit） | **コード完了** | `src/autotrade/data/bybit.py` + CLI `fetch-data` |
| データ取得フォールバック | **完了** | Bybit 403時は Binance Vision 実足（研究用） |
| MTFシグナル | **コード完了** | `src/autotrade/strategy/mtf_trend.py` |
| バックテスト引擎 | **コード完了** | 手数料・スリッページ込みシミュレータ |
| メトリクス/合否 | **コード完了** | DD・期待値・最低トレード数ゲート |
| 実データ Set B | **実施済み・FAIL** | 2024年・Binance Vision。詳細は `docs/BACKTEST_RESULTS.md` |
| 仮説カタログ | **完了** | 公開情報ベースの検証候補 20本超。`docs/HYPOTHESIS_CATALOG.md` |
| 合成データでの動作確認 | **完了** | `--synthetic` でパイプライン通確認済み |
| デモ注文（testnet） | **未着手** | |
| 本番執行 | **未着手** | |
| Dashboard / UI | **対象外（後回し）** | |

### 使えるコマンド（すでに実装済み）

```bash
pip install -e .

# Bybit から BTCUSDT 過去足を取得（APIキー不要・公開エンドポイント）
autotrade fetch-data --set B

# バックテスト（本検証セット B）
autotrade backtest --set B

# Cloud等で API が使えないとき（動作確認のみ・成績は参考にしない）
autotrade backtest --set B --synthetic
```

---

## 2. Bybit から BTC-USDT 過去データは取れるか？

**取れる。** しかも検証用途なら **APIキー不要**。

| 項目 | 内容 |
|------|------|
| API | Bybit v5 `GET /v5/market/kline`（公開） |
| 銘柄 | `BTCUSDT` / `category=linear`（USDT無期限） |
| 足 | `1d` / `4h` / `15m`（本プロジェクトで使用） |
| 認証 | 過去ローソク足の取得だけなら不要 |
| 本リポの実装 | `BybitPublicClient.fetch_klines` + `autotrade fetch-data` |
| 保存先 | `data/cache/*.csv`（gitignore） |

注意:
1. **Cloud Agent 環境からは国制限で 403** になることがある → **手元 Cursor / 自宅PC / VPS** で `fetch-data` する
2. 一度取得すれば CSV キャッシュされるので、同じ期間の再取得は不要
3. 履歴の長さは Bybit 側の保持範囲に依存（足りなければ期間を分割して取得）

→ **過去検証（バックテスト）用データとしてそのまま使える。**  
　Set B は実施済み（FAIL）。次は仮説カタログの優先5本を1本ずつ再検証。

---

## 3. 実装ロードマップ（これから）

### Step A — 実データで仮説を判定する（最優先・今ここ）

目的: 「この仮説はコスト込みで期待値プラスか」を実足で決める。

1. 手元環境で `autotrade fetch-data --set all`
2. `autotrade backtest --set B`（本検証）
3. 合格なら `autotrade backtest --set C`（直近耐久）
4. 結果を見て合否（ゲート: 期待値>0 / トレード≥100 / DD≤20%）

成果物: `artifacts/backtests/*/metrics.json` + `trades.csv`

**Gate A 不合格時の方針（いじりすぎ禁止）**
- エントリー条件を **1点だけ** 変えて再検証
- 時間足の役割（1D/4H/15m）は変えない
- 大量パラメータ探索はしない
- 別ファミリー（ブレイク、レジーム、イグジット変更）は `docs/HYPOTHESIS_CATALOG.md` の優先5本から1本ずつ

### Step A2 — 仮説カタログから再スクリーニング（いまここ）

v1 は Set B FAIL。次はカタログの優先バッチ:

1. H22 固定利確をやめる（v1と1点差）
2. H07 ATR損切り
3. H06 ADXレジーム
4. H02 Donchian 20/10
5. H21 ロングオンリー

### Step B — 執行レイヤ（demo）

目的: バックテストと同じシグナルで、testnet に実注文を出す。

1. Bybit testnet キーを `secrets/demo/bybit.env` に設定
2. 注文アダプタ（成行・ポジション照会・キャンセル）
3. モード `demo` の常駐ループ（15m足確定ごとに判定）
4. レート制限・再接続・メンテ時の安全停止
5. ログ: シグナル / 注文ID / 約定 / エラー

**Gate B:** 一定期間、注文が通り、ポジション認識がずれない。

### Step C — リスク制御の強化

1. 1日損失上限で新規停止
2. 最大ポジション1・レバ上限強制
3. live 誤起動防止フラグ
4. Kill switch（ファイル or 環境変数）

### Step D — 少額 live

1. `secrets/live`（出金権限なし・IP制限）
2. 少額・厳しい損失上限
3. 同一エンジンで稼働

### Step E —（後回し）Dashboard / 複数bot

Phase 1 完了後。

---

## 4. 直近2週間の作業順（推奨）

| 順 | 作業 | 依存 | 完了条件 |
|----|------|------|----------|
| 1 | 手元で Bybit 実データ取得 | ネットワークが Bybit に届くこと | `data/cache` に 1d/4h/15m CSV |
| 2 | set B バックテスト | 1 | metrics が出る |
| 3 | 合否レビュー | 2 | PASS/FAIL と次アクション決定 |
| 4 | （PASSなら）set C | 3 | 直近でも崩壊していない |
| 5 | demo 執行スケルトン実装 | 4 or 並行可 | testnet で1注文通る |
| 6 | demo 常駐 + 遅延/レート制限検証 | 5 | 観察ログが残る |

---

## 5. リスク・制約（実装時に忘れないこと）

- バックテスト合格 ≠ 実戦勝ち（demo を最終ゲートの前段にする）
- Cloud では実データ取得できない前提で進める
- 合成データ（`--synthetic`）の成績は **絶対に採用判断に使わない**
- APIキーは Git に入れない（既存 `secrets/` 運用）

---

## 6. 次のアクション提案

プラン承認後、すぐ着手すべき実装/作業は次のどちらか:

**A（推奨）:** 手元での実データ取得手順を短く確認し、取得〜BT結果の見方を整える（必要なら取得スクリプトの改善）  
**B:** 並行して **demo 執行アダプタ** の実装に入る（BTは手元で回してもらう）

どちらの優先でも、このドキュメントを正として進める。

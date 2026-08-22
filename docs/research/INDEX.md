# 研究ログ — 一覧

仮説・売買ロジック・検証結果の蓄積。詳細は各エントリと `registry.yaml` を参照。

運用: バックテスト実行後に自動追記。手動追記は `_template.md` と `registry.yaml` を参照。

## サマリー表

| Run ID | 日付 | 仮説 | ロジック | Set | データ | ステータス | 期待値 | DD | トレード | 詳細 |
|--------|------|------|----------|-----|--------|------------|--------|-----|----------|------|
| 20260822-003 | 2026-08-22 | L-COST | cost_gate_v1 | B | — | `proposed` | — | — |  | — |
| 20260822-004 | 2026-08-22 | L-MOM-VOL | vol_scaled_trend_v1 | B | — | `proposed` | — | — |  | — |
| 20260822-005 | 2026-08-22 | L-BREAK | donchian_20_10_v1 | B | — | `proposed` | — | — |  | — |
| 20260822-002 | 2026-08-22 | H01 | mtf_ema_pullback_v1 | B | binance_vision | `fail` | -3.10 | 49.4% | 594 | [doc](entries/H01-mtf_ema_pullback_v1-setB-20260822.md) |
| 20260822-001 | 2026-08-22 | H01 | mtf_ema_pullback_v1 | B | synthetic | `smoke` | 235.87 | 11.7% | 397 | [doc](entries/H01-mtf_ema_pullback_v1-setB-20260822-smoke.md) |

## ステータス凡例

| ステータス | 意味 |
|------------|------|
| `pass` | Set B ゲート合格 |
| `fail` | 実データでゲート不合格 |
| `smoke` | 合成データ等。採用判断に使わない |
| `proposed` | 未検証 |
| `archived` | 参照用に残すが追わない |

## 関連

- [README（運用ルール）](./README.md)
- [registry.yaml](./registry.yaml) — 機械可読マスタ
- [エントリテンプレート](./_template.md)
- [市場の歪み前提](../MARKET_EDGE_MAP.md)

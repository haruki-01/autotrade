# 研究ログ — 一覧

仮説・売買ロジック・検証結果の蓄積。詳細は各エントリと `registry.yaml` を参照。

運用: バックテスト実行後に自動追記。手動追記は `_template.md` と `registry.yaml` を参照。

## サマリー表

| Run ID | 日付 | 仮説 | ロジック | Set | データ | ステータス | 期待値 | DD | トレード | 詳細 |
|--------|------|------|----------|-----|--------|------------|--------|-----|----------|------|
| 20260823-001 | 2026-08-23 | L-BREAK-2 | donchian_h4_20_10_v1 | B | binance_vision | `fail` | 0.85 | 3.8% | 58 | [doc](entries/L-BREAK-2-donchian_h4_20_10_v1-setB-20260823-001.md) |
| 20260822-062 | 2026-08-22 | HYP-043 | d_near_high_break_v1 | B | binance_vision | `fail` | 7.63 | 1.0% | 5 | [doc](entries/HYP-043-d_near_high_break_v1-setB-20260822-062.md) |
| 20260822-061 | 2026-08-22 | HYP-036 | d_comp_break_v1 | B | binance_vision | `fail` | 22.05 | 0.0% | 1 | [doc](entries/HYP-036-d_comp_break_v1-setB-20260822-061.md) |
| 20260822-060 | 2026-08-22 | HYP-035 | d_exp_break_v1 | B | binance_vision | `fail` | -0.85 | 1.0% | 2 | [doc](entries/HYP-035-d_exp_break_v1-setB-20260822-060.md) |
| 20260822-059 | 2026-08-22 | HYP-034 | d_fri_break_v1 | B | binance_vision | `fail` | 3.98 | 0.5% | 2 | [doc](entries/HYP-034-d_fri_break_v1-setB-20260822-059.md) |
| 20260822-058 | 2026-08-22 | HYP-033 | d_monday_break_v1 | B | binance_vision | `fail` | 6.74 | 1.5% | 4 | [doc](entries/HYP-033-d_monday_break_v1-setB-20260822-058.md) |
| 20260822-057 | 2026-08-22 | HYP-032 | d_break_any_v1 | B | binance_vision | `fail` | 7.63 | 1.0% | 5 | [doc](entries/HYP-032-d_break_any_v1-setB-20260822-057.md) |
| 20260822-056 | 2026-08-22 | HYP-031 | d_dn_break_v1 | B | binance_vision | `fail` | -1.64 | 2.8% | 5 | [doc](entries/HYP-031-d_dn_break_v1-setB-20260822-056.md) |
| 20260822-055 | 2026-08-22 | HYP-028 | d_half_pb_v1 | B | binance_vision | `fail` | 2.75 | 3.4% | 5 | [doc](entries/HYP-028-d_half_pb_v1-setB-20260822-055.md) |
| 20260822-054 | 2026-08-22 | HYP-027 | d_shallow_pb_v1 | B | binance_vision | `fail` | 4.45 | 1.8% | 6 | [doc](entries/HYP-027-d_shallow_pb_v1-setB-20260822-054.md) |
| 20260822-053 | 2026-08-22 | HYP-026 | d_break_not_compress_v1 | B | binance_vision | `fail` | 7.25 | 1.0% | 5 | [doc](entries/HYP-026-d_break_not_compress_v1-setB-20260822-053.md) |
| 20260822-052 | 2026-08-22 | HYP-025 | d_reclaim_deep_v1 | B | binance_vision | `fail` | 6.51 | 0.8% | 3 | [doc](entries/HYP-025-d_reclaim_deep_v1-setB-20260822-052.md) |
| 20260822-051 | 2026-08-22 | HYP-024 | d_second_break_v1 | B | binance_vision | `fail` | 2.56 | 2.3% | 5 | [doc](entries/HYP-024-d_second_break_v1-setB-20260822-051.md) |
| 20260822-050 | 2026-08-22 | HYP-051 | h4_fail_ll_reclaim_ny_v1 | B | binance_vision | `fail` | -2.24 | 0.8% | 1 | [doc](entries/HYP-051-h4_fail_ll_reclaim_ny_v1-setB-20260822-050.md) |
| 20260822-049 | 2026-08-22 | HYP-050 | h4_inside_bar_break_v1 | B | binance_vision | `fail` | 1.17 | 1.7% | 9 | [doc](entries/HYP-050-h4_inside_bar_break_v1-setB-20260822-049.md) |
| 20260822-048 | 2026-08-22 | HYP-049 | h4_break_midweek_v1 | B | binance_vision | `fail` | 2.77 | 3.2% | 15 | [doc](entries/HYP-049-h4_break_midweek_v1-setB-20260822-048.md) |
| 20260822-047 | 2026-08-22 | HYP-048 | h4_break_non_asia_comp_v1 | B | binance_vision | `fail` | 1.87 | 3.3% | 7 | [doc](entries/HYP-048-h4_break_non_asia_comp_v1-setB-20260822-047.md) |
| 20260822-046 | 2026-08-22 | HYP-047 | h4_break_non_asia_exp_v1 | B | binance_vision | `fail` | 3.85 | 2.1% | 10 | [doc](entries/HYP-047-h4_break_non_asia_exp_v1-setB-20260822-046.md) |
| 20260822-045 | 2026-08-22 | HYP-046 | h4_bm_not_asia_v1 | B | binance_vision | `fail` | 1.59 | 3.2% | 30 | [doc](entries/HYP-046-h4_bm_not_asia_v1-setB-20260822-045.md) |
| 20260822-044 | 2026-08-22 | HYP-045 | h4_shallow_pb_exp_ny_v1 | B | binance_vision | `fail` | 0.18 | 1.1% | 5 | [doc](entries/HYP-045-h4_shallow_pb_exp_ny_v1-setB-20260822-044.md) |
| 20260822-043 | 2026-08-22 | HYP-044 | h4_shallow_pb_exp_lon_v1 | B | binance_vision | `fail` | 0.34 | 1.6% | 11 | [doc](entries/HYP-044-h4_shallow_pb_exp_lon_v1-setB-20260822-043.md) |
| 20260822-042 | 2026-08-22 | HYP-052 | h4_break_bull_confirm_v1 | B | binance_vision | `fail` | 1.46 | 4.3% | 30 | [doc](entries/HYP-052-h4_break_bull_confirm_v1-setB-20260822-042.md) |
| 20260822-041 | 2026-08-22 | HYP-042 | h4_break_below_sma_v1 | B | binance_vision | `fail` | -0.86 | 0.9% | 3 | [doc](entries/HYP-042-h4_break_below_sma_v1-setB-20260822-041.md) |
| 20260822-040 | 2026-08-22 | HYP-041 | h4_low_reclaim_v1 | B | binance_vision | `fail` | -1.90 | 4.5% | 7 | [doc](entries/HYP-041-h4_low_reclaim_v1-setB-20260822-040.md) |
| 20260822-039 | 2026-08-22 | HYP-040 | h4_two_bull_high_v1 | B | binance_vision | `fail` | 1.24 | 3.2% | 37 | [doc](entries/HYP-040-h4_two_bull_high_v1-setB-20260822-039.md) |
| 20260822-038 | 2026-08-22 | HYP-039 | h4_mid_range_break_v1 | B | binance_vision | `fail` | 15.11 | 0.0% | 2 | [doc](entries/HYP-039-h4_mid_range_break_v1-setB-20260822-038.md) |
| 20260822-037 | 2026-08-22 | HYP-038 | h4_first_break_v1 | B | binance_vision | `fail` | 1.75 | 2.4% | 19 | [doc](entries/HYP-038-h4_first_break_v1-setB-20260822-037.md) |
| 20260822-036 | 2026-08-22 | HYP-037 | h4_repeat_break_v1 | B | binance_vision | `fail` | 1.57 | 4.1% | 27 | [doc](entries/HYP-037-h4_repeat_break_v1-setB-20260822-036.md) |
| 20260822-035 | 2026-08-22 | HYP-030 | h4_fade_asia_high_v1 | B | binance_vision | `fail` | -0.36 | 8.0% | 34 | [doc](entries/HYP-030-h4_fade_asia_high_v1-setB-20260822-035.md) |
| 20260822-034 | 2026-08-22 | HYP-029 | h4_dn_break_non_asia_v1 | B | binance_vision | `fail` | 0.00 | 2.6% | 25 | [doc](entries/HYP-029-h4_dn_break_non_asia_v1-setB-20260822-034.md) |
| 20260822-033 | 2026-08-22 | HYP-023 | h4_compress_break_lon_v1 | B | binance_vision | `fail` | 4.39 | 2.5% | 9 | [doc](entries/HYP-023-h4_compress_break_lon_v1-setB-20260822-033.md) |
| 20260822-032 | 2026-08-22 | HYP-022 | h4_exp_trend_cont_v1 | B | binance_vision | `fail` | 1.97 | 3.5% | 15 | [doc](entries/HYP-022-h4_exp_trend_cont_v1-setB-20260822-032.md) |
| 20260822-031 | 2026-08-22 | HYP-021 | h4_pb_after_break_v1 | B | binance_vision | `fail` | 0.68 | 3.2% | 14 | [doc](entries/HYP-021-h4_pb_after_break_v1-setB-20260822-031.md) |
| 20260822-030 | 2026-08-22 | HYP-020 | h4_near_high_exp_lon_v1 | B | binance_vision | `fail` | 2.27 | 3.9% | 13 | [doc](entries/HYP-020-h4_near_high_exp_lon_v1-setB-20260822-030.md) |
| 20260822-029 | 2026-08-22 | HYP-019 | h4_fail_ll_reclaim_v1 | B | binance_vision | `fail` | -1.74 | 0.6% | 1 | [doc](entries/HYP-019-h4_fail_ll_reclaim_v1-setB-20260822-029.md) |
| 20260822-028 | 2026-08-22 | HYP-018 | h4_break_asia_only_v1 | B | binance_vision | `fail` | 1.39 | 5.8% | 26 | [doc](entries/HYP-018-h4_break_asia_only_v1-setB-20260822-028.md) |
| 20260822-027 | 2026-08-22 | HYP-017 | h4_break_ny_v1 | B | binance_vision | `fail` | 2.12 | 4.2% | 21 | [doc](entries/HYP-017-h4_break_ny_v1-setB-20260822-027.md) |
| 20260822-026 | 2026-08-22 | HYP-016 | h4_half_pb_london_v1 | B | binance_vision | `fail` | -0.24 | 4.3% | 18 | [doc](entries/HYP-016-h4_half_pb_london_v1-setB-20260822-026.md) |
| 20260822-025 | 2026-08-22 | HYP-015 | h4_bm_entry_v1 | B | binance_vision | `fail` | 1.49 | 4.6% | 33 | [doc](entries/HYP-015-h4_bm_entry_v1-setB-20260822-025.md) |
| 20260822-024 | 2026-08-22 | HYP-014 | h4_shallow_pb_exp_v1 | B | binance_vision | `fail` | 0.20 | 1.9% | 16 | [doc](entries/HYP-014-h4_shallow_pb_exp_v1-setB-20260822-024.md) |
| 20260822-023 | 2026-08-22 | HYP-013 | h4_break_london_v1 | B | binance_vision | `fail` | 2.07 | 3.3% | 22 | [doc](entries/HYP-013-h4_break_london_v1-setB-20260822-023.md) |
| 20260822-022 | 2026-08-22 | HYP-012 | h4_break_non_asia_v1 | B | binance_vision | `fail` | 1.41 | 4.4% | 31 | [doc](entries/HYP-012-h4_break_non_asia_v1-setB-20260822-022.md) |
| 20260822-021 | 2026-08-22 | HYP-012 | h4_break_non_asia_v1 | B | binance_vision | `fail` | 1.41 | 4.4% | 31 | [doc](entries/HYP-012-h4_break_non_asia_v1-setB-20260822-021.md) |
| 20260822-020 | 2026-08-22 | HYP-010 | fake_then_retest_v1 | B | binance_vision | `fail` | -0.62 | 0.2% | 1 | [doc](entries/HYP-010-fake_then_retest_v1-setB-20260822-020.md) |
| 20260822-019 | 2026-08-22 | HYP-009 | fake_then_rebreak_v1 | B | binance_vision | `fail` | -0.81 | 0.3% | 1 | [doc](entries/HYP-009-fake_then_rebreak_v1-setB-20260822-019.md) |
| 20260822-018 | 2026-08-22 | HYP-011 | near_high_expanded_v1 | B | binance_vision | `fail` | -0.60 | 0.9% | 2 | [doc](entries/HYP-011-near_high_expanded_v1-setB-20260822-018.md) |
| 20260822-017 | 2026-08-22 | HYP-002 | donchian_20_10_long_v2 | B | binance_vision | `fail` | 5.92 | 1.8% | 6 | [doc](entries/HYP-002-donchian_20_10_long_v2-setB-20260822-017.md) |
| 20260822-016 | 2026-08-22 | H21 | donchian_20_10_long_only | B | binance_vision | `fail` | 122.43 | 2.0% | 8 | [doc](entries/H21-donchian_20_10_long_only-setB-20260822-016.md) |
| 20260822-015 | 2026-08-22 | L-BREAK | donchian_20_10_v1 | B | binance_vision | `fail` | 54.34 | 3.8% | 13 | [doc](entries/L-BREAK-donchian_20_10_v1-setB-20260822-015.md) |
| 20260822-014 | 2026-08-22 | L-MOM-VOL | vol_scaled_trend_v1 | B | binance_vision | `fail` | -6.59 | 98.4% | 1064 | [doc](entries/L-MOM-VOL-vol_scaled_trend_v1-setB-20260822-014.md) |
| 20260822-013 | 2026-08-22 | L-COST | cost_gate_v1 | B | binance_vision | `fail` | -3.73 | 51.6% | 570 | [doc](entries/L-COST-cost_gate_v1-setB-20260822-013.md) |
| 20260822-012 | 2026-08-22 | H01 | mtf_ema_pullback_v1 | B | binance_vision | `fail` | -3.10 | 49.4% | 594 | [doc](entries/H01-mtf_ema_pullback_v1-setB-20260822-012.md) |
| 20260822-011 | 2026-08-22 | H01 | mtf_ema_pullback_v1 | B | binance_vision | `fail` | -3.10 | 49.4% | 594 | [doc](entries/H01-mtf_ema_pullback_v1-setB-20260822-011.md) |
| 20260822-010 | 2026-08-22 | H21 | donchian_20_10_long_only | B | synthetic | `smoke` | 4102.21 | 0.0% | 3 | [doc](entries/H21-donchian_20_10_long_only-setB-20260822-010-smoke.md) |
| 20260822-009 | 2026-08-22 | L-BREAK | donchian_20_10_v1 | B | synthetic | `smoke` | 4474.33 | 0.0% | 5 | [doc](entries/L-BREAK-donchian_20_10_v1-setB-20260822-009-smoke.md) |
| 20260822-008 | 2026-08-22 | L-MOM-VOL | vol_scaled_trend_v1 | B | synthetic | `smoke` | 356.26 | 30.2% | 566 | [doc](entries/L-MOM-VOL-vol_scaled_trend_v1-setB-20260822-008-smoke.md) |
| 20260822-007 | 2026-08-22 | L-COST | cost_gate_v1 | B | synthetic | `smoke` | 242.07 | 11.7% | 385 | [doc](entries/L-COST-cost_gate_v1-setB-20260822-007-smoke.md) |
| 20260822-006 | 2026-08-22 | H01 | mtf_ema_pullback_v1 | B | synthetic | `smoke` | 242.07 | 11.7% | 385 | [doc](entries/H01-mtf_ema_pullback_v1-setB-20260822-006-smoke.md) |
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
- [市場の歪み前提](../master/MARKET_EDGE_MAP.md)
- [Workstreams](../workstreams/)

# 研究ログ — 一覧

仮説・売買ロジック・検証結果の蓄積。詳細は各エントリと `registry.yaml` を参照。

運用: バックテスト実行後に自動追記。手動追記は `_template.md` と `registry.yaml` を参照。

## サマリー表

\* 20260825-slow-evdd: EV+DD は PASS。期間ごとの n<100 は判定保留。月50は非ゲート。

| Run ID | 日付 | 仮説 | ロジック | Set | データ | ステータス | 期待値 | DD | トレード | 詳細 |
|--------|------|------|----------|-----|--------|------------|--------|-----|----------|------|
| 20260825-slow-evdd | 2026-08-25 | SH-01 | sh01n_center | A/B/C | binance_vision | `pass`* | 0.99 | 7.6% | 164 | [doc](entries/SH-01-sh01n_center-evdd-20260825.md) |
| 20260823-071 | 2026-08-23 | EH-09 | eh09_slope_0p05 | B | binance_vision | `pass` | 0.11 | 3.7% | 179 | [doc](entries/EH-09-eh09_slope_0p05-setB-20260823-071.md) |
| 20260823-072 | 2026-08-23 | EH-09 | eh09_trail_2p5 | B | binance_vision | `pass` | 0.02 | 11.8% | 266 | [doc](entries/EH-09-eh09_trail_2p5-setB-20260823-072.md) |
| 20260823-068 | 2026-08-23 | EH-09 | eh09_base | B | binance_vision | `pass` | 0.01 | 9.2% | 311 | [doc](entries/EH-09-eh09_base-setB-20260823-068.md) |
| 20260823-069 | 2026-08-23 | EH-09 | eh09_win_8 | B | binance_vision | `pass` | 0.03 | 11.3% | 302 | [doc](entries/EH-09-eh09_win_8-setB-20260823-069.md) |
| 20260823-070 | 2026-08-23 | EH-09 | eh09_win_32 | B | binance_vision | `pass` | 0.00 | 11.3% | 291 | [doc](entries/EH-09-eh09_win_32-setB-20260823-070.md) |
| 20260823-065 | 2026-08-23 | EH-08 | eh08_ctrl_no_build | B | binance_vision | `pass` | 0.05 | 6.5% | 269 | [doc](entries/EH-08-eh08_ctrl_no_build-setB-20260823-065.md) |
| 20260823-066 | 2026-08-23 | EH-08 | eh08_trail_4 | B | binance_vision | `pass` | 0.01 | 6.1% | 182 | [doc](entries/EH-08-eh08_trail_4-setB-20260823-066.md) |
| 20260823-067 | 2026-08-23 | EH-08 | eh08_long_only | B | binance_vision | `pass` | 0.05 | 5.1% | 105 | [doc](entries/EH-08-eh08_long_only-setB-20260823-067.md) |
| 20260823-062 | 2026-08-23 | EH-01 | eh01_brk_192 | B | binance_vision | `pass` | 0.01 | 9.6% | 157 | [doc](entries/EH-01-eh01_brk_192-setB-20260823-062.md) |
| 20260823-063 | 2026-08-23 | EH-01 | eh01_long_only | B | binance_vision | `pass` | 0.13 | 5.2% | 138 | [doc](entries/EH-01-eh01_long_only-setB-20260823-063.md) |
| 20260823-064 | 2026-08-23 | EH-06 | eh06_win_10d | B | binance_vision | `pass` | 0.00 | 19.2% | 721 | [doc](entries/EH-06-eh06_win_10d-setB-20260823-064.md) |
| 20260823-061 | 2026-08-23 | DB-31 | db_1h_wide_v1 | C | binance_vision | `fail` | -0.07 | 12.0% | 273 | [doc](entries/DB-31-db_1h_wide_v1-setC-20260823-061.md) |
| 20260823-060 | 2026-08-23 | DB-41 | db_1h_band_tight_v1 | C | binance_vision | `fail` | -0.07 | 9.2% | 208 | [doc](entries/DB-41-db_1h_band_tight_v1-setC-20260823-060.md) |
| 20260823-059 | 2026-08-23 | DB-42 | db_1h_band_wide_v1 | C | binance_vision | `fail` | -0.11 | 12.1% | 211 | [doc](entries/DB-42-db_1h_band_wide_v1-setC-20260823-059.md) |
| 20260823-058 | 2026-08-23 | DB-29 | db_1h_stop_bottom_v1 | C | binance_vision | `fail` | -0.12 | 12.4% | 207 | [doc](entries/DB-29-db_1h_stop_bottom_v1-setC-20260823-058.md) |
| 20260823-057 | 2026-08-23 | DB-33 | db_1h_clean_v1 | C | binance_vision | `fail` | -0.13 | 14.1% | 210 | [doc](entries/DB-33-db_1h_clean_v1-setC-20260823-057.md) |
| 20260823-056 | 2026-08-23 | DB-27 | db_1h_fresh72_v1 | C | binance_vision | `fail` | -0.12 | 11.3% | 196 | [doc](entries/DB-27-db_1h_fresh72_v1-setC-20260823-056.md) |
| 20260823-055 | 2026-08-23 | DB-43 | db_1h_close_bottoms_v1 | C | binance_vision | `fail` | -0.08 | 12.9% | 292 | [doc](entries/DB-43-db_1h_close_bottoms_v1-setC-20260823-055.md) |
| 20260823-054 | 2026-08-23 | DB-25 | db_1h_fresh48_v1 | C | binance_vision | `fail` | -0.12 | 10.8% | 192 | [doc](entries/DB-25-db_1h_fresh48_v1-setC-20260823-054.md) |
| 20260823-053 | 2026-08-23 | DB-51 | db_1h_atr_stop_v1 | B | binance_vision | `fail` | -0.03 | 7.6% | 109 | [doc](entries/DB-51-db_1h_atr_stop_v1-setB-20260823-053.md) |
| 20260823-052 | 2026-08-23 | DB-50 | db_4h_pivot2_v1 | B | binance_vision | `fail` | 0.34 | 4.6% | 46 | [doc](entries/DB-50-db_4h_pivot2_v1-setB-20260823-052.md) |
| 20260823-051 | 2026-08-23 | DB-49 | db_4h_band_tight_v1 | B | binance_vision | `fail` | 0.52 | 1.7% | 29 | [doc](entries/DB-49-db_4h_band_tight_v1-setB-20260823-051.md) |
| 20260823-050 | 2026-08-23 | DB-48 | db_15m_fresh48_v1 | B | binance_vision | `fail` | -0.10 | 23.2% | 448 | [doc](entries/DB-48-db_15m_fresh48_v1-setB-20260823-050.md) |
| 20260823-049 | 2026-08-23 | DB-47 | db_15m_reclaim_v1 | B | binance_vision | `fail` | -0.10 | 19.7% | 389 | [doc](entries/DB-47-db_15m_reclaim_v1-setB-20260823-049.md) |
| 20260823-048 | 2026-08-23 | DB-46 | db_15m_up_only_v1 | B | binance_vision | `fail` | -0.17 | 12.2% | 167 | [doc](entries/DB-46-db_15m_up_only_v1-setB-20260823-048.md) |
| 20260823-047 | 2026-08-23 | DB-45 | db_15m_baseline_v1 | B | binance_vision | `fail` | -0.12 | 27.2% | 486 | [doc](entries/DB-45-db_15m_baseline_v1-setB-20260823-047.md) |
| 20260823-046 | 2026-08-23 | DB-44 | db_1h_far_bottoms_v1 | B | binance_vision | `fail` | -0.05 | 4.8% | 75 | [doc](entries/DB-44-db_1h_far_bottoms_v1-setB-20260823-046.md) |
| 20260823-045 | 2026-08-23 | DB-43 | db_1h_close_bottoms_v1 | B | binance_vision | `pass` | 0.06 | 7.0% | 156 | [doc](entries/DB-43-db_1h_close_bottoms_v1-setB-20260823-045.md) |
| 20260823-044 | 2026-08-23 | DB-42 | db_1h_band_wide_v1 | B | binance_vision | `pass` | 0.02 | 7.5% | 110 | [doc](entries/DB-42-db_1h_band_wide_v1-setB-20260823-044.md) |
| 20260823-043 | 2026-08-23 | DB-41 | db_1h_band_tight_v1 | B | binance_vision | `pass` | 0.01 | 5.3% | 110 | [doc](entries/DB-41-db_1h_band_tight_v1-setB-20260823-043.md) |
| 20260823-042 | 2026-08-23 | DB-40 | db_1h_pivot5_v1 | B | binance_vision | `fail` | -0.01 | 4.2% | 77 | [doc](entries/DB-40-db_1h_pivot5_v1-setB-20260823-042.md) |
| 20260823-041 | 2026-08-23 | DB-39 | db_1h_pivot2_v1 | B | binance_vision | `fail` | -0.01 | 7.3% | 149 | [doc](entries/DB-39-db_1h_pivot2_v1-setB-20260823-041.md) |
| 20260823-040 | 2026-08-23 | DB-38 | db_1h_session_v1 | B | binance_vision | `fail` | 0.03 | 4.2% | 75 | [doc](entries/DB-38-db_1h_session_v1-setB-20260823-040.md) |
| 20260823-039 | 2026-08-23 | DB-37 | db_1h_first_retest_v1 | B | binance_vision | `fail` | -0.02 | 6.8% | 92 | [doc](entries/DB-37-db_1h_first_retest_v1-setB-20260823-039.md) |
| 20260823-038 | 2026-08-23 | DB-36 | db_1h_break_bh_v1 | B | binance_vision | `fail` | -0.00 | 4.2% | 61 | [doc](entries/DB-36-db_1h_break_bh_v1-setB-20260823-038.md) |
| 20260823-037 | 2026-08-23 | DB-35 | db_1h_pct_height_v1 | B | binance_vision | `fail` | -0.07 | 5.6% | 71 | [doc](entries/DB-35-db_1h_pct_height_v1-setB-20260823-037.md) |
| 20260823-036 | 2026-08-23 | DB-34 | db_1h_fixed_pct_v1 | B | binance_vision | `fail` | -0.04 | 6.6% | 108 | [doc](entries/DB-34-db_1h_fixed_pct_v1-setB-20260823-036.md) |
| 20260823-035 | 2026-08-23 | DB-33 | db_1h_clean_v1 | B | binance_vision | `pass` | 0.02 | 5.1% | 103 | [doc](entries/DB-33-db_1h_clean_v1-setB-20260823-035.md) |
| 20260823-034 | 2026-08-23 | DB-32 | db_1h_wick_v1 | B | binance_vision | `fail` | -0.01 | 6.6% | 105 | [doc](entries/DB-32-db_1h_wick_v1-setB-20260823-034.md) |
| 20260823-033 | 2026-08-23 | DB-31 | db_1h_wide_v1 | B | binance_vision | `pass` | 0.01 | 6.6% | 138 | [doc](entries/DB-31-db_1h_wide_v1-setB-20260823-033.md) |
| 20260823-032 | 2026-08-23 | DB-30 | db_1h_tight_v1 | B | binance_vision | `fail` | 0.03 | 3.5% | 75 | [doc](entries/DB-30-db_1h_tight_v1-setB-20260823-032.md) |
| 20260823-031 | 2026-08-23 | DB-29 | db_1h_stop_bottom_v1 | B | binance_vision | `pass` | 0.02 | 6.6% | 105 | [doc](entries/DB-29-db_1h_stop_bottom_v1-setB-20260823-031.md) |
| 20260823-030 | 2026-08-23 | DB-28 | db_1h_trail_v1 | B | binance_vision | `fail` | -0.08 | 8.6% | 111 | [doc](entries/DB-28-db_1h_trail_v1-setB-20260823-030.md) |
| 20260823-029 | 2026-08-23 | DB-27 | db_1h_fresh72_v1 | B | binance_vision | `pass` | 0.06 | 4.1% | 106 | [doc](entries/DB-27-db_1h_fresh72_v1-setB-20260823-029.md) |
| 20260823-028 | 2026-08-23 | DB-26 | db_1h_fresh24_v1 | B | binance_vision | `fail` | 0.05 | 3.9% | 99 | [doc](entries/DB-26-db_1h_fresh24_v1-setB-20260823-028.md) |
| 20260823-027 | 2026-08-23 | DB-25 | db_1h_fresh48_v1 | B | binance_vision | `pass` | 0.08 | 3.6% | 103 | [doc](entries/DB-25-db_1h_fresh48_v1-setB-20260823-027.md) |
| 20260823-026 | 2026-08-23 | DB-24 | db_1h_reclaim_v1 | B | binance_vision | `fail` | -0.08 | 7.1% | 94 | [doc](entries/DB-24-db_1h_reclaim_v1-setB-20260823-026.md) |
| 20260823-025 | 2026-08-23 | DB-23 | db_1h_not_down_v1 | B | binance_vision | `fail` | 0.04 | 5.3% | 79 | [doc](entries/DB-23-db_1h_not_down_v1-setB-20260823-025.md) |
| 20260823-024 | 2026-08-23 | DB-22 | db_1h_up_only_v1 | B | binance_vision | `fail` | -0.32 | 5.5% | 37 | [doc](entries/DB-22-db_1h_up_only_v1-setB-20260823-024.md) |
| 20260823-023 | 2026-08-23 | DB-21 | db_1h_up_fresh_reclaim_v1 | B | binance_vision | `fail` | -0.31 | 4.1% | 27 | [doc](entries/DB-21-db_1h_up_fresh_reclaim_v1-setB-20260823-023.md) |
| 20260823-022 | 2026-08-23 | DB-10 | db_struct_1h_v1 | C | binance_vision | `fail` | -0.10 | 11.1% | 209 | [doc](entries/DB-10-db_struct_1h_v1-setC-20260823-022.md) |
| 20260823-021 | 2026-08-23 | DB-20 | db_1h_up_pct_height_v1 | B | binance_vision | `fail` | -0.48 | 4.2% | 23 | [doc](entries/DB-20-db_1h_up_pct_height_v1-setB-20260823-021.md) |
| 20260823-020 | 2026-08-23 | DB-19 | db_trail_atr_v1 | B | binance_vision | `fail` | 0.33 | 2.9% | 34 | [doc](entries/DB-19-db_trail_atr_v1-setB-20260823-020.md) |
| 20260823-019 | 2026-08-23 | DB-18 | db_session_lon_ny_v1 | B | binance_vision | `fail` | 0.12 | 1.8% | 21 | [doc](entries/DB-18-db_session_lon_ny_v1-setB-20260823-019.md) |
| 20260823-018 | 2026-08-23 | DB-17 | db_mirror_short_v1 | B | binance_vision | `fail` | -0.47 | 9.6% | 50 | [doc](entries/DB-17-db_mirror_short_v1-setB-20260823-018.md) |
| 20260823-017 | 2026-08-23 | DB-16 | db_first_retest_only_v1 | B | binance_vision | `fail` | -0.03 | 2.9% | 31 | [doc](entries/DB-16-db_first_retest_only_v1-setB-20260823-017.md) |
| 20260823-016 | 2026-08-23 | DB-15 | db_clean_break_v1 | B | binance_vision | `fail` | -0.05 | 2.5% | 32 | [doc](entries/DB-15-db_clean_break_v1-setB-20260823-016.md) |
| 20260823-015 | 2026-08-23 | DB-14 | db_retest_fresh_v1 | B | binance_vision | `fail` | 0.49 | 1.9% | 24 | [doc](entries/DB-14-db_retest_fresh_v1-setB-20260823-015.md) |
| 20260823-014 | 2026-08-23 | DB-13 | db_entry_break_bounce_high_v1 | B | binance_vision | `fail` | -0.12 | 3.4% | 22 | [doc](entries/DB-13-db_entry_break_bounce_high_v1-setB-20260823-014.md) |
| 20260823-013 | 2026-08-23 | DB-12 | db_stop_at_bottom_v1 | B | binance_vision | `fail` | 0.11 | 2.9% | 34 | [doc](entries/DB-12-db_stop_at_bottom_v1-setB-20260823-013.md) |
| 20260823-012 | 2026-08-23 | DB-11 | db_struct_daily_v1 | B | binance_vision | `fail` | -1.86 | 3.2% | 5 | [doc](entries/DB-11-db_struct_daily_v1-setB-20260823-012.md) |
| 20260823-011 | 2026-08-23 | DB-10 | db_struct_1h_v1 | B | binance_vision | `pass` | 0.00 | 6.0% | 109 | [doc](entries/DB-10-db_struct_1h_v1-setB-20260823-011.md) |
| 20260823-010 | 2026-08-23 | DB-09 | db_wick_break_v1 | B | binance_vision | `fail` | -0.11 | 3.2% | 30 | [doc](entries/DB-09-db_wick_break_v1-setB-20260823-010.md) |
| 20260823-009 | 2026-08-23 | DB-08 | db_wide_bottoms_v1 | B | binance_vision | `fail` | 0.32 | 2.6% | 41 | [doc](entries/DB-08-db_wide_bottoms_v1-setB-20260823-009.md) |
| 20260823-008 | 2026-08-23 | DB-07 | db_tight_bottoms_v1 | B | binance_vision | `fail` | -0.35 | 4.1% | 26 | [doc](entries/DB-07-db_tight_bottoms_v1-setB-20260823-008.md) |
| 20260823-007 | 2026-08-23 | DB-06 | db_bounce_fixed_pct_v1 | B | binance_vision | `fail` | -0.12 | 2.9% | 36 | [doc](entries/DB-06-db_bounce_fixed_pct_v1-setB-20260823-007.md) |
| 20260823-006 | 2026-08-23 | DB-05 | db_bounce_pct_height_v1 | B | binance_vision | `fail` | -0.18 | 4.2% | 24 | [doc](entries/DB-05-db_bounce_pct_height_v1-setB-20260823-006.md) |
| 20260823-005 | 2026-08-23 | DB-04 | db_bounce_reclaim_ext_v1 | B | binance_vision | `fail` | 0.23 | 1.8% | 25 | [doc](entries/DB-04-db_bounce_reclaim_ext_v1-setB-20260823-005.md) |
| 20260823-004 | 2026-08-23 | DB-03 | db_htf_not_down_v1 | B | binance_vision | `fail` | 0.24 | 2.7% | 26 | [doc](entries/DB-03-db_htf_not_down_v1-setB-20260823-004.md) |
| 20260823-003 | 2026-08-23 | DB-02 | db_htf_up_only_v1 | B | binance_vision | `fail` | 0.55 | 1.8% | 11 | [doc](entries/DB-02-db_htf_up_only_v1-setB-20260823-003.md) |
| 20260823-002 | 2026-08-23 | DB-01 | db_baseline_v1 | B | binance_vision | `fail` | 0.18 | 2.6% | 34 | [doc](entries/DB-01-db_baseline_v1-setB-20260823-002.md) |
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

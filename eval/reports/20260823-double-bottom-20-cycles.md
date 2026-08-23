# SPOT-001 ダブルボトム — 20サイクル Formal Set B

実行UTC: 2026-08-23T01:04:23Z

## min_trades 注記

- `min_trades=100` は **Set B（1年）合計**。1ヶ月100ではない。
- 足は最短15m執行（1分未満は禁止）。

## サマリー

| C# | logic | knob | Gate | EV | DD | n | failures |
|----|-------|------|------|----|----|---|----------|
| 1 | `db_baseline_v1` | 基準 | FAIL | 0.178 | 2.6% | 34 | min_trades |
| 2 | `db_htf_up_only_v1` | D1 上昇のみ | FAIL | 0.551 | 1.8% | 11 | min_trades |
| 3 | `db_htf_not_down_v1` | D1 下降以外 | FAIL | 0.243 | 2.7% | 26 | min_trades |
| 4 | `db_bounce_reclaim_ext_v1` | C2 高値奪還 | FAIL | 0.234 | 1.8% | 25 | min_trades |
| 5 | `db_bounce_pct_height_v1` | C2 高%戻し | FAIL | -0.180 | 4.2% | 24 | expectancy,min_trades |
| 6 | `db_bounce_fixed_pct_v1` | C2 固定% | FAIL | -0.120 | 2.9% | 36 | expectancy,min_trades |
| 7 | `db_tight_bottoms_v1` | A3 厳しい2底 | FAIL | -0.353 | 4.1% | 26 | expectancy,min_trades |
| 8 | `db_wide_bottoms_v1` | A3 緩い2底 | FAIL | 0.322 | 2.6% | 41 | min_trades |
| 9 | `db_wick_break_v1` | B1 ヒゲ突破 | FAIL | -0.106 | 3.2% | 30 | expectancy,min_trades |
| 10 | `db_struct_1h_v1` | A1 1H構造 | PASS | 0.004 | 6.0% | 109 | — |
| 11 | `db_struct_daily_v1` | A1 日足構造 | FAIL | -1.858 | 3.2% | 5 | expectancy,min_trades |
| 12 | `db_stop_at_bottom_v1` | E1 第2底損切 | FAIL | 0.106 | 2.9% | 34 | min_trades |
| 13 | `db_entry_break_bounce_high_v1` | C2 反発高抜け | FAIL | -0.119 | 3.4% | 22 | expectancy,min_trades |
| 14 | `db_retest_fresh_v1` | B2 鮮度 | FAIL | 0.491 | 1.9% | 24 | min_trades |
| 15 | `db_clean_break_v1` | B1 きれいな突破 | FAIL | -0.052 | 2.5% | 32 | expectancy,min_trades |
| 16 | `db_first_retest_only_v1` | C1 初回のみ | FAIL | -0.028 | 2.9% | 31 | expectancy,min_trades |
| 17 | `db_mirror_short_v1` | 対称ショート | FAIL | -0.471 | 9.6% | 50 | expectancy,min_trades |
| 18 | `db_session_lon_ny_v1` | セッション | FAIL | 0.122 | 1.8% | 21 | min_trades |
| 19 | `db_trail_atr_v1` | E2 ATRトレール | FAIL | 0.326 | 2.9% | 34 | min_trades |
| 20 | `db_1h_up_pct_height_v1` | 事前合成 | FAIL | -0.477 | 4.2% | 23 | expectancy,min_trades |

## サイクル詳細

### C01 — `db_baseline_v1`

- **ノブ:** 基準
- **なぜこの測り方:** 仮説の最小実装。変数なしのベースライン。
- **結果:** n=34 / EV=0.17767277778434348 / DD=2.6437951774693316 / fail=min_trades
- **report:** `eval/reports/20260823T010425Z_db_baseline_v1_setB.md`

### C02 — `db_htf_up_only_v1`

- **ノブ:** D1 上昇のみ
- **なぜこの測り方:** 上位上昇でのみ取るか。
- **結果:** n=11 / EV=0.5505082306040072 / DD=1.7947623401104114 / fail=min_trades 前回比 trades -23.
- **report:** `eval/reports/20260823T010427Z_db_htf_up_only_v1_setB.md`

### C03 — `db_htf_not_down_v1`

- **ノブ:** D1 下降以外
- **なぜこの測り方:** レンジ許容の差を見る。
- **結果:** n=26 / EV=0.24252883347119583 / DD=2.654517211148142 / fail=min_trades 前回比 trades +15.
- **report:** `eval/reports/20260823T010430Z_db_htf_not_down_v1_setB.md`

### C04 — `db_bounce_reclaim_ext_v1`

- **ノブ:** C2 高値奪還
- **なぜこの測り方:** ロング焼き後の本確定の測り方。
- **結果:** n=25 / EV=0.23396246757515776 / DD=1.7531926994113736 / fail=min_trades 前回比 trades -1.
- **report:** `eval/reports/20260823T010432Z_db_bounce_reclaim_ext_v1_setB.md`

### C05 — `db_bounce_pct_height_v1`

- **ノブ:** C2 高%戻し
- **なぜこの測り方:** DBスケールに比例した反発。
- **結果:** n=24 / EV=-0.180419827228842 / DD=4.153078408457836 / fail=expectancy,min_trades 前回比 trades -1.
- **report:** `eval/reports/20260823T010434Z_db_bounce_pct_height_v1_setB.md`

### C06 — `db_bounce_fixed_pct_v1`

- **ノブ:** C2 固定%
- **なぜこの測り方:** 固定反発の対照。
- **結果:** n=36 / EV=-0.11957176088568738 / DD=2.9300171673087507 / fail=expectancy,min_trades 前回比 trades +12.
- **report:** `eval/reports/20260823T010436Z_db_bounce_fixed_pct_v1_setB.md`

### C07 — `db_tight_bottoms_v1`

- **ノブ:** A3 厳しい2底
- **なぜこの測り方:** 形の質を上げる。
- **結果:** n=26 / EV=-0.35254012073515184 / DD=4.0586841857144424 / fail=expectancy,min_trades 前回比 trades -10.
- **report:** `eval/reports/20260823T010438Z_db_tight_bottoms_v1_setB.md`

### C08 — `db_wide_bottoms_v1`

- **ノブ:** A3 緩い2底
- **なぜこの測り方:** サンプル増とノイズのトレードオフ。
- **結果:** n=41 / EV=0.32209182277355486 / DD=2.619566100936768 / fail=min_trades 前回比 trades +15.
- **report:** `eval/reports/20260823T010441Z_db_wide_bottoms_v1_setB.md`

### C09 — `db_wick_break_v1`

- **ノブ:** B1 ヒゲ突破
- **なぜこの測り方:** 終値より早い突破定義。
- **結果:** n=30 / EV=-0.10623373462128209 / DD=3.240385214265488 / fail=expectancy,min_trades 前回比 trades -11.
- **report:** `eval/reports/20260823T010443Z_db_wick_break_v1_setB.md`

### C10 — `db_struct_1h_v1`

- **ノブ:** A1 1H構造
- **なぜこの測り方:** 回数不足対策（1m未満は禁止）。
- **結果:** n=109 / EV=0.004070949322216269 / DD=6.005026386165772 前回比 trades +79.
- **report:** `eval/reports/20260823T010445Z_db_struct_1h_v1_setB.md`

### C11 — `db_struct_daily_v1`

- **ノブ:** A1 日足構造
- **なぜこの測り方:** より厚いが希少。
- **結果:** n=5 / EV=-1.8583801578684984 / DD=3.1570487926235082 / fail=expectancy,min_trades 前回比 trades -104.
- **report:** `eval/reports/20260823T010447Z_db_struct_daily_v1_setB.md`

### C12 — `db_stop_at_bottom_v1`

- **ノブ:** E1 第2底損切
- **なぜこの測り方:** 無効化を構造に合わせる。
- **結果:** n=34 / EV=0.10625563500686007 / DD=2.9044233844359546 / fail=min_trades 前回比 trades +29.
- **report:** `eval/reports/20260823T010449Z_db_stop_at_bottom_v1_setB.md`

### C13 — `db_entry_break_bounce_high_v1`

- **ノブ:** C2 反発高抜け
- **なぜこの測り方:** 遅延エントリーでダマシ削減。
- **結果:** n=22 / EV=-0.11896709289979857 / DD=3.3699290513690556 / fail=expectancy,min_trades 前回比 trades -12.
- **report:** `eval/reports/20260823T010452Z_db_entry_break_bounce_high_v1_setB.md`

### C14 — `db_retest_fresh_v1`

- **ノブ:** B2 鮮度
- **なぜこの測り方:** 古い突破の再テストを捨てる。
- **結果:** n=24 / EV=0.4909417529129649 / DD=1.8621374622676778 / fail=min_trades 前回比 trades +2.
- **report:** `eval/reports/20260823T010454Z_db_retest_fresh_v1_setB.md`

### C15 — `db_clean_break_v1`

- **ノブ:** B1 きれいな突破
- **なぜこの測り方:** 弱い突破を捨てる。
- **結果:** n=32 / EV=-0.0518132819301001 / DD=2.5130416644097275 / fail=expectancy,min_trades 前回比 trades +8.
- **report:** `eval/reports/20260823T010456Z_db_clean_break_v1_setB.md`

### C16 — `db_first_retest_only_v1`

- **ノブ:** C1 初回のみ
- **なぜこの測り方:** 二度目以降の薄さ回避。
- **結果:** n=31 / EV=-0.028469471185153604 / DD=2.9080691050932423 / fail=expectancy,min_trades 前回比 trades -1.
- **report:** `eval/reports/20260823T010458Z_db_first_retest_only_v1_setB.md`

### C17 — `db_mirror_short_v1`

- **ノブ:** 対称ショート
- **なぜこの測り方:** ロング一辺倒の対照実験。
- **結果:** n=50 / EV=-0.4713940667677943 / DD=9.594967753384784 / fail=expectancy,min_trades 前回比 trades +19.
- **report:** `eval/reports/20260823T010501Z_db_mirror_short_v1_setB.md`

### C18 — `db_session_lon_ny_v1`

- **ノブ:** セッション
- **なぜこの測り方:** 薄い時間の執行を避ける。
- **結果:** n=21 / EV=0.12161742685742542 / DD=1.7925250430864847 / fail=min_trades 前回比 trades -29.
- **report:** `eval/reports/20260823T010503Z_db_session_lon_ny_v1_setB.md`

### C19 — `db_trail_atr_v1`

- **ノブ:** E2 ATRトレール
- **なぜこの測り方:** 大勝ちを残す退出。
- **結果:** n=34 / EV=0.32593394230270806 / DD=2.9064171245320067 / fail=min_trades 前回比 trades +13.
- **report:** `eval/reports/20260823T010505Z_db_trail_atr_v1_setB.md`

### C20 — `db_1h_up_pct_height_v1`

- **ノブ:** 事前合成
- **なぜこの測り方:** 1H×上昇×高%戻し（結果見て選ばない事前宣言）。
- **結果:** n=23 / EV=-0.4771759433160435 / DD=4.192122260279149 / fail=expectancy,min_trades 前回比 trades -11.
- **report:** `eval/reports/20260823T010508Z_db_1h_up_pct_height_v1_setB.md`

## 総括

- Gate PASS (Set B): **1** / 20 → `db_struct_1h_v1`
- 最多トレード: `db_struct_1h_v1` n=109
- 最良EV（サンプル不足込み）: `db_htf_up_only_v1` EV≈+0.55（n=11）
- **Holdout Set C (`db_struct_1h_v1`): FAIL** — EV **-0.10** / DD 11.1% / n=209 → **デモ不可**

### 構造的学び（20サイクル後）

1. **回数:** 4H構造では多くが n=20–40 で `min_trades=100`（**年次**）に届かない。1H構造だけが n≥100 を達成。
2. **品質 vs 回数:** EVが厚いのは上位上昇フィルタ・鮮度・高値奪還など「絞る」測り方。ただし n が足りない。1Hは回数は足りるが Set B のEVはほぼゼロ、Set C でマイナス。
3. **反発定義:** 陽線反発・高値奪還はEVプラス寄り。固定%・DB高%戻し・厳しい2底はEVマイナス寄り。
4. **対称ショート**は悪化。この仮説はロング構造が本体。
5. **EMAは未使用。** 上位バイアスはスイング高低の切上げ/切下げ。
6. Set B PASSでも holdout で崩れる → 「ゲート通過＝採用」ではない（今回で実証）。

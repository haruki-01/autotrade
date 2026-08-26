# SPOT-001 ダブルボトム — 検証30サイクル（DB-22..DB-51）

実行UTC: 2026-08-23T02:01:04Z

## 方針

- DB-21（質ノブの積）失敗を受け、**1H/15m/4H基点でノブは1点のみ**
- `min_trades=100` は **Set B 1年合計**（月次ではない）
- 足は15m以上（1分未満禁止）
- EMA不使用

## サマリー

| C# | logic | knob | Gate | EV | DD | n | failures |
|----|-------|------|------|----|----|---|----------|
| 22 | `db_1h_up_only_v1` | 1H+上昇 | FAIL | -0.319 | 5.5% | 37 | expectancy,min_trades |
| 23 | `db_1h_not_down_v1` | 1H+下降以外 | FAIL | 0.045 | 5.3% | 79 | min_trades |
| 24 | `db_1h_reclaim_v1` | 1H+高値奪還 | FAIL | -0.077 | 7.1% | 94 | expectancy,min_trades |
| 25 | `db_1h_fresh48_v1` | 1H+鮮度48h | PASS | 0.076 | 3.6% | 103 | — |
| 26 | `db_1h_fresh24_v1` | 1H+鮮度24h | FAIL | 0.051 | 3.9% | 99 | min_trades |
| 27 | `db_1h_fresh72_v1` | 1H+鮮度72h | PASS | 0.057 | 4.1% | 106 | — |
| 28 | `db_1h_trail_v1` | 1H+ATRトレール | FAIL | -0.075 | 8.6% | 111 | expectancy |
| 29 | `db_1h_stop_bottom_v1` | 1H+第2底損切 | PASS | 0.017 | 6.6% | 105 | — |
| 30 | `db_1h_tight_v1` | 1H+厳しい2底 | FAIL | 0.033 | 3.5% | 75 | min_trades |
| 31 | `db_1h_wide_v1` | 1H+緩い2底 | PASS | 0.011 | 6.6% | 138 | — |
| 32 | `db_1h_wick_v1` | 1H+ヒゲ突破 | FAIL | -0.012 | 6.6% | 105 | expectancy |
| 33 | `db_1h_clean_v1` | 1H+きれい突破 | PASS | 0.020 | 5.1% | 103 | — |
| 34 | `db_1h_fixed_pct_v1` | 1H+固定%反発 | FAIL | -0.039 | 6.6% | 108 | expectancy |
| 35 | `db_1h_pct_height_v1` | 1H+高%戻し | FAIL | -0.066 | 5.6% | 71 | expectancy,min_trades |
| 36 | `db_1h_break_bh_v1` | 1H+反発高抜け | FAIL | -0.004 | 4.2% | 61 | expectancy,min_trades |
| 37 | `db_1h_first_retest_v1` | 1H+初回のみ | FAIL | -0.025 | 6.8% | 92 | expectancy,min_trades |
| 38 | `db_1h_session_v1` | 1H+セッション | FAIL | 0.030 | 4.2% | 75 | min_trades |
| 39 | `db_1h_pivot2_v1` | 1H+ピボット2 | FAIL | -0.013 | 7.3% | 149 | expectancy |
| 40 | `db_1h_pivot5_v1` | 1H+ピボット5 | FAIL | -0.012 | 4.2% | 77 | expectancy,min_trades |
| 41 | `db_1h_band_tight_v1` | 1H+帯狭い | PASS | 0.013 | 5.3% | 110 | — |
| 42 | `db_1h_band_wide_v1` | 1H+帯広い | PASS | 0.016 | 7.5% | 110 | — |
| 43 | `db_1h_close_bottoms_v1` | 1H+底近い | PASS | 0.064 | 7.0% | 156 | — |
| 44 | `db_1h_far_bottoms_v1` | 1H+底遠い | FAIL | -0.050 | 4.8% | 75 | expectancy,min_trades |
| 45 | `db_15m_baseline_v1` | 15m構造 | FAIL | -0.117 | 27.2% | 486 | expectancy,drawdown |
| 46 | `db_15m_up_only_v1` | 15m+上昇 | FAIL | -0.171 | 12.2% | 167 | expectancy |
| 47 | `db_15m_reclaim_v1` | 15m+奪還 | FAIL | -0.100 | 19.7% | 389 | expectancy |
| 48 | `db_15m_fresh48_v1` | 15m+鮮度 | FAIL | -0.104 | 23.2% | 448 | expectancy,drawdown |
| 49 | `db_4h_band_tight_v1` | 4H+帯狭い | FAIL | 0.519 | 1.7% | 29 | min_trades |
| 50 | `db_4h_pivot2_v1` | 4H+ピボット2 | FAIL | 0.339 | 4.6% | 46 | min_trades |
| 51 | `db_1h_atr_stop_v1` | 1H+ATR損切 | FAIL | -0.035 | 7.6% | 109 | expectancy |

## サイクル詳細

### C22 — `db_1h_up_only_v1`

- **ノブ:** 1H+上昇
- **なぜ:** DB-21積は失敗。上昇フィルタ単体を1Hで見る。
- **結果:** n=37 / EV=-0.318867817369308 / DD=5.499207322039108 / fail=expectancy,min_trades
- **report:** `eval/reports/20260823T020106Z_db_1h_up_only_v1_setB.md`

### C23 — `db_1h_not_down_v1`

- **ノブ:** 1H+下降以外
- **なぜ:** 上昇のみとの差。
- **結果:** n=79 / EV=0.04455243524409276 / DD=5.267822018107517 / fail=min_trades
- **report:** `eval/reports/20260823T020109Z_db_1h_not_down_v1_setB.md`

### C24 — `db_1h_reclaim_v1`

- **ノブ:** 1H+高値奪還
- **なぜ:** 4HでEV+だった反発定義を1H単体で。
- **結果:** n=94 / EV=-0.07709011940730087 / DD=7.139211864234539 / fail=expectancy,min_trades
- **report:** `eval/reports/20260823T020111Z_db_1h_reclaim_v1_setB.md`

### C25 — `db_1h_fresh48_v1`

- **ノブ:** 1H+鮮度48h
- **なぜ:** 鮮度単体。
- **結果:** n=103 / EV=0.07620132204048213 / DD=3.61032143519904 / fail=—
- **report:** `eval/reports/20260823T020114Z_db_1h_fresh48_v1_setB.md`

### C26 — `db_1h_fresh24_v1`

- **ノブ:** 1H+鮮度24h
- **なぜ:** より厳しい鮮度。
- **結果:** n=99 / EV=0.05056418247035305 / DD=3.852746880472525 / fail=min_trades
- **report:** `eval/reports/20260823T020116Z_db_1h_fresh24_v1_setB.md`

### C27 — `db_1h_fresh72_v1`

- **ノブ:** 1H+鮮度72h
- **なぜ:** 緩い鮮度。
- **結果:** n=106 / EV=0.05659641941239489 / DD=4.12013553554006 / fail=—
- **report:** `eval/reports/20260823T020118Z_db_1h_fresh72_v1_setB.md`

### C28 — `db_1h_trail_v1`

- **ノブ:** 1H+ATRトレール
- **なぜ:** 大勝ちを残す退出。
- **結果:** n=111 / EV=-0.07526923869300865 / DD=8.573118226733781 / fail=expectancy
- **report:** `eval/reports/20260823T020121Z_db_1h_trail_v1_setB.md`

### C29 — `db_1h_stop_bottom_v1`

- **ノブ:** 1H+第2底損切
- **なぜ:** 構造損切。
- **結果:** n=105 / EV=0.01731085201757844 / DD=6.587222000426518 / fail=—
- **report:** `eval/reports/20260823T020123Z_db_1h_stop_bottom_v1_setB.md`

### C30 — `db_1h_tight_v1`

- **ノブ:** 1H+厳しい2底
- **なぜ:** 形の質。
- **結果:** n=75 / EV=0.03344089328807849 / DD=3.5058455268054853 / fail=min_trades
- **report:** `eval/reports/20260823T020126Z_db_1h_tight_v1_setB.md`

### C31 — `db_1h_wide_v1`

- **ノブ:** 1H+緩い2底
- **なぜ:** サンプル増。
- **結果:** n=138 / EV=0.011285751405427898 / DD=6.616544742351815 / fail=—
- **report:** `eval/reports/20260823T020128Z_db_1h_wide_v1_setB.md`

### C32 — `db_1h_wick_v1`

- **ノブ:** 1H+ヒゲ突破
- **なぜ:** 突破定義。
- **結果:** n=105 / EV=-0.012103974403540628 / DD=6.632623169026752 / fail=expectancy
- **report:** `eval/reports/20260823T020131Z_db_1h_wick_v1_setB.md`

### C33 — `db_1h_clean_v1`

- **ノブ:** 1H+きれい突破
- **なぜ:** 弱い突破排除。
- **結果:** n=103 / EV=0.019643010960497198 / DD=5.077387961800744 / fail=—
- **report:** `eval/reports/20260823T020133Z_db_1h_clean_v1_setB.md`

### C34 — `db_1h_fixed_pct_v1`

- **ノブ:** 1H+固定%反発
- **なぜ:** 反発対照。
- **結果:** n=108 / EV=-0.03919053023428055 / DD=6.623548076154527 / fail=expectancy
- **report:** `eval/reports/20260823T020136Z_db_1h_fixed_pct_v1_setB.md`

### C35 — `db_1h_pct_height_v1`

- **ノブ:** 1H+高%戻し
- **なぜ:** DB-20から上昇フィルタを外した単体。
- **結果:** n=71 / EV=-0.0658226165945276 / DD=5.564647662580699 / fail=expectancy,min_trades
- **report:** `eval/reports/20260823T020138Z_db_1h_pct_height_v1_setB.md`

### C36 — `db_1h_break_bh_v1`

- **ノブ:** 1H+反発高抜け
- **なぜ:** 遅延エントリー。
- **結果:** n=61 / EV=-0.003743394284751985 / DD=4.167866852559838 / fail=expectancy,min_trades
- **report:** `eval/reports/20260823T020140Z_db_1h_break_bh_v1_setB.md`

### C37 — `db_1h_first_retest_v1`

- **ノブ:** 1H+初回のみ
- **なぜ:** 二度目以降を捨てる。
- **結果:** n=92 / EV=-0.024786805021700366 / DD=6.756272389515358 / fail=expectancy,min_trades
- **report:** `eval/reports/20260823T020143Z_db_1h_first_retest_v1_setB.md`

### C38 — `db_1h_session_v1`

- **ノブ:** 1H+セッション
- **なぜ:** 薄い時間回避。
- **結果:** n=75 / EV=0.030146438634779425 / DD=4.184246624538896 / fail=min_trades
- **report:** `eval/reports/20260823T020145Z_db_1h_session_v1_setB.md`

### C39 — `db_1h_pivot2_v1`

- **ノブ:** 1H+ピボット2
- **なぜ:** 検出感度↑。
- **結果:** n=149 / EV=-0.012829206558463882 / DD=7.2580483687219965 / fail=expectancy
- **report:** `eval/reports/20260823T020148Z_db_1h_pivot2_v1_setB.md`

### C40 — `db_1h_pivot5_v1`

- **ノブ:** 1H+ピボット5
- **なぜ:** 検出感度↓。
- **結果:** n=77 / EV=-0.012475054973193692 / DD=4.237435836657805 / fail=expectancy,min_trades
- **report:** `eval/reports/20260823T020150Z_db_1h_pivot5_v1_setB.md`

### C41 — `db_1h_band_tight_v1`

- **ノブ:** 1H+帯狭い
- **なぜ:** ネックタッチ精度。
- **結果:** n=110 / EV=0.012957741178531115 / DD=5.311853677827234 / fail=—
- **report:** `eval/reports/20260823T020153Z_db_1h_band_tight_v1_setB.md`

### C42 — `db_1h_band_wide_v1`

- **ノブ:** 1H+帯広い
- **なぜ:** タッチ取りこぼし減。
- **結果:** n=110 / EV=0.015916654607765077 / DD=7.481869795226821 / fail=—
- **report:** `eval/reports/20260823T020155Z_db_1h_band_wide_v1_setB.md`

### C43 — `db_1h_close_bottoms_v1`

- **ノブ:** 1H+底近い
- **なぜ:** 時間間隔。
- **結果:** n=156 / EV=0.06377122573499767 / DD=6.983766459998529 / fail=—
- **report:** `eval/reports/20260823T020158Z_db_1h_close_bottoms_v1_setB.md`

### C44 — `db_1h_far_bottoms_v1`

- **ノブ:** 1H+底遠い
- **なぜ:** より大きなDB。
- **結果:** n=75 / EV=-0.05041493273742723 / DD=4.82444214801032 / fail=expectancy,min_trades
- **report:** `eval/reports/20260823T020200Z_db_1h_far_bottoms_v1_setB.md`

### C45 — `db_15m_baseline_v1`

- **ノブ:** 15m構造
- **なぜ:** 回数確保（1m未満禁止の下限に近い）。
- **結果:** n=486 / EV=-0.11706670540825741 / DD=27.1900657478655 / fail=expectancy,drawdown
- **report:** `eval/reports/20260823T020205Z_db_15m_baseline_v1_setB.md`

### C46 — `db_15m_up_only_v1`

- **ノブ:** 15m+上昇
- **なぜ:** 15mに質フィルタ1点。
- **結果:** n=167 / EV=-0.1705317191314166 / DD=12.24219908349545 / fail=expectancy
- **report:** `eval/reports/20260823T020211Z_db_15m_up_only_v1_setB.md`

### C47 — `db_15m_reclaim_v1`

- **ノブ:** 15m+奪還
- **なぜ:** 15mに反発定義。
- **結果:** n=389 / EV=-0.10019987285663098 / DD=19.73258837228084 / fail=expectancy
- **report:** `eval/reports/20260823T020216Z_db_15m_reclaim_v1_setB.md`

### C48 — `db_15m_fresh48_v1`

- **ノブ:** 15m+鮮度
- **なぜ:** 15mに鮮度。
- **結果:** n=448 / EV=-0.10419548010931197 / DD=23.165091483257974 / fail=expectancy,drawdown
- **report:** `eval/reports/20260823T020221Z_db_15m_fresh48_v1_setB.md`

### C49 — `db_4h_band_tight_v1`

- **ノブ:** 4H+帯狭い
- **なぜ:** 4H残りノブ。
- **結果:** n=29 / EV=0.5192428253144338 / DD=1.6905511079211948 / fail=min_trades
- **report:** `eval/reports/20260823T020223Z_db_4h_band_tight_v1_setB.md`

### C50 — `db_4h_pivot2_v1`

- **ノブ:** 4H+ピボット2
- **なぜ:** 4H感度。
- **結果:** n=46 / EV=0.3386409568319565 / DD=4.622442147650947 / fail=min_trades
- **report:** `eval/reports/20260823T020225Z_db_4h_pivot2_v1_setB.md`

### C51 — `db_1h_atr_stop_v1`

- **ノブ:** 1H+ATR損切
- **なぜ:** 損切定義の単体。
- **結果:** n=109 / EV=-0.034915118956515015 / DD=7.5721130806710475 / fail=expectancy
- **report:** `eval/reports/20260823T020228Z_db_1h_atr_stop_v1_setB.md`

## 総括

- Set B Gate PASS: **8** / 30
- 最多n: `db_15m_baseline_v1` n=486（ただし EV マイナス・DD超過）
- 最良EV（n問わず）: `db_4h_band_tight_v1` EV≈+0.52（n=29・回数不足）
- **Set C holdout: 8/8 FAIL（すべて EV マイナス）→ デモ/本番不可**

### Set B PASS → Set C holdout

| logic | B EV | B n | C EV | C n | C Gate |
|-------|------|-----|------|-----|--------|
| `db_1h_fresh48_v1` | +0.076 | 103 | **-0.120** | 192 | FAIL |
| `db_1h_close_bottoms_v1` | +0.064 | 156 | **-0.083** | 292 | FAIL |
| `db_1h_fresh72_v1` | +0.057 | 106 | **-0.123** | 196 | FAIL |
| `db_1h_clean_v1` | +0.020 | 103 | **-0.132** | 210 | FAIL |
| `db_1h_stop_bottom_v1` | +0.017 | 105 | **-0.125** | 207 | FAIL |
| `db_1h_band_wide_v1` | +0.016 | 110 | **-0.114** | 211 | FAIL |
| `db_1h_band_tight_v1` | +0.013 | 110 | **-0.070** | 208 | FAIL |
| `db_1h_wide_v1` | +0.011 | 138 | **-0.066** | 273 | FAIL |

Holdout JSON: `eval/reports/20260823-double-bottom-30-holdout-C.json`

### 構造的学び

1. **1H+ノブ1点**で Set B を通るものは増えたが、いずれも EV が薄く **Set C で符号反転**。
2. **15m構造**は回数は十分だが費用負け（EVマイナス・一部DD超過）。短足だけでは解決しない。
3. **4H**は依然 EV 厚めだが年次 n 不足。質と回数のトレードオフは未解消。
4. 鮮度・底間隔・きれいな突破は相対的にマシだが、holdout耐性なし → 現行ファミリーは採用しない。
5. EMA不使用。1分未満の足は未使用。

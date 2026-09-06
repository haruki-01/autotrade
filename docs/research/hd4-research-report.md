# H-D4 研究ループレポート（30 サイクル）

生成: 2026-09-06T11:58:42.739304+00:00
サンプル: 2024-01-01..2026-08-31

## エグゼクティブサマリー

- **全局最良**: break_2.0%_sw72_pull_cd144_mb48
- mode=break, pct=2.0%, swing=72, entry=pull
- 執行込み OOS 月次 P ≈ **¥311**（Gate2 目標 ¥1,500）
- EV ≈ ¥30.3, N ≈ 10.3/月, W = 61.5%
- 劣化率 = 1.14
- Gate1 = False / Gate2 = False / verdict = **fail**

## 全局 best P の推移

| Cycle | Best OOS P |
|---:|---:|
| 1 | ¥-45 |
| 2 | ¥19 |
| 3 | ¥67 |
| 4 | ¥67 |
| 5 | ¥247 |
| 6 | ¥247 |
| 7 | ¥247 |
| 8 | ¥247 |
| 9 | ¥247 |
| 10 | ¥247 |
| 11 | ¥247 |
| 12 | ¥247 |
| 13 | ¥247 |
| 14 | ¥247 |
| 15 | ¥247 |
| 16 | ¥247 |
| 17 | ¥247 |
| 18 | ¥247 |
| 19 | ¥247 |
| 20 | ¥247 |
| 21 | ¥247 |
| 22 | ¥311 |
| 23 | ¥311 |
| 24 | ¥311 |
| 25 | ¥311 |
| 26 | ¥311 |
| 27 | ¥311 |
| 28 | ¥311 |
| 29 | ¥311 |
| 30 | ¥311 |

## サイクル履歴（30）

### Cycle 1: H1: Phase0 再現 — break@−1.5%/−2.0% vs bounce@−1.0%/−1.2%（執行込み Gate1/2）

- テスト: 4 / Gate1: 0 / Gate2: 0 / stale: 0
- Best: break_2.0%_sw24_immediate_cd48_mb48 (P≈¥-45)
- **Learning**: 最良 break_2.0%_sw24_immediate_cd48_mb48: 執行P≈¥-45, EV≈¥-6.4, N≈8.5/月, W=33.3% → EV≤0。mode 反転 or pct_level 変更。 → N<40。cooldown 短縮 or pct 浅く。
- **次仮説**: mode=bounce へ pivot、または pct_level ±0.2%

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_1.5%_sw24_immediate_cd48_mb48 | ¥-164 | ¥-9.2 | 31.6% | 17.9 | N | N |
| break_2.0%_sw24_immediate_cd48_mb48 | ¥-45 | ¥-6.4 | 33.3% | 8.5 | N | N |
| bounce_1.0%_sw24_immediate_cd48_mb48 | ¥-232 | ¥-6.3 | 35.8% | 36.2 | N | N |
| bounce_1.2%_sw24_immediate_cd48_mb48 | ¥-96 | ¥-3.5 | 37.2% | 27.4 | N | N |

### Cycle 2: H2: cooldown グリッド — N 帯 40–60 へ（best mode=break）

- テスト: 5 / Gate1: 0 / Gate2: 0 / stale: 0
- Best: break_2.0%_sw24_immediate_cd144_mb48 (P≈¥19)
- **Learning**: 最良 break_2.0%_sw24_immediate_cd144_mb48: 執行P≈¥19, EV≈¥2.2, N≈6.5/月, W=37.3% → EV>0 だが P 不足（N=6.5）。cooldown/N 調整。 → 執行劣化大。理論 pass でも promote 不可。 → N<40。cooldown 短縮 or pct 浅く。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_2.0%_sw24_immediate_cd24_mb48 | ¥-5 | ¥-1.6 | 35.7% | 10.0 | N | N |
| break_2.0%_sw24_immediate_cd48_mb48 | ¥-45 | ¥-6.4 | 33.3% | 8.5 | N | N |
| break_2.0%_sw24_immediate_cd72_mb48 | ¥15 | ¥0.9 | 39.0% | 7.7 | N | N |
| break_2.0%_sw24_immediate_cd96_mb48 | ¥6 | ¥-0.5 | 35.4% | 7.1 | N | N |
| break_2.0%_sw24_immediate_cd144_mb48 | ¥19 | ¥2.2 | 37.3% | 6.5 | N | N |

### Cycle 3: H3: スイング lookback（12/24/48）— 群集水準の定義

- テスト: 3 / Gate1: 0 / Gate2: 0 / stale: 0
- Best: break_2.0%_sw48_immediate_cd144_mb48 (P≈¥67)
- **Learning**: 最良 break_2.0%_sw48_immediate_cd144_mb48: 執行P≈¥67, EV≈¥7.5, N≈8.9/月, W=44.7% → EV>0 だが P 不足（N=8.9）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_2.0%_sw12_immediate_cd144_mb48 | ¥-31 | ¥-8.5 | 32.0% | 4.3 | N | N |
| break_2.0%_sw24_immediate_cd144_mb48 | ¥19 | ¥2.2 | 37.3% | 6.5 | N | N |
| break_2.0%_sw48_immediate_cd144_mb48 | ¥67 | ¥7.5 | 44.7% | 8.9 | N | N |

### Cycle 4: H4: pct_level fine-tune（±0.2%/0.4%）

- テスト: 3 / Gate1: 0 / Gate2: 0 / stale: 1
- Best: break_1.8%_sw48_immediate_cd144_mb48 (P≈¥63)
- **Learning**: 最良 break_1.8%_sw48_immediate_cd144_mb48: 執行P≈¥63, EV≈¥5.5, N≈11.1/月, W=42.6% → EV>0 だが P 不足（N=11.1）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_1.8%_sw48_immediate_cd144_mb48 | ¥63 | ¥5.5 | 42.6% | 11.1 | N | N |
| break_2.2%_sw48_immediate_cd144_mb48 | ¥-7 | ¥-2.5 | 36.1% | 7.4 | N | N |
| break_2.4%_sw48_immediate_cd144_mb48 | ¥11 | ¥0.6 | 38.0% | 5.6 | N | N |

### Cycle 5: H5: 即入り vs 押し待ち（H-D PULL 教訓の転用）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 0
- Best: break_2.0%_sw48_pull_cd144_mb48 (P≈¥247)
- **Learning**: 最良 break_2.0%_sw48_pull_cd144_mb48: 執行P≈¥247, EV≈¥27.2, N≈9.1/月, W=59.5% → EV>0 だが P 不足（N=9.1）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_2.0%_sw48_immediate_cd144_mb48 | ¥67 | ¥7.5 | 44.7% | 8.9 | N | N |
| break_2.0%_sw48_pull_cd144_mb48 | ¥247 | ¥27.2 | 59.5% | 9.1 | N | N |

### Cycle 6: H6: Exit — fixed pct vs RR 1:3 ATR

- テスト: 3 / Gate1: 0 / Gate2: 0 / stale: 1
- Best: break_2.0%_sw48_pull_cd144_mb48 (P≈¥247)
- **Learning**: 最良 break_2.0%_sw48_pull_cd144_mb48: 執行P≈¥247, EV≈¥27.2, N≈9.1/月, W=59.5% → EV>0 だが P 不足（N=9.1）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_2.0%_sw48_pull_cd144_mb48 | ¥247 | ¥27.2 | 59.5% | 9.1 | N | N |
| break_2.0%_sw48_pull_cd144_mb48 | ¥191 | ¥21.5 | 54.0% | 8.7 | N | N |
| break_2.0%_sw48_pull_cd144_mb48 | ¥112 | ¥12.4 | 50.2% | 8.8 | N | N |

### Cycle 7: H7: max_bars（h60/h240/h360 相当）

- テスト: 3 / Gate1: 0 / Gate2: 0 / stale: 2
- Best: break_2.0%_sw48_pull_cd144_mb48 (P≈¥247)
- **Learning**: 最良 break_2.0%_sw48_pull_cd144_mb48: 執行P≈¥247, EV≈¥27.2, N≈9.1/月, W=59.5% → EV>0 だが P 不足（N=9.1）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_2.0%_sw48_pull_cd144_mb24 | ¥181 | ¥20.4 | 55.9% | 8.7 | N | N |
| break_2.0%_sw48_pull_cd144_mb48 | ¥247 | ¥27.2 | 59.5% | 9.1 | N | N |
| break_2.0%_sw48_pull_cd144_mb72 | ¥235 | ¥26.0 | 56.7% | 9.0 | N | N |

### Cycle 8: H8: cooldown 72/96/120 — N 帯へ（auto 代替）

- テスト: 3 / Gate1: 0 / Gate2: 0 / stale: 3
- Best: break_2.0%_sw48_pull_cd120_mb48 (P≈¥214)
- **Learning**: 最良 break_2.0%_sw48_pull_cd120_mb48: 執行P≈¥214, EV≈¥22.5, N≈9.5/月, W=55.1% → EV>0 だが P 不足（N=9.5）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 3 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_2.0%_sw48_pull_cd72_mb48 | ¥194 | ¥18.0 | 51.6% | 10.5 | N | N |
| break_2.0%_sw48_pull_cd96_mb48 | ¥205 | ¥19.7 | 52.9% | 10.4 | N | N |
| break_2.0%_sw48_pull_cd120_mb48 | ¥214 | ¥22.5 | 55.1% | 9.5 | N | N |

### Cycle 9: H9: H-M4 土日停止 ON/OFF

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 4
- Best: break_2.0%_sw48_pull_cd144_mb48 (P≈¥247)
- **Learning**: 最良 break_2.0%_sw48_pull_cd144_mb48: 執行P≈¥247, EV≈¥27.2, N≈9.1/月, W=59.5% → EV>0 だが P 不足（N=9.1）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 4 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_2.0%_sw48_pull_cd144_mb48 | ¥247 | ¥27.2 | 59.5% | 9.1 | N | N |
| break_2.0%_sw48_pull_cd144_mb48 | ¥209 | ¥19.2 | 53.4% | 10.6 | N | N |

### Cycle 10: H10: Phase1 前半まとめ — top2 再確認 + 逆 mode 対照

- テスト: 3 / Gate1: 0 / Gate2: 0 / stale: 5
- Best: break_2.0%_sw48_pull_cd144_mb48 (P≈¥247)
- **Learning**: 最良 break_2.0%_sw48_pull_cd144_mb48: 執行P≈¥247, EV≈¥27.2, N≈9.1/月, W=59.5% → EV>0 だが P 不足（N=9.1）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 5 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_2.0%_sw48_pull_cd144_mb48 | ¥247 | ¥27.2 | 59.5% | 9.1 | N | N |
| break_2.0%_sw48_pull_cd144_mb48 | ¥209 | ¥19.2 | 53.4% | 10.6 | N | N |
| bounce_2.0%_sw48_pull_cd144_mb48 | ¥80 | ¥8.6 | 47.1% | 9.2 | N | N |

### Cycle 11: H11: 全局 best 周辺 — cooldown 微調整（best P≈¥247）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 6
- Best: break_2.0%_sw48_pull_cd168_mb48 (P≈¥233)
- **Learning**: 最良 break_2.0%_sw48_pull_cd168_mb48: 執行P≈¥233, EV≈¥27.4, N≈8.5/月, W=57.8% → EV>0 だが P 不足（N=8.5）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 6 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 12: H12: 全局 best 周辺 — cooldown 微調整（best P≈¥247）

- テスト: 3 / Gate1: 0 / Gate2: 0 / stale: 7
- Best: break_2.0%_sw48_pull_cd168_mb48 (P≈¥233)
- **Learning**: 最良 break_2.0%_sw48_pull_cd168_mb48: 執行P≈¥233, EV≈¥27.4, N≈8.5/月, W=57.8% → EV>0 だが P 不足（N=8.5）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 7 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 13: H13: 全局 best 周辺 — cooldown 微調整（best P≈¥247）

- テスト: 1 / Gate1: 0 / Gate2: 0 / stale: 8
- Best: break_2.0%_sw48_pull_cd96_mb48 (P≈¥205)
- **Learning**: 最良 break_2.0%_sw48_pull_cd96_mb48: 執行P≈¥205, EV≈¥19.7, N≈10.4/月, W=52.9% → EV>0 だが P 不足（N=10.4）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 8 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 14: H14: 全局 best 周辺 — cooldown 微調整（best P≈¥247）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 9
- Best: break_2.0%_sw48_pull_cd168_mb48 (P≈¥233)
- **Learning**: 最良 break_2.0%_sw48_pull_cd168_mb48: 執行P≈¥233, EV≈¥27.4, N≈8.5/月, W=57.8% → EV>0 だが P 不足（N=8.5）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 9 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 15: H15: 全局 best 周辺 — cooldown 微調整（best P≈¥247）

- テスト: 3 / Gate1: 0 / Gate2: 0 / stale: 10
- Best: break_2.0%_sw48_pull_cd168_mb48 (P≈¥233)
- **Learning**: 最良 break_2.0%_sw48_pull_cd168_mb48: 執行P≈¥233, EV≈¥27.4, N≈8.5/月, W=57.8% → EV>0 だが P 不足（N=8.5）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 10 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_2.0%_sw48_pull_cd120_mb48 | ¥214 | ¥22.5 | 55.1% | 9.5 | N | N |
| break_2.0%_sw48_pull_cd168_mb48 | ¥233 | ¥27.4 | 57.8% | 8.5 | N | N |
| bounce_2.0%_sw48_pull_cd144_mb48 | ¥80 | ¥8.6 | 47.1% | 9.2 | N | N |

### Cycle 16: H16: 全局 best 周辺 — pct_level 微調整（best P≈¥247）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 11
- Best: break_1.8%_sw48_pull_cd144_mb48 (P≈¥200)
- **Learning**: 最良 break_1.8%_sw48_pull_cd144_mb48: 執行P≈¥200, EV≈¥17.6, N≈11.2/月, W=53.3% → EV>0 だが P 不足（N=11.2）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 11 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 17: H17: 全局 best 周辺 — pct_level 微調整（best P≈¥247）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 12
- Best: break_1.6%_sw48_pull_cd144_mb48 (P≈¥243)
- **Learning**: 最良 break_1.6%_sw48_pull_cd144_mb48: 執行P≈¥243, EV≈¥19.4, N≈12.5/月, W=53.3% → EV>0 だが P 不足（N=12.5）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 12 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 18: H18: 全局 best 周辺 — pct_level 微調整（best P≈¥247）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 13
- Best: break_1.6%_sw48_pull_cd144_mb48 (P≈¥243)
- **Learning**: 最良 break_1.6%_sw48_pull_cd144_mb48: 執行P≈¥243, EV≈¥19.4, N≈12.5/月, W=53.3% → EV>0 だが P 不足（N=12.5）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 13 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 19: H19: 全局 best 周辺 — pct_level 微調整（best P≈¥247）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 14
- Best: break_1.8%_sw48_pull_cd144_mb48 (P≈¥200)
- **Learning**: 最良 break_1.8%_sw48_pull_cd144_mb48: 執行P≈¥200, EV≈¥17.6, N≈11.2/月, W=53.3% → EV>0 だが P 不足（N=11.2）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 14 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 20: H20: 全局 best 周辺 — pct_level 微調整（best P≈¥247）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 15
- Best: break_1.8%_sw48_pull_cd144_mb48 (P≈¥200)
- **Learning**: 最良 break_1.8%_sw48_pull_cd144_mb48: 執行P≈¥200, EV≈¥17.6, N≈11.2/月, W=53.3% → EV>0 だが P 不足（N=11.2）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 15 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_1.8%_sw48_pull_cd144_mb48 | ¥200 | ¥17.6 | 53.3% | 11.2 | N | N |
| break_2.2%_sw48_pull_cd144_mb48 | ¥144 | ¥18.1 | 50.8% | 7.3 | N | N |

### Cycle 21: H21: 全局 best 周辺 — swing_bars 微調整（best P≈¥247）

- テスト: 3 / Gate1: 0 / Gate2: 0 / stale: 16
- Best: break_2.0%_sw60_pull_cd144_mb48 (P≈¥226)
- **Learning**: 最良 break_2.0%_sw60_pull_cd144_mb48: 執行P≈¥226, EV≈¥23.0, N≈9.8/月, W=56.0% → EV>0 だが P 不足（N=9.8）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 16 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 22: H22: 全局 best 周辺 — swing_bars 微調整（best P≈¥247）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 0
- Best: break_2.0%_sw72_pull_cd144_mb48 (P≈¥311)
- **Learning**: 最良 break_2.0%_sw72_pull_cd144_mb48: 執行P≈¥311, EV≈¥30.3, N≈10.3/月, W=61.5% → EV>0 だが P 不足（N=10.3）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 23: H23: 全局 best 周辺 — swing_bars 微調整（best P≈¥311）

- テスト: 1 / Gate1: 0 / Gate2: 0 / stale: 1
- Best: break_2.0%_sw96_pull_cd144_mb48 (P≈¥274)
- **Learning**: 最良 break_2.0%_sw96_pull_cd144_mb48: 執行P≈¥274, EV≈¥24.2, N≈11.3/月, W=56.3% → EV>0 だが P 不足（N=11.3）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 24: H24: 全局 best 周辺 — swing_bars 微調整（best P≈¥311）

- テスト: 3 / Gate1: 0 / Gate2: 0 / stale: 2
- Best: break_2.0%_sw84_pull_cd144_mb48 (P≈¥274)
- **Learning**: 最良 break_2.0%_sw84_pull_cd144_mb48: 執行P≈¥274, EV≈¥25.0, N≈11.0/月, W=56.6% → EV>0 だが P 不足（N=11.0）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 25: H25: 全局 best 周辺 — swing_bars 微調整（best P≈¥311）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 3
- Best: break_2.0%_sw84_pull_cd144_mb48 (P≈¥274)
- **Learning**: 最良 break_2.0%_sw84_pull_cd144_mb48: 執行P≈¥274, EV≈¥25.0, N≈11.0/月, W=56.6% → EV>0 だが P 不足（N=11.0）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 3 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_2.0%_sw60_pull_cd144_mb48 | ¥226 | ¥23.0 | 56.0% | 9.8 | N | N |
| break_2.0%_sw84_pull_cd144_mb48 | ¥274 | ¥25.0 | 56.6% | 11.0 | N | N |

### Cycle 26: H26: 全局 top3 最終 validation（iter 26–30 収束）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 4
- Best: break_2.0%_sw84_pull_cd144_mb48 (P≈¥274)
- **Learning**: 最良 break_2.0%_sw84_pull_cd144_mb48: 執行P≈¥274, EV≈¥25.0, N≈11.0/月, W=56.6% → EV>0 だが P 不足（N=11.0）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 4 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 27: H27: 全局 top3 最終 validation（iter 26–30 収束）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 5
- Best: break_2.0%_sw84_pull_cd144_mb48 (P≈¥274)
- **Learning**: 最良 break_2.0%_sw84_pull_cd144_mb48: 執行P≈¥274, EV≈¥25.0, N≈11.0/月, W=56.6% → EV>0 だが P 不足（N=11.0）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 5 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 28: H28: 全局 top3 最終 validation（iter 26–30 収束）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 6
- Best: break_2.0%_sw84_pull_cd144_mb48 (P≈¥274)
- **Learning**: 最良 break_2.0%_sw84_pull_cd144_mb48: 執行P≈¥274, EV≈¥25.0, N≈11.0/月, W=56.6% → EV>0 だが P 不足（N=11.0）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 6 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 29: H29: 全局 top3 最終 validation（iter 26–30 収束）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 7
- Best: break_2.0%_sw84_pull_cd144_mb48 (P≈¥274)
- **Learning**: 最良 break_2.0%_sw84_pull_cd144_mb48: 執行P≈¥274, EV≈¥25.0, N≈11.0/月, W=56.6% → EV>0 だが P 不足（N=11.0）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 7 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

### Cycle 30: H30: 全局 top3 最終 validation（iter 26–30 収束）

- テスト: 2 / Gate1: 0 / Gate2: 0 / stale: 8
- Best: break_2.0%_sw84_pull_cd144_mb48 (P≈¥274)
- **Learning**: 最良 break_2.0%_sw84_pull_cd144_mb48: 執行P≈¥274, EV≈¥25.0, N≈11.0/月, W=56.6% → EV>0 だが P 不足（N=11.0）。cooldown/N 調整。 → N<40。cooldown 短縮 or pct 浅く。 → 8 iter 無改善 — pivot（mode/pct 変更）。
- **次仮説**: cooldown↓ or pct_level 浅く（イベント増）

| Config | 執行P | EV | W | N/mo | G1 | G2 |
|---|---:|---:|---:|---:|:---:|:---:|
| break_2.0%_sw84_pull_cd144_mb48 | ¥274 | ¥25.0 | 56.6% | 11.0 | N | N |
| break_2.0%_sw60_pull_cd144_mb48 | ¥226 | ¥23.0 | 56.0% | 9.8 | N | N |

## 30 サイクル総括

- Gate2 pass サイクル: **0** / 30
- Gate1 pass サイクル: **0** / 30
- 最終 stale（無改善）: 8

### パラメータ応答（観察）

- **mode**: break（貫通）vs bounce（反発）— Phase0 weak 再現、執行込みで split 不安定
- **pct_level**: 浅いほど N↑、深いほど edge 方向性が break に寄る
- **cooldown / auto-N**: N 帯調整可能だが EV とトレードオフ
- **entry pull**: H-D 教訓通り immediate より pull が優位な場合あり
- **Exit fixed pct**: ATR RR より執行劣化が小さい傾向

### 最終判定

- **weak-positive** — EV>0 だが N=10.3/月、Gate2 遠隔。 単体 L1 不採用、フィルタ用途のみ。

## 次アクション

1. H-D4 単体 promote 不可 → edge-catalog closed 候補
2. EV>0 設定があれば H-D canonical との合成（非 tuning）のみ検討
3. 次 L1: H-D5（ピンバー）or 別メカニズム

データ: `data/research/hd4_loop/hd4_loop_summary.json`


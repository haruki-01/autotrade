# ナレッジログ

検証バッチごとの学びを蓄積する正本。  
**pass / fail 問わず** Knowledge Card を1件残す。`learnings` または `next_actions` が空のカードは **未完了** とみなす。

記入テンプレとバッチ別の事前 `if_pass` / `if_fail` は本ファイル下部を参照。  
運用手順は [verification-workflow.md](verification-workflow.md)。

---

## Knowledge Card テンプレ

新規カードは以下をコピーし、`## KB-{batch_id}-{YYYYMMDD}` 見出しで追記する。

```markdown
## KB-B03-20260903

| 項目 | 内容 |
|---|---|
| batch_id | B03 |
| date | 2026-09-03 |
| purpose | （バッチの purpose をそのまま） |
| decision_question | （バッチで答える1文の問い） |
| hypotheses | H-B（主）, 遅入対照 |
| metrics | P0-HB-EARLY, P0-HB-LATE, P0-HB-FREQ, … |
| sample_period | 2024-01-01〜2025-12-31 |
| operator | （任意） |

### result_summary

- （数値の要約のみ。解釈は learnings へ）

### batch_verdict

`promote` | `conditional` | `reject` | `defer` | `spawn`

### learnings

- （観測された事実。例: 「EARLY mean_edge=+0.8%, LATE=+0.1%」）
- （条件付き weak なら条件: 「EUROPE_US 帯のみ pass」）

### next_actions

- （必須。例: Phase1 候補に H-B 追加 / B03-R で SESSION 分割 / H-A2 へ pivot）

### spawned_hypotheses

- （なし、または `H-B2` parent=P0-HB2-DIR など）

### catalog_updates

- H-B: status → Phase1候補
- H-A: status → 棄却（理由: …）
```

---

## 必須項目チェックリスト

バッチ完了前に確認:

- [ ] `purpose` が verification-workflow §4 と一致
- [ ] `decision_question` が実行 **前** に書かれていた（シート or 本カード）
- [ ] 対象 metric の `verdict` がシートに記入済み
- [ ] `batch_verdict` が §5.2 の定義に沿っている
- [ ] `learnings` に事実が1行以上
- [ ] `next_actions` が1行以上（promote でも「Phase1 仕様ドラフト作成」等）
- [ ] `edge-catalog.md` の status を更新した（または spawn 追記）

---

## バッチ別：事前 if_pass / if_fail

計測 **前** に参照し、Knowledge Card の `next_actions` 草案として使う。

### B01 — 時間構造

| | 内容 |
|---|---|
| decision_question | 時間帯・6:00・土日で statistically 説明力のある歪みはあるか？ |
| if_pass | 有意な帯を H-M4 / H-E ルールとして葉に固定。後続バッチの分割条件に使う |
| if_fail | 時間フィルタは採用しない。H-C / H-E 系を棄却または defer |

### B02 — スパイク分岐

| | 内容 |
|---|---|
| decision_question | SPIKE 後、回帰（H-A）と継続（H-A2）のどちらが edge_return 優位か？ |
| if_pass | 優位側のみ Phase1 候補。劣位側は reject。PATH で執行タイミングを葉化 |
| if_fail | 両方 fail → スパイク系は Phase1 載せない。B07 稀イベントのみ defer |

### B03 — 早期性

| | 内容 |
|---|---|
| decision_question | IGNITE の EARLY は LATE を有意に上回るか？頻度は N≈50 可能か？ |
| if_pass | H-B を promote。H-M5（遅入禁止）を Phase1 必須ルールに |
| if_fail | H-B reject or conditional（サブサンプルのみなら B03-R） |

### B04 — 点火亜型

| | 内容 |
|---|---|
| decision_question | B2/B3 は H-B 独立候補か、B に統合フィルタか？ |
| if_pass | 独立 promote or B03 ロジックに合成 |
| if_fail | カタログで H-B2/H-B3 を棄却。B03 のみ Phase1 |

### B05 — レジーム内押し

| | 内容 |
|---|---|
| decision_question | 押し待ち（RESUME）は CTRL より優位か？ |
| if_pass | H-F1 を Phase1 候補（トレンド内押しロジック） |
| if_fail | H-F1 棄却。F2/F3 は B05 拡張で defer |

### B06 — 群集

| | 内容 |
|---|---|
| decision_question | 群集シグナルは PULL/ALIGN が RAW より優位か？ |
| if_pass | 「即入り禁止・初押し・12h 整合」を Phase1 執行の葉に固定 |
| if_fail | H-D 系を棄却 or 単独フィルタのみ（エントリー本体にしない） |

### B07 — 稀イベント

| | 内容 |
|---|---|
| decision_question | 稀イベントは n≥30 で edge が +2% 帯に届くか？ |
| if_pass | 該当 ID のみ Phase1（低頻度・高 RR 想定） |
| if_fail | defer（期間延長）or 棄却 |

---

## 記録済みカード

### KB-B01-20260903

| 項目 | 内容 |
|---|---|
| batch_id | B01 |
| date | 2026-09-03 |
| purpose | 時間構造の歪みを低コストで確認し、フィルタ採用可否を決める |
| decision_question | 時間帯・6:00・土日で statistically 説明力のある歪みはあるか？ |
| hypotheses | H-E, H-C, H-C4 |
| metrics | P0-HE-* (5), P0-HC4-* (2), P0-HC-* (4) |
| sample_period | 2024-01-01..2026-08-31 |
| data_source | GMO Coin public API BTC_JPY 5min (276,718 bars) |

**result_summary**

- batch_verdict: **conditional**
- H-E: FEE_WINDOW 日次リターンはランダム1h窓より +0.035%/日 優位（P0-HE-VS pass）だが、方向バイアス・ボラ差は弱い/ fail
- H-C4: 平日 fwd h60 が土日よりわずかに大きい（pass）。土日 SPIKE 継続失敗率 58%（pass）→ 土日は偽ブレイク多め
- H-C: セッション間 fwd 差は小さい（weak）。EUROPE_US の run length は TOKYO より短い（weak）。TOKYO の spike 回帰 edge は弱い

**batch_verdict:** conditional

**learnings**

- 6:00 前後（FEE_WINDOW）に統計的に detectable なリターン差はあるが、hit_rate≈51% でトレード単体エッジとしては弱い
- 土日はブレイク継続が失敗しやすく、**土日新規停止フィルタ（H-M4）** の採用候補
- セッション別の追随/回帰の差は小さく、単独では Phase1 エントリー本体にしない
- 平日 vs 土日の差は方向としては平日有利だが effect size は極小

**next_actions**

- H-M4（土日ゲート）を後続バッチ B02–B07 の分割条件として記録
- H-E は Phase1 単体候補にしない（6:00 前後イベント専用は defer）
- **B02（スパイク分岐）** へ進行。SESSION 分割は P0-HA-BY-SESS で再確認

**spawned_hypotheses**

- なし

**catalog_updates**

- H-C4 / H-M4: 探索中 → **条件付き採用（土日フィルタ）**
- H-E: 探索中 → weak（単体 Phase1 見送り）
- H-C: 探索中 → weak（フィルタ補助のみ）

---

### KB-B02-20260903

| 項目 | 内容 |
|---|---|
| batch_id | B02 |
| date | 2026-09-03 |
| purpose | スパイク後に「回帰」と「継続」どちらが優位か分岐する |
| decision_question | SPIKE 後、回帰（H-A）と継続（H-A2）のどちらが edge_return 優位か？ |
| hypotheses | H-A（回帰）, H-A2（継続） |
| metrics | P0-HA-REVERT, CONT, REVERT15, PATH, BY-SESS |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **promote**（H-A2 側）
- P0-HA-REVERT: mean=-0.012%, hit=54.2%, n=4692 → fail
- P0-HA-CONT: mean=+0.012%, hit=45.8%, n=4692 → pass（対照優位）
- P0-HA-REVERT15: mean≈0, hit=55.1% → fail（h15 回帰 edge なし）
- P0-HA-PATH: revert_first=3807 / cont_first=884（81% が 0.3×ATR 逆行先到達）→ pass
- P0-HA-BY-SESS: WD-only REVERT mean=-0.019%、全 SESSION で回帰 edge 弱い

**batch_verdict:** promote

**learnings**

- SPIKE 後 h60 方向 edge は **継続（H-A2）が回帰（H-A）に明確に勝つ**（diff=+0.024%）
- PATH 分析では短期の逆行先到達率が高いが、h60 リターンでは継続方向が優位 → 執行タイミングと保有 horizon の乖離あり
- セッション分割・平日フィルタ（H-M4）でも回帰 edge は改善せず

**next_actions**

- **H-A2 を Phase1 候補**に昇格。H-A は reject
- Phase1 仕様で PATH（0.3×ATR 逆行）を SL 参考、h60 継続を TP 方向の初期案として検討
- B03（IGNITE 早期性）へ進行

**spawned_hypotheses**

- なし

**catalog_updates**

- H-A2: 探索中 → **Phase1 候補**
- H-A: 探索中 → **棄却**（CONT に負け）

---

### KB-B03-20260903

| 項目 | 内容 |
|---|---|
| batch_id | B03 |
| date | 2026-09-03 |
| purpose | 点火エッジが「早期性」に依存するか検証する |
| decision_question | IGNITE の EARLY は LATE を有意に上回るか？頻度は N≈50 可能か？ |
| hypotheses | H-B（早期点火） |
| metrics | P0-HB-EARLY, LATE, PULL, FREQ, BODY, HB5-SPLIT |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **conditional**
- P0-HB-EARLY: mean≈0, hit=47.9%, n=13685, vs LATE=+0.037% → pass（対照優位だが絶対 edge 極小）
- P0-HB-LATE: mean=-0.037%, n=3679 → fail
- P0-HB-PULL: mean=-0.021%, n=10087 → fail
- P0-HB-FREQ: 428 件/月 → weak（N≈50 帯を大幅超過、定義緩い可能性）
- P0-HB-BODY / HB5-SPLIT: 実体条件差なし → weak/fail

**batch_verdict:** conditional

**learnings**

- EARLY は LATE より統計的に優位だが、**絶対 mean_edge≈0** で Phase0 単体 promote には届かない
- IGNITE 頻度が月 428 件と過多 → 定義の厳格化 or フィルタ合成が Phase1 前提
- 押し戻し（PULL）後も edge なし

**next_actions**

- H-B は **conditional（H-M5 遅入禁止を Phase1 必須ルール候補）** として記録
- Phase1 前に IGNITE 定義の厳格化 + H-M4 土日ゲート併用で FREQ を N 帯に再計測（B03-R）
- B04 へ進行（B03 reject ではないため亜型の独立判定を実施）

**spawned_hypotheses**

- なし

**catalog_updates**

- H-B: 探索中 → **conditional**（早期性あり、絶対 edge 弱い）

---

### KB-B04-20260903

| 項目 | 内容 |
|---|---|
| batch_id | B04 |
| date | 2026-09-03 |
| purpose | 点火の亜型（圧縮解放・スイング連鎖）を独立候補にするか判断 |
| decision_question | B2/B3 は H-B 独立候補か、B に統合フィルタか？ |
| hypotheses | H-B2（SQUEEZE_RELEASE）, H-B3（SWING_CHAIN） |
| metrics | P0-HB2-DIR, FAKE, FREQ, P0-HB3-CONT, 3RD |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **reject**
- P0-HB2-DIR: mean=+0.023%, n=910 → weak
- P0-HB2-FAKE: fake_rate=20.4% → pass（参考）
- P0-HB2-FREQ: 28.5/月 → weak
- P0-HB3-CONT: mean=-0.084%, n=7595 → fail
- P0-HB3-3RD: 3rd reach=45.6% → weak

**batch_verdict:** reject

**learnings**

- SQUEEZE 解放・SWING 連鎖とも **独立 Phase1 候補としての edge 不足**
- B03 conditional のため参考記録だが、亜型独立 promote 条件を満たさない

**next_actions**

- H-B2 / H-B3 を **棄却**。H-B（B03）のみ conditional 継続
- B05 へ進行

**spawned_hypotheses**

- なし

**catalog_updates**

- H-B2: 探索中 → **棄却**
- H-B3: 探索中 → **棄却**

---

### KB-B05-20260903

| 項目 | 内容 |
|---|---|
| batch_id | B05 |
| date | 2026-09-03 |
| purpose | 上位トレンド内の行き過ぎ押しが再開エッジを持つか |
| decision_question | 押し待ち（RESUME）は CTRL より優位か？ |
| hypotheses | H-F1（TREND_EXCESS_PULL） |
| metrics | P0-HF1-RESUME, CTRL, FREQ |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **reject**
- P0-HF1-RESUME: mean=+2.14%, n=7 → insufficient_n（vs CTRL=+1.56%）
- P0-HF1-CTRL: mean=+0.58%, hit=66.5%, n=427 → pass
- P0-HF1-FREQ: 0.2/月 → weak（イベント極稀）

**batch_verdict:** reject

**learnings**

- 厳格な TREND_EXCESS_PULL 定義では RESUME イベントが月 0.2 件と **Phase0 検出力不足**
- CTRL（押し待ちなし）の方が頻度・hit_rate で優位 → 「押し待ち」仮説は棄却方向
- 初期実装の緩い定義（n=106k）は過検出。修正後は妥当な頻度に収束

**next_actions**

- H-F1 を **棄却**。H-F2/F3 は拡張バッチで defer
- B06 へ進行

**spawned_hypotheses**

- なし

**catalog_updates**

- H-F1: 探索中 → **棄却**（insufficient_n + CTRL 優位）

---

### KB-B06-20260903

| 項目 | 内容 |
|---|---|
| batch_id | B06 |
| date | 2026-09-03 |
| purpose | 群集シグナルは「即入り」より「押し待ち・上位整合」か |
| decision_question | 群集シグナルは PULL/ALIGN が RAW より優位か？ |
| hypotheses | H-D, H-D2, H-D3, H-D4, H-D5 |
| metrics | P0-HD-* (13行) |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **conditional**
- P0-HD-RAW: mean=+0.009%, n=8126 → weak
- P0-HD-PULL: mean=+0.24%, hit=64.3%, n=8125 → **pass**（PULL>RAW）
- P0-HD-ALIGN: mean=+0.021%, n=4330 → weak
- P0-HD2-MAG/REJECT/THROUGH: ラウンド数反発 → weak/fail
- P0-HD3-IMMEDIATE/DELAY: 差なし → fail
- P0-HD4-BOUNCE/BREAK: PCT_LEVEL → weak
- P0-HD5-FADE/CONT: 12h ピンバー → fail/weak

**batch_verdict:** conditional

**learnings**

- RSI 出口＋**初押し待ち（PULL）** が RAW 即入りより mean_edge +0.23% 改善
- 12h トレンド整合（ALIGN）単体では edge 増幅せず
- EMA クロス IMMEDIATE vs DELAY、ピンバー fade に edge なし

**next_actions**

- H-D を **conditional Phase1 候補**（執行: RSI シグナル → 初押し待ち必須）
- Phase1 仕様に「即入り禁止・初押し」を葉ルールとして固定
- B07 へ進行

**spawned_hypotheses**

- なし

**catalog_updates**

- H-D: 探索中 → **conditional**（PULL 執行ルール付き Phase1 候補）

---

### KB-B07-20260903

| 項目 | 内容 |
|---|---|
| batch_id | B07 |
| date | 2026-09-03 |
| purpose | 稀イベントに Phase1 載せる価値があるか |
| decision_question | 稀イベントは n≥30 で edge が detectable か？ |
| hypotheses | H-A3, H-A4, H-C2, H-B4 |
| metrics | P0-HA3-*, P0-HA4-*, P0-HC2-*, P0-HB4-* |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **conditional**（defer 要素あり）
- P0-HA3-REVERT2: mean=-0.012%, n=835 → fail
- P0-HA3-RATE: 45/月 → weak
- P0-HA4-CONT: mean=+0.026%, n=3217 → weak
- P0-HC2-GAP: mean=+0.16%, n=40015 → weak（参考）
- P0-HC2-CONT/REVERT: 週明け方向 edge 極小 → weak/fail
- P0-HB4-POST/CTRL: 12h クローズ先行 edge なし → weak

**batch_verdict:** conditional

**learnings**

- DOUBLE_SPIKE 2回目回帰、FAILED_EDGE 継続とも **Phase1 単体候補には届かない**
- 週明け gap は detectable だが方向 edge は弱い
- 稀イベントは n は確保できるが mean_edge が +2% 帯に遠い

**next_actions**

- H-A3 / H-A4 / H-B4 → **棄却 or defer**
- H-C2 → **参考記録**（Phase1 単体載せない）
- **Phase0 総括**（phase0-summary.md）を作成し Phase1 仕様ドラフトへ

**spawned_hypotheses**

- なし

**catalog_updates**

- H-A3, H-A4, H-B4: 探索中 → **棄却**
- H-C2: 探索中 → **weak（参考）**

---

### KB-P1-A-20260903

| 項目 | 内容 |
|---|---|
| batch_id | P1-A |
| date | 2026-09-03 |
| purpose | H-D（RSI + 初押し待ち）の取引可能エッジ検証 |
| decision_question | RSI+PULL は RR 1:2・執行込みで Gate1 pass か？ |
| hypotheses | H-D（主）, RAW 対照 |
| metrics | P1-HD-PULL（IS/OOS1/OOS2）, P1-HD-PULL_M4 |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **conditional**
- 平日フィルタ（H-M4）あり: 執行込み EV=+¥21.3, W=57.6%, N=47.6/月 → **Gate1 pass**
- フィルタなし: N=63–78/月で Gate1 fail（N 帯超過）。EV は正だが頻度過多
- RAW 即入り対照: EV=−¥4.9 → PULL 優位を再確認
- ランダム W≈46.5% vs 戦略 W≈57.7%
- **Gate2 fail**（月次 P≈¥1,013 << 旧 ¥10,000 / 新 ¥2,500 目標）→ [KB-P1-REBASELINE](#kb-p1-rebaseline-20260903) で再評価

**batch_verdict:** conditional

**learnings**

- Phase0 の PULL 優位は RR 1:2 バックテストでも再現（執行込み EV 正）
- **H-M4 土日停止が N 帯調整に必須**（47.6/月 ≈ 目標 50）
- Gate2（月次 +5% = ¥2,500）にも未到達（再採点後も fail）。EV 絶対値が小さい

**next_actions**

- H-D + H-M4 を Phase1 候補として **conditional 継続**
- Gate2 到達には SL/TP 幅・保有時間の感度分析（Phase1-R）
- P1-B へ進行

**catalog_updates**

- H-D: Phase0 conditional → **Phase1 conditional（H-M4 必須）**

---

### KB-P1-B-20260903

| 項目 | 内容 |
|---|---|
| batch_id | P1-B |
| date | 2026-09-03 |
| purpose | H-A2 SPIKE 継続の取引可能エッジ検証 |
| decision_question | SPIKE 継続は執行込みでも Phase0 promote が再現するか？ |
| hypotheses | H-A2（主）, H-A 回帰対照 |
| metrics | P1-HA2-CONT（IS/OOS1/OOS2） |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **reject**
- 執行込み EV=−¥6.0（IS）、W≈21%、N 帯も超過
- 回帰対照も EV 負 → Phase0 の微小 edge は RR 1:2 では再現せず
- ランダム W≈44% > 戦略 W≈21%

**batch_verdict:** reject

**learnings**

- Phase0 promote（mean_edge +0.012%）は **Phase1 執行込みでは棄却**
- ATR ベース SL/TP（0.3/0.6）では継続方向が機能しない
- N 過多（65–78/月）も Gate1 阻害要因

**next_actions**

- H-A2 を **Phase1 棄却**
- P1-C は H-D のみで合成（H-A2 除外）

**catalog_updates**

- H-A2: Phase0 promote → **Phase1 reject**

---

### KB-P1-C-20260903

| 項目 | 内容 |
|---|---|
| batch_id | P1-C |
| date | 2026-09-03 |
| purpose | Gate1 pass 候補 + H-M4 の合成ロジック |
| decision_question | 合成で Gate1/2 を満たすか？ |
| hypotheses | H-D + H-M4（H-A2 は Gate1 fail のため除外） |
| metrics | P1-COMPOSITE（IS/OOS1/OOS2） |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **conditional**
- OOS2: 執行込み EV=+¥17.5, N=50.4/月, W=57.4% → **Gate1 pass**
- IS/OOS1 も Gate1 pass
- Gate2 fail（月次 P≈¥740–1,211；新基準 ¥2,500 でも未達）

**batch_verdict:** conditional

**learnings**

- H-D + H-M4 合成は OOS で Gate1 を安定 pass
- H-A2 除外でも N 帯・EV 符号は維持
- 月次 +5%（¥2,500）目標にも RR/幅の再設計だけでは不足 → [KB-P1-REBASELINE](#kb-p1-rebaseline-20260903)

**next_actions**

- **Phase1-R**: SL/TP 幅グリッド + Gate2 到達可否を探索
- 採用確定前に実装フェーズへは進まない
- H-B（遅入禁止）フィルタは B03-R 後に合成候補

**catalog_updates**

- composite: Phase1 conditional（H-D + H-M4）

---

### KB-P1-R-20260903

| 項目 | 内容 |
|---|---|
| batch_id | P1-R |
| date | 2026-09-03 |
| purpose | H-D + H-M4 の SL/TP 幅グリッドで Gate2 到達可否 |
| decision_question | R 幅変更で執行込み月次 P≥¥10,000（旧 Gate2）に届くか？ → 新 Gate2 ¥2,500 は [KB-P1-REBASELINE](#kb-p1-rebaseline-20260903) |
| hypotheses | H-D + H-M4 |
| metrics | P1R-BASELINE, P1R-BEST, 72 組グリッド |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **conditional**（Gate1 のみ。Gate2 は全組み合わせ fail）
- グリッド: 72 組（理論値スクリーン）→ 上位 15 組を執行込み再検証
- **gate2_any_count = 0**（Gate2 到達組み合わせなし）
- **P1R-BASELINE**（pct=0.8%, atr×0.5, 48bar）: OOS Gate1 pass、月次 P≈¥712（OOS 平均）
- **P1R-BEST**（pct=0.8%, atr×1.5, 96bar）: OOS Gate1 pass、月次 P≈¥678（baseline より劣る）
- 理論値スクリーン最高でも月次 P≈¥1,600 程度（Gate2 遠隔）

**batch_verdict:** conditional

**learnings**

- SL/TP 幅を広げても **Gate2（月次 +¥10,000）は到達不能**
- R 拡大は W 低下とトレードオフし、OOS 平均 P は baseline 超えず
- **H-M4 + 初押し待ち** は Gate1（取引可能エッジ）としては維持
- 目標 EV ¥200/回には、現 Q=¥10,000・RR 1:2・H-D 単体では不足

**next_actions**

- H-D 単体での Gate2 追求は **停止**（Phase1-R 結論）
- 選択肢: (1) 目標 P の再ベースライン検討 (2) 別仮説探索 (3) H-D をフィルタとして別エントリーと合成
- 実装フェーズには **Gate2 pass 候補なし** のため進まない

**catalog_updates**

- H-D: Phase1 conditional 維持（Gate1 のみ）。Gate2 未達を明記（新基準 ¥2,500 でも fail）

---

### KB-P1-REBASELINE-20260903

| 項目 | 内容 |
|---|---|
| batch_id | P1-REBASELINE |
| date | 2026-09-03 |
| purpose | L0 目標を月次 +20%（¥10,000）→ **+5%（¥2,500）** へ再ベースライン |
| decision_question | 既存 Phase1 結果を新 Gate2 で再採点すると pass するか？ |
| hypotheses | H-D + H-M4（P1-A/C/R 既存結果） |
| metrics | P1-A M4, P1-C composite, P1-R baseline/best（gate 再採点のみ） |
| sample_period | 2024-01-01..2026-08-31（バックテスト再実行なし） |

**L0 変更（SPEC §2.3）**

| 項目 | 旧 | 新 |
|---|---|---|
| Gate2 月次目標 | +20%（¥10,000） | **+5%（¥2,500）** |
| 必要 EV（N≈50） | ¥200/回（+2.0%） | **¥50/回（+0.5%）** |
| サイジング | 固定表記 | **margin = B/10、Q = B/5**（複利） |
| Stretch | — | +20%（Gate 対象外） |

**result_summary**

- **gate2_any_count = 0**（全 Phase1 結果で新 Gate2 も fail）
- P1-A H-M4（ALL）: 月次 P≈¥1,013（新目標の **41%**）
- P1-C composite OOS 平均: 月次 P≈¥812（**32%**）
- P1-R baseline OOS 平均: 月次 P≈¥812（**32%**）
- Gate1（EV>0、N 40–60/月）は **維持**

**batch_verdict:** conditional（Gate1 のみ。Gate2 は新基準でも全 fail）

**learnings**

- 目標を 1/4 に下げても、OOS P は新目標の **約 1/3** にとどまる
- H-D 単体 + RR 1:2 + H-M4 では **Gate2 到達不可**（SL/TP グリッドでも同様）
- 初期 BR ¥50,000 では固定 Q=¥10,000 = B/5 のため、再採点は gate フラグのみで完結

**next_actions**（PM 判断待ち）

- (A) Gate1 候補（H-D + H-M4）で paper trade を開始するか → **実施済み [KB-PT-A](#kb-pt-a-20260903)**
- (B) 新 L1 仮説探索へ移行するか
- (C) P1-R2（N 削減・シグナル厳格化で EV/trade 向上）を試すか
- 実装フェーズには **Gate2 pass 候補なし** のため、明示的 PM 決定なしでは進まない

**catalog_updates**

- SPEC §2.3 Gate2 = +5%
- edge-catalog / phase1-spec / common.py 定数を同期

---

### KB-PT-A-20260903

| 項目 | 内容 |
|---|---|
| batch_id | PT-A |
| date | 2026-09-03 |
| purpose | H-D + H-M4 のフォワード sim paper trade（複利 BR） |
| decision_question | Phase1 Gate1 が forward 逐次処理で再現するか？ |
| hypotheses | H-D + H-M4（P1-C 同一） |
| metrics | PT-A-FORWARD（OOS1+OOS2） |
| sample_period | 2025-07-01..2026-08-31 |

**result_summary**

- batch_verdict: **conditional**
- PT-Gate1 **pass**: EV=+¥14.1, N=49/月, W=55.4%
- PT-Gate2 **fail**: 月次 P≈¥692（目標 ¥2,500 の 28%）
- 複利 BR: ¥50,000 → ¥59,692（+19.4% / 14ヶ月）
- Phase1 参照劣化率: 0.86（≥0.7 pass）

**learnings**

- Paper trade sim でも Gate1（取引可能エッジ）は **再現**
- Gate2 未到達は Phase1 backtest と一致
- 複利運用でも月次 +5% には届かない

**next_actions**

- N 感度検証（P1-N）へ → [KB-P1-N](#kb-p1-n-20260903)

---

### KB-P1-N-20260903

| 項目 | 内容 |
|---|---|
| batch_id | P1-N |
| date | 2026-09-03 |
| purpose | N=10/20/50/100 の感度検証 + 必要 EV/W* 整理 |
| decision_question | 各 N 帯で Gate1/2 に届くか？ |
| hypotheses | H-D + H-M4（cooldown 調整） |
| metrics | P1N-N10/20/50/100 |
| sample_period | OOS1+OOS2 |

**必要エッジ（Gate2 = ¥2,500/月）**

| N | EV* | W*（Gate2） | 実測 W | 実測 P | Gate1 | Gate2 |
|---:|---:|---:|---:|---:|:---:|:---:|
| 10 | ¥250 | 139%（不可） | 55.0% | ¥136 | pass | fail |
| 20 | ¥125 | 87.1% | 58.6% | ¥314 | pass | fail |
| 50 | ¥50 | 55.8% | 55.3% | ¥709 | pass | fail |
| 100 | ¥25 | 45.4% | 57.3% | ¥1,121 | fail | fail |

**batch_verdict:** conditional（N=10/20/50 で Gate1 pass、全 N で Gate2 fail）

**learnings**

- **N=10 は RR 1:2 では Gate2 構造的に不可**（1回最大 EV ≈ ¥156 @ W=100%）
- N を下げても EV/trade は ¥13–18 程度で、Gate2 必要 EV に遠い
- N=100 は cooldown 最小でも N 帯 80–120 に届かず（max ≈62/月）
- 損益分岐 W=35% は全 N でクリア。Gate2 には **W* または EV/trade の大幅改善**が必要

**next_actions**

- Gate2 到達には RR 1:2 以外（幅拡大・別 L1）を検討
- 現 Gate1 候補を live paper（GMO API）へ進めるか PM 判断

**catalog_updates**

- H-D: PT-A conditional 確認。N 感度結果を edge-catalog に反映

---

### KB-P1-NR-20260904

| 項目 | 内容 |
|---|---|
| batch_id | P1-NR（10 iter loop） |
| date | 2026-09-04 |
| purpose | N=20/50 × RR=1:3/1:5 + R 幅探索（10 サイクル verify→update→verify） |
| decision_question | 3変数（N, RR, R）で執行込み Gate2 に届くか？ |
| hypotheses | H-D + H-M4 |
| metrics | 全局 best: N50, RR1:3, pct_risk=0.006, cd=12 |
| sample_period | OOS1+OOS2 |

**10 イテレーション要約**

| Iter | 仮説 | Best 執行P |
|---:|---|---:|
| 1 | N×RR core grid | ¥726 |
| 2 | cooldown + RR1:4 | ¥867 |
| 3 | R 拡大 | ¥983 |
| 4 | R 縮小 | ¥1,119 |
| 5–10 | ATR/max_bars/N 汎化/再確認 | ¥1,127 |

**batch_verdict:** conditional（Gate2 fail、W≥W* 達成、EV 不足がボトルネック）

**learnings**

- RR 1:3 > RR 1:5（執行込み OOS P）。TP 遠いほど劣化率悪化
- R 縮小（0.6%）が R 拡大より執行込み P 改善 — P1-R 教訓と整合
- 理論 P≈¥1,644 vs 執行 P≈¥1,127（劣化率 0.90）
- Gate2 最良でも目標の 45%。**H-D 単体では L3 限界**

**next_actions**

- H-D をエントリーフィルタとし別 L1（H-B 等）と合成
- 新 L1 仮説探索へ移行（Gate2 到達の主戦場）

**catalog_updates**

- H-D: Phase1/PT conditional 確定。Gate2 未到達を P1-NR で蓋然性高く確認

---

### KB-L1-A-20260904

| 項目 | 内容 |
|---|---|
| batch_id | P2-A |
| date | 2026-09-04 |
| purpose | H-B EARLY + H-M4 + H-M5 の Phase1 同等検証 |
| decision_question | 点火3本目 + 遅入禁止で Gate1/2 pass か？ |
| hypotheses | H-B EARLY（主）, RR 1:3 感度 |
| metrics | P2-HB-EARLY（IS/OOS1/OOS2）, RR3, M4 |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **conditional**（OOS2 Gate1 pass のみ）
- OOS2: 執行 EV=+¥3.7, W=46.6%, N=48.6/月, P≈¥181 → Gate1 pass / Gate2 fail
- IS/OOS1: 執行 EV 負（P≈−¥123〜−¥135）
- ALL: 執行 EV 負、劣化率 −0.98
- 初回 run は pullback フィルタ bug（wick ベース）で n=0 → close ベース修正後再実行

**batch_verdict:** conditional（OOS 安定性なし）

**learnings**

- Phase0 EARLY>LATE は RR 1:2 執行込みでは再現せず
- W≈44–47% < ランダム W≈49% — 勝率優位なし
- OOS2 のみ pass は過学習リスク

**next_actions**

- H-B EARLY 単体は **Gate2 不可** → reject 方向
- H-M5 フィルタ有効性は P2-B LATE 対照で確認済み

**catalog_updates**

- H-B: Phase1 **reject**（Gate2 不可、OOS 不安定）

---

### KB-L1-B-20260904

| 項目 | 内容 |
|---|---|
| batch_id | P2-B |
| date | 2026-09-04 |
| purpose | H-B PULL（20–40% 戻し）+ LATE 対照 |
| decision_question | 初押し執行は EARLY より優位か？ |
| hypotheses | H-B PULL（主）, H-B LATE（対照） |
| metrics | P2-HB-PULL, P2-HB-LATE-CTRL |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **reject**
- PULL 全 split 執行 EV 負（OOS P≈−¥301〜−¥329）
- LATE 対照: 執行 EV=+¥4.1, P≈¥113, N=27.2/月 → EV 正だが N 帯不足

**batch_verdict:** reject

**learnings**

- PULL は EARLY より劣る — 初押し待ちは H-B では機能しない
- LATE（+1.5% 遅入）は EV 正 → **H-M5 遅入禁止の根拠を再確認**
- LATE はエントリーとして不採用（N 不足 + 戦略矛盾）

**next_actions**

- H-B PULL 棄却
- H-M5 を他 L1 候補のフィルタとして継続利用

**catalog_updates**

- H-B PULL: reject

---

### KB-L1-C-20260904

| 項目 | 内容 |
|---|---|
| batch_id | P2-C |
| date | 2026-09-04 |
| purpose | H-B EARLY + H-D PULL 合成 |
| decision_question | 合成で Gate2 到達可能か？ |
| hypotheses | H-B + H-D + H-M4 |
| metrics | P2-HBD-COMPOSITE（IS/OOS1/OOS2） |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **conditional**
- OOS1: P≈¥386, W=51.4%, N=58.2/月 → Gate1 pass / Gate2 fail
- OOS2: P≈¥363, N=61.4/月 → Gate1 fail（N 帯超過）
- **P1-C（H-D のみ）OOS P≈¥741–884 より大幅劣化**（劣化率 0.44–0.57）

**batch_verdict:** conditional（合成メリットなし）

**learnings**

- H-B 追加は H-D 単体の執行 P を **半減以下に劣化**
- 同一 bar H-B 優先ルールでも H-D の edge を H-B が希薄化
- Gate2 到達には寄与せず

**next_actions**

- H-B + H-D 合成は **不採用**
- H-D + H-M4（P1-C）を引き続き最良候補として維持

**catalog_updates**

- composite H-B+H-D: reject

---

### KB-L1-D-20260904

| 項目 | 内容 |
|---|---|
| batch_id | P2-D |
| date | 2026-09-04 |
| purpose | H-B × セッション（EU_US / TOKYO） |
| decision_question | セッション限定で edge 増幅するか？ |
| hypotheses | H-B EARLY × H-C セッション |
| metrics | P2-HB-EU, P2-HB-TOKYO |
| sample_period | OOS1+OOS2 |

**result_summary**

- batch_verdict: **reject**
- N≈14–16/月に激減（Gate1 N 帯不可）
- EU OOS2 のみ P≈¥105（W=52.6%）—  pocket だが N 不足
- TOKYO / EU OOS1 は EV 負またはゼロ

**batch_verdict:** reject

**learnings**

- セッション分割は N を 1/3 に削減、edge 増幅なし
- Phase0 H-C conditional との合成は H-B では機能しない

**next_actions**

- H-B × セッション分割は停止
- H-C は H-D 等別 L1 との組み合わせを別途検討

**catalog_updates**

- H-B session split: reject

---

### KB-B08-20260906

| 項目 | 内容 |
|---|---|
| batch_id | B08 |
| date | 2026-09-06 |
| purpose | H-F2 ボラ急騰後の平均回帰 edge（Phase0） |
| decision_question | VOL_SHOCK 後、中点回帰は CONT より優位か？ |
| hypotheses | H-F2 MID（主）, CONT（対照）, ABSREV |
| metrics | P0-HF2-MID, ABSREV, CONT, FREQ |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **conditional**
- MID mean_edge=+0.0095%, hit=51.2%, n=41,119 → weak（CONT より +0.019% 優位）
- ABSREV pass（ショック後 range 縮小 70% hit）
- 頻度 ≈1,287 shocks/月 — 検出条件が緩い（range×2.5 OR rv top 10%）

**batch_verdict:** conditional

**learnings**

- 回帰方向は記述統計で CONT より優位だが edge 絶対値は極小
- イベント過多 → Phase1 では cooldown 必須
- ABSREV pass はボラ収縮現象の存在を確認（トレード方向性とは別）

**next_actions**

- P3-A 執行込み検証へ
- reject 時は B09（H-F3）へ pivot

**catalog_updates**

- H-F2: Phase0 conditional

---

### KB-P3-A-20260906

| 項目 | 内容 |
|---|---|
| batch_id | P3-A |
| date | 2026-09-06 |
| purpose | H-F2 中点回帰の Phase1 執行込み検証 |
| decision_question | MID 回帰は RR 1:2 + H-M4 で Gate1/2 pass か？ |
| hypotheses | H-F2 MID（主）, CONT（対照） |
| metrics | P3-HF2-MID（IS/OOS1/OOS2）, CONT-CTRL |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **reject**
- 全 split 執行 EV 負（OOS P≈−¥27〜−¥211）
- W≈46–49% ≈ ランダム — 勝率優位なし
- preflight **sign_parity warn**: P0 mean=+0.0001 vs P1 theory EV=−0.39

**batch_verdict:** reject

**learnings**

- Phase0 weak 優位は Phase1 執行込みで再現せず（H-A2/H-B と同型）
- preflight 符号チェックが非再現を計測前に警告 — 5 段パイプライン有効
- VOL_SHOCK 即時エントリー + RR 1:2 では Gate1 不可

**next_actions**

- H-F2 MID エントリー棄却
- B09 H-F3（レンジ回帰）Phase0 を次バッチに選定
- H-D + H-M4 hold 継続

**catalog_updates**

- H-F2: Phase1 **reject**

---

### KB-B09-20260906

| 項目 | 内容 |
|---|---|
| batch_id | B09 |
| date | 2026-09-06 |
| purpose | H-F3 レンジ内回帰 edge（Phase0） |
| decision_question | レンジ端タッチからの回帰は BREAK より優位か？ |
| hypotheses | H-F3 REVERT（主）, BREAK（対照） |
| metrics | P0-HF3-EDGE, EV, FREQ |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **promote**
- EDGE: mean=+0.096%, hit=64.1%, n=5,294 → **pass**
- vs BREAK diff=+0.19% — 回帰方向が明確に優位
- mean\|edge\|=0.24% → Gate2 必要 0.5% には未達（weak EV 指標）

**learnings**

- Phase0 では **H-D / H-B / H-F2 より strongest** の一つ
- 12h tight range + 2h edge touch の組み合わせ有効

**next_actions**

- P3-B 執行込み検証

---

### KB-P3-B-20260906

| 項目 | 内容 |
|---|---|
| batch_id | P3-B |
| date | 2026-09-06 |
| purpose | H-F3 レンジ端回帰の Phase1 執行込み |
| decision_question | REVERT は RR 1:2 + H-M4 で Gate1/2 pass か？ |
| hypotheses | H-F3 REVERT, BREAK 対照 |
| metrics | P3-HF3-REVERT（IS/OOS1/OOS2） |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **reject**（Gate1 — N 帯不足）
- OOS2: 執行 P≈¥261, W=71.4%, EV=+¥18.7, **N=14/月**
- OOS1: P≈¥11, N=8/月
- preflight sign_parity **pass**（P0 +0.001 vs P1 theory +15.4）
- BREAK 対照: P≈−¥222 — 回帰優位は Phase1 でも維持

**learnings**

- **edge は OOS2 で確認** — H-F2 とは異なり Phase0→Phase1 符号一致
- **N≈12–14/月** が Gate1/Gate2 阻害要因（EV ではない）
- cooldown=12 でも N 帯 40–60 に遠い → P3-B-NR で N 拡大が必要

**next_actions**

- **P3-B-NR**: cooldown 短縮 / 検出緩和で N→50 探索
- Gate1 pass 後 P3-C（H-D filter + H-F3）

**catalog_updates**

- H-F3: Phase0 promote → Phase1 **conditional（N 不足）**

---

### KB-V1-20260906

| 項目 | 内容 |
|---|---|
| batch_id | V1 |
| date | 2026-09-06 |
| purpose | Gate1 pass 候補の WF+MC+Robustness 検証 |
| decision_question | H-D / H-F3 は Research Gate pass か？ |
| hypotheses | H-D+M4, H-F3 cd4_q40_at20 |
| metrics | WF, MC, PF, Sharpe, Research Gate |
| sample_period | VALIDATION 2025-07-01..2026-02-28 |

**result_summary**

- H-D: Research Gate **pass**, Gate1 Y, Gate2 N, P≈¥741, WF 3/3, PF=1.64
- H-F3: Research Gate **pass**, Gate1 N (N=33), Gate2 N, P≈¥234, WF 3/3, PF=1.53

**learnings**

- 両戦略とも Walk Forward 100% pass — 1 期間だけ強いパターンではない
- Research Gate と Gate2 は独立 — edge ありでもビジネス目標未到達
- MC ruin=0%（修正後）。初期バグ: `0.0 or 1.0` で ruin 判定が誤動作

**next_actions**

- H-D Paper 継続
- B10 MFE/MAE で Exit 候補評価
- P3-C 合成結果と比較

**catalog_updates**

- HD-M4: research_gate → **pass**
- HF3-cd4_q40_at20: research_gate → **pass**

---

### KB-B10-20260906

| 項目 | 内容 |
|---|---|
| batch_id | B10 |
| date | 2026-09-06 |
| purpose | MFE/MAE Exit 分析 |
| decision_question | 固定 RR 1:2 が edge を削っていないか？ |
| hypotheses | H-D, H-F3 |
| metrics | MFE, MAE, TP/SL grid hit rates |
| sample_period | TRAIN + VALIDATION |

**result_summary**

- H-D VALIDATION: mfe_mae_ratio=2.06, avg MFE=0.81%, avg MAE=0.40%
- H-F3 VALIDATION: mfe_mae_ratio=1.35, avg MFE=0.43%, avg MAE=0.32%
- H-D: TP 0.5% hit=73%, SL 0.8% hit=25% — RR 1:2 より狭い TP 候補あり

**learnings**

- H-D は MFE >> MAE — Exit 再設計余地あり（TP 0.5% で 73% hit）
- H-F3 は MFE/MAE 比は正だが絶対値小 — edge 薄い

**next_actions**

- H-D P1-R2: TP 0.5%/0.8% 候補を VALIDATION で grid（defer）
- H-F3 Gate2 追求は停止（EV 上限）

---

### KB-P3-C-20260906

| 項目 | 内容 |
|---|---|
| batch_id | P3-C |
| date | 2026-09-06 |
| purpose | H-D zone filter + H-F3 合成 |
| decision_question | RSI 押し目 zone 内 H-F3 で edge 増幅するか？ |
| hypotheses | H-F3 + H-D zone (lookback=48) |
| metrics | P3C-COMPOSITE IS/OOS1/OOS2 |
| sample_period | 2024-01-01..2026-08-31 |

**result_summary**

- batch_verdict: **conditional**
- OOS2: P≈¥339 vs H-F3 単体 ¥278 — **+22% P 改善**
- OOS2: EV≈¥9.4 vs H-F3 ¥5.9 — edge 増幅確認
- Gate1 fail: N=36/mo（帯 40–60 未達）
- filter_ratio≈70% — zone フィルタは緩すぎ

**learnings**

- 合成は H-F3 単体より OOS2 で P/EV 改善 — 方向性は正
- N 帯不足が継続ボトルネック
- zone lookback=48 は広すぎる可能性 — 24 で再検証 defer

**next_actions**

- H-D 単体 + Paper 継続（最良 Gate1 候補）
- P3-C zone 厳格化（lookback 24）— defer
- Gate2 未到達 → L1 探索継続

**catalog_updates**

- P3C-HD-HF3: status → conditional

---

### KB-PT-B-20260906

| 項目 | 内容 |
|---|---|
| batch_id | PT-B |
| purpose | H-D forward 継続監視（V1 Research Gate pass 後） |
| decision_question | Gate1 forward 再現 + 執行劣化率は許容か？ |
| metrics | PT-B-FORWARD |

**result_summary**

- batch_verdict: **conditional**
- PT-Gate1 pass: EV=+¥14.1, N=49/月, W=55.4%
- PT-Gate2 fail: P≈¥692
- degradation=0.86 vs Phase1、v1_research_gate_hd=true

**next_actions**

- P1-R2 Exit grid（B10 示唆）へ
- Paper 継続監視

---

### KB-P1-R2-20260906

| 項目 | 内容 |
|---|---|
| batch_id | P1-R2 |
| purpose | B10 示唆の固定 TP/SL grid（VALIDATION のみ） |
| decision_question | TP 0.5%/SL 0.5% で Gate1/Research Gate 改善するか？ |

**result_summary**

- batch_verdict: **conditional**
- **Best**: sl=0.5%, tp=1.0% → P≈¥1,031, EV=+¥21.2, N=48.7, **Gate1 pass**, **Research Gate pass**
- Baseline (0.8%/1.6%): P≈¥741
- **+39% P 改善**（VALIDATION）。Gate2 未到達（41%）

**learnings**

- B10 MFE/MAE 示唆どおり、狭い TP で edge 効率改善
- TEST 未使用（VALIDATION tuning のみ）

**next_actions**

- ~~IS/OOS2/TEST で best config 再計測~~ → **P1-R2C 完了**（KB-P1-R2C 参照）
- H-D 葉ルール更新 → **phase1-spec §2.1 canonical 確定**

---

### KB-P1-R2C-20260906

| 項目 | 内容 |
|---|---|
| batch_id | P1-R2C |
| purpose | P1-R2 best config 固定 — TRAIN/VAL/TEST 再現（tuning 禁止） |
| decision_question | sl=0.5%/tp=1.0% は OOS（TEST）でも Gate1 pass するか？ |

**result_summary**

- batch_verdict: **conditional**
- TRAIN: EV=+¥24.5, P≈¥1,148, Gate1 pass
- VALIDATION: EV=+¥21.2, P≈¥1,031, Gate1 pass, Research Gate pass
- TEST: EV=+¥14.1, P≈¥727, Gate1 pass（Gate2 の 29%）
- PT-B（canonical）: P≈¥943 forward（旧 ¥692 から +36%）

**learnings**

- P1-R2 VALIDATION best は **TEST でも EV>0・Gate1 pass** — overfit 兆候なし
- TEST P は VAL より −30% だが依然 Gate1 帯内（N=51）
- canonical exit を phase1-spec / V1 / Paper に統一

**next_actions**

- ~~Paper 継続監視（PT-B）~~ → **継続中**（KB-PT-B-2 参照）
- Gate2 未到達のため本番採用は見送り

**catalog_updates**

- H-D: status → **Phase1 canonical 確定**（sl0.5%/tp1.0% + H-M4）

---

### KB-PT-B-2-20260906

| 項目 | 内容 |
|---|---|
| batch_id | PT-B（継続監視 #2） |
| purpose | canonical H-D forward 監視 — P1-R2C ベンチマーク + 停止ルール |
| decision_question | monitoring_status=continue で Paper 継続可能か？ |

**result_summary**

- batch_verdict: **conditional**
- PT-Gate1 pass: EV=+¥19.2, N=49, P≈¥943（複利 forward）
- **monitoring_status: continue**（停止ルール未発動）
- split: VALIDATION EV=+¥21.2/P=¥1,031, TEST EV=+¥14.1/P=¥727 — いずれも Gate1 pass
- Gate2: 14 ヶ月中 0 ヶ月 pass（gate2_pass_rate=0%）
- final_BR=¥63,200（+26.4%）

**learnings**

- P1-R2C ベンチマークと forward が整合（ev_vs_p1r2c≈1.17）
- 2026-04〜06 は低 P 帯（¥148–532/月）だが EV>0 維持
- Gate2 未到達でも Gate1 + Research Gate は安定

**next_actions**

- **Paper 継続**（monitoring_status=continue）
- 月次で `python3 -m scripts.paper.run_pt PT-B` を再実行
- Gate2 L0 再ベースラインは PM 判断

---

改訂: 2026-09-06（P1-R2C canonical exit 確定）

---

### KB-P3CR-20260906

| 項目 | 内容 |
|---|---|
| batch_id | P3-C-R |
| purpose | zone lookback 48→24 厳格化 |
| decision_question | 厳格 zone で edge/N 改善するか？ |

**result_summary**

- batch_verdict: **conditional**（EV>0 だが Gate1 fail）
- VALIDATION: P≈¥161 vs P3-C ¥175（**劣化**）、N=17 vs 25
- filter_ratio: 42% vs 70%（厳格化でシグナル半減）

**learnings**

- lookback=24 は **厳しすぎ** — P3-C (48) の方が VALIDATION で優位

**next_actions**

- P3-C (lookback=48) を hold。zone 厳格化は停止

---

### KB-B11-20260906

| 項目 | 内容 |
|---|---|
| batch_id | B11 |
| purpose | H-F4 THRUST_DECAY Phase0 |
| decision_question | 減速後に revert/continuation edge があるか？ |

**result_summary**

- batch_verdict: **reject**
- events=1,368/月≈43、mean_edge≈0（revert vs cont 差なし）

**next_actions**

- H-F4 Phase1 不要。棄却

---

### KB-P1-HA-20260906

| 項目 | 内容 |
|---|---|
| batch_id | P1-HA |
| purpose | H-A SPIKE revert 執行込み（未検証） |
| decision_question | Phase0 reject でも執行ルールで edge あるか？ |

**result_summary**

- batch_verdict: **reject**
- OOS 執行 EV≈−¥4.5、W≈28% — Phase0 結論を **再確認**

**next_actions**

- H-A 探索停止（edge-catalog reject 維持）

---

改訂: 2026-09-06（PT-B / P1-R2 / P3-C-R / B11 / P1-HA）

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
- **Gate2 fail**（月次 P≈¥1,013 << ¥10,000 目標）

**batch_verdict:** conditional

**learnings**

- Phase0 の PULL 優位は RR 1:2 バックテストでも再現（執行込み EV 正）
- **H-M4 土日停止が N 帯調整に必須**（47.6/月 ≈ 目標 50）
- Gate2（月次 +¥10,000）には未到達。EV 絶対値が小さい

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
- Gate2 fail（月次 P≈¥740–1,211）

**batch_verdict:** conditional

**learnings**

- H-D + H-M4 合成は OOS で Gate1 を安定 pass
- H-A2 除外でも N 帯・EV 符号は維持
- 月次 +¥10,000 目標には RR/幅の再設計が必要

**next_actions**

- **Phase1-R**: SL/TP 幅グリッド + Gate2 到達可否を探索
- 採用確定前に実装フェーズへは進まない
- H-B（遅入禁止）フィルタは B03-R 後に合成候補

**catalog_updates**

- composite: Phase1 conditional（H-D + H-M4）

---

改訂: 2026-09-03

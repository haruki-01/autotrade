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

（検証開始後、上記テンプレでここに追記していく）

_（まだ記録なし）_

---

改訂: 2026-09-03

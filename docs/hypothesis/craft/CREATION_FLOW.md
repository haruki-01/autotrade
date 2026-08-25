# 仮説作成フロー（精緻版・再現性）

**目的:** 誰が・いつやっても同じ品質の「ready カード」に到達する。  
**禁止:** このフロー中に formal eval・パラメータ探索・デモ発注をしない。

入口: 歪みの疑問 / 敗因からの再作成  
出口: `inventory/HYP-xxx` が `status: ready`

簡易版: [FLOW.md](../FLOW.md)  
考え方: [WINNING_HYPOTHESIS_CREATION.md](./WINNING_HYPOTHESIS_CREATION.md)  
ストック技法: [HYPOTHESIS_STOCK_METHODS.md](./HYPOTHESIS_STOCK_METHODS.md)

---

## ステータス機械

```text
idea → draft → evidence_wip → checklist → ready
                              ↘ blocked（データ不足）
                              ↘ discarded（作成段階で棄却）
```

| status | 意味 | 次に許されること |
|--------|------|------------------|
| `idea` | メモだけ | 5行仮説を書く |
| `draft` | 5行＋カードあり | 証拠作業 |
| `evidence_wip` | 証拠作成中 | 証拠完了まで ready 不可 |
| `ready` | チェックリスト全通 | **検証フローへ渡す** |
| `blocked` | データ/前提不足 | 解除条件をカードに書く |
| `discarded` | 作成段階で棄却 | postmortems に1行理由 |

---

## Step C0 — 試行番号の予約（多重検定の自覚）

1. `inventory/README.md` で同一主歪み（E?）の既存カード数を数える  
2. 新 ID を採番: `HYP-NNN`（欠番なし）  
3. カード先頭に書く: `PRIOR_TRIALS_SAME_DISTORTION: N本目`

**ゲート:** ID と試行番号が無いものは draft にしない。

---

## Step C1 — 歪み選択（1つだけ）

入力: `MARKET_EDGE_MAP`  
出力: `PRIMARY_DISTORTION: E?` + `FAMILY: momentum|mean-reversion|structural`

チェック:
- [ ] 主歪みは1つ
- [ ] 「やらない戦場」に抵触しない
- [ ] 個人が取れるか列が「不可」なら blocked か discarded

---

## Step C2 — 5行仮説（コード禁止）

テンプレ（必須・空欄不可）:

```text
CLAIM:
WHY:
WHO LOSES:
DIES WHEN:
TESTABLE:   # 検証で何が起きたら捨てるか（作成時点の約束）
```

**ゲート:** WHO LOSES または DIES WHEN が空 → draft 不可。  
ファイル: `inventory/HYP-NNN-slug.md` に貼る。

---

## Step C3 — 翻訳・差分・自由度契約

カードに必須:

| 欄 | 内容 |
|----|------|
| TRANSLATION_NOTE | 学術/実務を単一BTCにどう翻訳したか＋弱点 |
| WHY_NOT_PRIOR_FAIL | 既存 FAIL（H01等）と同じ敗因をどう避けるか |
| DEGREES_OF_FREEDOM | 0 または 1（触るノブ名を1つまで） |
| CAPACITY_NOTE | 証拠金$30×レバ3で意味があるか（[SIZING.md](./SIZING.md)） |

**ゲート:** 自由度 ≥2 → 分割して別カードにしろ。

---

## Step C4 — 現象ルール（インジ名禁止）

`MINIMAL_PHENOMENON_RULE` を1段落で書く。  
禁止語の目安: 「パラメータは後で」「いくつか試して」「AND条件を足す」。

**ゲート:** ルールがインジの列挙だけ → 書き直し。

---

## Step C5 — 粗い証拠の計画と実行

1. `COARSE_EVIDENCE_PLAN` をカードに書く  
2. `evidence/E?-topic.md` を新規作成（レバなし・合否ゲートなし）  
3. データソース・期間・定義・結果・限界を固定フォーマットで残す  
4. カード status → `evidence_wip` → 完了後も当面 `draft`

証拠ファイル必須見出し:

```markdown
## データ（パス・期間・定義）
## 結果（表）
## 解釈（作成継続 / 作成棄却）
## 限界
## 再現（コマンド or 手順）
```

**ゲート（作成棄却）:** 方向・裾が費用線を明らかに下回る → `discarded` + 理由1行。  
**ゲート（継続）:** 「あり」または「判断保留だが機制は残す」→ checklist へ。

---

## Step C6 — QUALITY_CHECKLIST

[QUALITY_CHECKLIST.md](./QUALITY_CHECKLIST.md) をカード末尾で全項目チェック。

**ゲート:** 1つでも未チェック → `ready` 禁止。

---

## Step C7 — ready 宣言（作成の完了）

1. `status: ready`  
2. `ready_at: YYYY-MM-DD`  
3. `validation_handoff:` に検証フローへの引き渡しメモ（logic_id 案、棄却条件の再掲）  
4. `inventory/README.md` の表を更新  

**再現性バンドル（作成完了時に揃っていること）:**

- [ ] カードパスが安定している  
- [ ] 証拠ファイルパスがカードからリンクされている  
- [ ] 試行番号・自由度が書いてある  
- [ ] TESTABLE（棄却条件）が検証側と矛盾しない文言  

→ ここから先は [VALIDATION_FLOW.md](./VALIDATION_FLOW.md) のみ。

---

## 作成フローのアンチパターン

| NG | 代わり |
|----|--------|
| 証拠前に workstream 作成 | ready まで待つ |
| BT結果をカードの CLAIM に書く | 検証レイヤの話 |
| 同時に3ファミリーを1カードに | カード分割 |
| 「とりあえず ready」 | checklist 厳守 |

---

## エージェント用チェックリスト（コピー用）

```text
Creation Progress:
- [ ] C0 採番・試行番号
- [ ] C1 歪み1つ
- [ ] C2 5行仮説
- [ ] C3 翻訳・差分・自由度≤1
- [ ] C4 現象ルール
- [ ] C5 evidence 計画→実行→解釈
- [ ] C6 QUALITY_CHECKLIST
- [ ] C7 ready + inventory 更新
```

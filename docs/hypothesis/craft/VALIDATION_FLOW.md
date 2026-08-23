# 仮説検証フロー（精緻版・再現性）

**目的:** 同じ ready カード・同じ lock・同じ設定なら、誰が回しても同じ合否になる。  
**入口:** `inventory` が `status: ready` のものだけ。  
**出口:** research 記録 + postmortem +（PASSなら）holdout / デモ検討。

作成側: [CREATION_FLOW.md](./CREATION_FLOW.md)  
環境: [EVAL_PROTOCOL.md](../../master/EVAL_PROTOCOL.md) · [eval/README.md](../../../eval/README.md)  
Skill: `.cursor/skills/backtest-eval/SKILL.md`

---

## 絶対禁止（再現性を壊す行為）

1. `--synthetic` で合否を出す  
2. lock なし / config hash 不一致のまま eval  
3. Set B を見て同期間のパラメータを再最適化  
4. ready でないカードの実装  
5. 1ランでルールを2点以上変える  
6. ゲート閾値を結果に合わせて動かす  

違反したらそのランは **無効**（research に `invalidated` と注記）。

---

## ステータス機械（検証）

```text
ready → implementing → eval_B → (fail|pass_B) → eval_C? → demo_candidate?
                ↘ aborted（実装不能・バグ）
```

| status（カード側） | 意味 |
|--------------------|------|
| `ready` | 検証待ち |
| `implementing` | コード中 |
| `in_eval` | formal 実行中/済の記録中 |
| `fail` / `pass` | 主ゲート（通常 Set B）の結果 |
| `holdout_fail` / `holdout_pass` | Set C |
| `archived` | 追わない（学びは postmortem） |

---

## Step V0 — 引き渡し監査（実装前）

ready カードを開き、次を確認:

- [ ] `status: ready`
- [ ] TESTABLE / 棄却条件が書いてある
- [ ] DEGREES_OF_FREEDOM ≤ 1
- [ ] evidence リンクが存在する
- [ ] サイジング前提が [SIZING.md](./SIZING.md) / `configs/eval_v1.yaml` と矛盾しない

**ゲート不合格 → 作成フローに差し戻し**（検証しない）。

カードを `implementing` に更新。workstream フォルダを作成または更新。

---

## Step V1 — 環境ロックの確認

```bash
# lock が無い、または config を変えた直後
PYTHONPATH=src python3 -m autotrade.cli eval-prepare --config configs/eval_v1.yaml
```

確認項目:

- [ ] `eval/locks/eval_v1.lock.yaml` が存在
- [ ] `forbid_synthetic: true`
- [ ] `config_sha256` が現行 `configs/eval_v1.yaml` と一致
- [ ] Set B の `data_source` が `bybit` または `binance_vision`（synthetic 禁止）
- [ ] ファイル hash がディスクと一致

Vision 使用時はレポートに必ず書く: **live 前に Bybit 再確認**。

**ゲート不合格 → eval 禁止。**

---

## Step V2 — 最小実装（差分1点）

1. `logic_id` を registry に登録（カードの validation_handoff と一致）  
2. 現象ルールをコード化（カード外の条件を足さない）  
3. 触るノブが契約された1点以外に増えていないかレビュー  

**ゲート:** 「ついでにフィルタ追加」→ 別仮説カードへ分割して作成フローへ戻す。

---

## Step V3 — Formal Eval Set B（本検証）

```bash
PYTHONPATH=src python3 -m autotrade.cli eval \
  --config configs/eval_v1.yaml \
  --logic-id <logic_id>
```

必須成果物:

| 成果物 | 場所 |
|--------|------|
| metrics.json / trades.csv | `artifacts/evals/...` |
| 人間向けレポート | `eval/reports/...` |
| research 追記 | `docs/research/`（自動） |
| workstream LATEST | 自動 |
| カード更新 | status / run_id / gate |

記録する再現キー:

- eval_version  
- config_sha256 / lock 作成時刻  
- git commit  
- logic_id / hypothesis_id  
- data_source  
- sizing（margin / risk / lev）  

---

## Step V4 — 合否の解釈（改ざんしない）

現行ゲート（`eval_v1` 系）:

1. 平均トレード損益 > 0  
2. トレード数 ≥ 100  
3. 最大 DD ≤ 20%  

| 結果 | アクション |
|------|------------|
| 全クリア | `pass` → V5 |
| EVまたはDD不合格 | `fail` → V6 postmortem。**同ロジック再チューニング禁止** |
| 回数のみ不足 | `fail`（判定保留扱い）。次は**作成フローで別カード**（イベント定義の変更）。同一コードの閾値漁り禁止 |
| 実装バグ（未来参照等） | 修正して **同一カードで再 eval 可**（ルール変更ではない場合のみ） |

---

## Step V5 — Holdout Set C（B合格後のみ）

```bash
PYTHONPATH=src python3 -m autotrade.cli eval --logic-id <id> --set C
```

- パラメータ変更禁止  
- 符号が大きく壊れたら `holdout_fail`（採用しない）  
- 耐えたら `holdout_pass` → デモ検討リストへ（デモ実装は別プロジェクト段階）

---

## Step V6 — Postmortem（PASS/FAIL 問わず）

`postmortems/YYYY-MM-DD-<logic_id>.md` 最低項目:

```markdown
## 何を試したか（カードID・logic_id）
## 環境キー（eval_version / data_source / git）
## 数値（EV / DD / n / リターン）
## 構造的学び（再発防止）
## 次の作成への示唆（検証側から作成へ返す一文）
```

inventory と workstream README を同期更新。

---

## Step V7 — 試行台帳（多重検定）

`docs/research/INDEX.md` と inventory の試行番号が、歪みごとの累計試行と矛盾しないか確認。  
「報告した成功だけ残す」は禁止。FAIL も残す。

---

## 再現性チェックリスト（ラン完了時）

```text
Validation Progress:
- [ ] V0 引き渡し監査
- [ ] V1 lock / hash OK
- [ ] V2 差分1点のみ
- [ ] V3 Set B formal + 成果物揃い
- [ ] V4 ゲート解釈が表どおり（動かしていない）
- [ ] V5（PASS時のみ）Set C
- [ ] V6 postmortem
- [ ] V7 台帳更新
```

---

## 検証 ≠ 作成の再オープン

検証中に「やっぱりルールを変えたい」場合:

1. 現ランを完了して FAIL/学びを書く  
2. **新しい HYP-ID** で作成フローを最初から  
3. 旧カードは archived / fail のまま残す  

同一カード上でのルール改変は再現性違反。

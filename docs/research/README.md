# 研究ログ — 運用ルール

仮説・売買ロジック・検証結果・知見を **将来の bot 更新の資産** として蓄積する場所。

## ファイル構成

```text
docs/research/
  README.md          ← 本ファイル（運用）
  INDEX.md           ← 一覧（自動更新）
  registry.yaml      ← マスタ（自動追記 + 手動編集可）
  _template.md       ← 手動追記用テンプレ
  entries/           ← 1検証 = 1 Markdown（自動生成）
```

## 1回の検証に残す情報

| 区分 | 項目 | なぜ必要か |
|------|------|------------|
| 識別 | run_id, 日付, git commit | 再現・比較 |
| 仮説 | ID, 名称, 狙う歪み(E1〜E8), 一言 | 「何を試したか」を忘れない |
| ロジック | エントリー/退出/フィルタ/サイズ/レバ | 同じ失敗を繰り返さない |
| 検証 | Set A/B/C, 期間, データソース | 条件が違えば結果も違う |
| コスト | fee, slip, funding の扱い | 甘いBTとの差 |
| 結果 | 期待値, DD, 回数, ゲート | 合否の根拠 |
| 知見 | 構造的理由, 残す/捨てる | **将来の設計に効く部分** |
| 次 | next_actions | 次に何を変えるか |
| 成果物 | artifacts パス | トレード一覧の再確認 |

## ステータス

| 値 | 意味 |
|----|------|
| `proposed` | 仮説だけ。未バックテスト |
| `smoke` | 合成データ等。パイプライン確認のみ |
| `fail` | 実データでゲート不合格 |
| `pass` | 実データでゲート合格 |
| `archived` | 採用しないが参照用 |

## 自動追記

バックテスト実行後、デフォルトで `registry.yaml` と `entries/` に追記し、`INDEX.md` を更新する。

```bash
autotrade backtest --set B --hypothesis-id H01 --logic-id mtf_ema_pullback_v1
```

合成データ（`--synthetic`）は自動で `smoke` ステータス。

## 手動追記

1. `_template.md` をコピーして `entries/` に置く
2. `registry.yaml` の `runs:` に同内容を YAML で追加
3. `autotrade research refresh-index` で INDEX 更新

## ルール

1. **1 run = 1 変更点**（エントリーか退出かフィルタのどれか1つ）
2. 合成データの PASS を採用判断に使わない
3. FAIL も必ず記録する（「やらないリスト」が資産）
4. 知見の「構造的理由」を必ず1行以上書く
5. パラメータ最適化の試行回数は `notes` に残す

## 関連

- [INDEX.md](./INDEX.md)
- [registry.yaml](./registry.yaml)
- [MARKET_EDGE_MAP.md](../MARKET_EDGE_MAP.md)

# ドキュメント地図

このリポジトリの知識は **3層** に分けて管理する。

**最初に読む:** [master/CURRENT.md](./master/CURRENT.md) — 理想状態・合否・いまの論点・次ステップ。

```text
docs/
  master/        ← 全体の正（方針・前提・合否ルール）
  workstreams/   ← 小プロジェクト（ロジック／要素ごとのリサーチ）
  research/      ← 検証ランの機械可読ログ（自動追記）
  ops/           ← 開発環境・画面レイアウトなど運用メモ
```

## どれを読むか

| 知りたいこと | 場所 |
|--------------|------|
| **いま何をするか・理想状態** | [master/CURRENT.md](./master/CURRENT.md) |
| **仮説の精度・立て方・学び** | [hypothesis/](./hypothesis/) |
| プロジェクト全体の目的・フェーズ | [master/PROJECT_PLAN.md](./master/PROJECT_PLAN.md) |
| 日付順の探索ログ | [master/IMPLEMENTATION_PLAN.md](./master/IMPLEMENTATION_PLAN.md) |
| 歪み・優位の前提 | [master/MARKET_EDGE_MAP.md](./master/MARKET_EDGE_MAP.md) · [優位の採点軸](./master/MARKET_ADVANTAGE_AXES.md) |
| 特定ロジックの進捗・メモ | [workstreams/](./workstreams/) |
| **demo の起動** | [ops/DEMO.md](./ops/DEMO.md) |
| バックテストの数値ログ | [research/INDEX.md](./research/INDEX.md) |

## 書き分けルール（短く）

1. **仮説の質・証拠・敗因の型** → `hypothesis/`（実装より先）
2. **方針・合否・全体ロードマップ** → `master/`
3. **1ロジックの進捗** → `workstreams/<id>/`
4. **1回のバックテスト結果** → `research/`
5. **Cursor の操作メモ・環境** → `ops/`

詳細は [workstreams/README.md](./workstreams/README.md) と `.cursor/rules/docs-organization.mdc` を参照。

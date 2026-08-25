# このリポジトリの画面レイアウト（自動設定）

このプロジェクトを Cursor で開くと、次の配置になる設定を入れています。

```text
左: フォルダ   |   中央: コード / Diff   |   右: チャット
```

設定ファイル:
- `.vscode/settings.json`
- `autotrade.code-workspace`（こちらを開いても同じ）

Cursor では `workbench.sideBar.location = left` が **Editor レイアウト**（フォルダ左・チャット右）に対応します。

## あなたがやること（これだけ）

### A. すでにパソコンに `autotrade` フォルダがある

1. Cursor を開く
2. メニュー **File → Open Folder…**（Mac なら **Open…**）
3. `autotrade` フォルダを選んで Open
4. 画面がチャット中心なら、右上で **Editor** に切り替える
5. 左にフォルダ一覧が出たら成功

最新のキー用ファイルを取るなら、Cursor の下の Terminal で:

```bash
git fetch origin
git checkout cursor/slow-oos-validation-d77f
git pull origin cursor/slow-oos-validation-d77f
```

### B. まだフォルダがない（初回）

手元の Terminal（または Cursor の Terminal）で:

```bash
git clone https://github.com/haruki-01/autotrade.git
cd autotrade
git checkout cursor/slow-oos-validation-d77f
cursor -n .
```

`cursor` コマンドが無いときは、Cursor で **File → Open Folder…** → 今作った `autotrade` を選ぶ。

## うまくいかないとき

- **Agents だけの画面** → 右上 / タイトルバーで **Editor** に切替
- それでも逆 → `Cmd/Ctrl+Shift+P` → `View: Toggle Primary Side Bar Position`
- 古い配置が残る → ウィンドウを閉じて、このワークスペースを開き直す

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

手元のターミナルで:

```bash
git clone https://github.com/haruki-01/autotrade.git
cd autotrade
git fetch origin
git checkout cursor/secrets-folder-and-planning-d77f
cursor -n autotrade.code-workspace
```

または Cursor で `File` → `Open Workspace from File…` → `autotrade.code-workspace` を選ぶ。

左にチャットが出ていたら、右上で **Editor** に切り替える。

## うまくいかないとき

- **Agents だけの画面** → 右上 / タイトルバーで **Editor** に切替
- それでも逆 → `Cmd/Ctrl+Shift+P` → `View: Toggle Primary Side Bar Position`
- 古い配置が残る → ウィンドウを閉じて、このワークスペースを開き直す

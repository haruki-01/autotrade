# Local development notes

## おすすめ画面レイアウト（左=フォルダ / 中央=コード・レビュー / 右=チャット）

目指す配置:

```text
| エクスプローラー |  エディタ / Diff / PRレビュー  |  Agent / Chat  |
|     （左）      |           （中央）            |     （右）     |
```

### いちばん確実な手順

1. **Editor レイアウトにする**（Agent 専用レイアウトだと左右が逆転しやすい）
   - 右上の歯車（または Layout）から **Editor** / **Editor (Classic)** を選ぶ
   - または Cursor Settings（`Ctrl+Shift+J` / Mac: `Cmd+Shift+J`）→ **Default Layout** → `Editor`
2. **ファイルツリーを左へ**
   - `View` → `Appearance` → **Move Primary Side Bar Left**
   - または Command Palette（`Ctrl/Cmd+Shift+P`）で `View: Toggle Primary Side Bar Position`
3. **チャットを右へ**
   - 右上 Layout / 歯車の **Agent Sidebar** を **Right** にする
   - Primary（フォルダ）と Agent（チャット）は **左右反対** にするのがポイント
4. **中央でレビュー**
   - コード: 普通にファイルを開く
   - PR差分: Source Control / GitHub PR 拡張、または Cursor の Review パネル
   - Diff: ファイルを開いた状態で変更箇所を中央で確認

### settings.json に書く場合（補助）

`Ctrl/Cmd+Shift+P` → `Preferences: Open User Settings (JSON)`:

```json
{
  "workbench.sideBar.location": "left"
}
```

そのうえで Layout メニューの **Agent Sidebar = Right** を確認する。  
（Cursor のバージョンによっては Agent 側の設定が優先され、再起動後に戻ることがあります。そのときは Layout メニュー側を再度指定してください。）

### うまくいかないとき

- いま **Agents ビュー** だけの画面になっている → `File` → **Open IDE**、またはタイトルバーの **Editor** 切替を押す
- 左にチャット・右にフォルダになっている → Agent Sidebar と Primary Side Bar の左右を入れ替える
- 設定がウィンドウごとに崩れる → Cursor Settings で **Sync layouts across windows** を一度オフにしてから配置し直す

---

## Open this repo in another Cursor window

Cloud Agent はサーバ上で動くため、手元でコードを触る・ターミナルで Bybit に繋ぐには **ローカルの Cursor ウィンドウ** が必要です。

### 手順

1. GitHub でリポジトリをクローン（未取得の場合）
   ```bash
   git clone https://github.com/haruki-01/autotrade.git
   cd autotrade
   ```
2. 作業ブランチを取得
   ```bash
   git fetch origin
   git checkout cursor/secrets-folder-and-planning-d77f
   ```
3. Cursor で **別ウィンドウ** を開く
   - メニュー: `File` → `New Window`
   - そのウィンドウで `File` → `Open Folder…` → クローンした `autotrade` を選択
   - またはターミナルから:
     ```bash
     cursor -n /path/to/autotrade
     ```
4. 上記の **左フォルダ / 中央レビュー / 右チャット** レイアウトにする
5. ローカルで依存関係を入れて実データ検証
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e .
   autotrade fetch-data --set B
   autotrade backtest --set B
   ```

### UI について

Phase 1 は Web UI なしです。確認するものは:

- コード: Cursor 中央のエディタ
- バックテスト結果: `artifacts/backtests/*/metrics.json` と `trades.csv`
- チャット: 右の Agent / Chat
- 将来の Dashboard: Phase 5 以降

PR のレビューだけなら、GitHub の PR ページまたは Cursor の PR 差分ビューでもコード確認できます。

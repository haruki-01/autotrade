# Local development notes

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
4. ローカルで依存関係を入れて実データ検証
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e .
   autotrade fetch-data --set B
   autotrade backtest --set B
   ```

### UI について

Phase 1 は Web UI なしです。確認するものは:

- コード: Cursor のエディタ
- バックテスト結果: `artifacts/backtests/*/metrics.json` と `trades.csv`
- 将来の Dashboard: Phase 5 以降

PR のレビューだけなら、GitHub の PR ページまたは Cursor の PR 差分ビューでもコード確認できます。

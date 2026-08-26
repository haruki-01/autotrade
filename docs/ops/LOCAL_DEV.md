# Local development notes

## 画面レイアウト（自動設定済み）

リポジトリに `.vscode/settings.json` を入れてあり、このフォルダを開くと次の配置になります。

```text
左: フォルダ   |   中央: コード / Diff   |   右: チャット
```

手順の詳細は [LAYOUT.md](./LAYOUT.md) を参照。

---

## Open this repo in another Cursor window

Cloud Agent はサーバ上で動くため、手元でコードを触る・ターミナルで Bybit に繋ぐには **ローカルの Cursor ウィンドウ** が必要です。

### 手順（プロジェクトを IDE で開く）

1. パソコンにリポジトリが無いときだけ clone
   ```bash
   git clone https://github.com/haruki-01/autotrade.git
   cd autotrade
   ```
2. いまの作業ブランチを取る
   ```bash
   git fetch origin
   git checkout cursor/slow-oos-validation-d77f
   git pull origin cursor/slow-oos-validation-d77f
   ```
3. Cursor でフォルダを開く（どれか1つ）
   - メニュー: **File → Open Folder…** → `autotrade` を選ぶ
   - または Terminal: `cursor -n /path/to/autotrade`
4. 左がチャットだけのときは、右上で **Editor** に切替。成功すると左にフォルダ一覧が出る
5. （任意）依存関係を入れて検証
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.lock.txt
   pip install -e . --no-deps
   ```

---

## 検証結果を再現するとき

`data/cache/` は gitignore 対象なので、環境を作り直すと消えます。取り直しは冪等で、
同じ span を再取得すれば同じ sha256 になります（[取得の欠損バグ](../hypothesis/postmortems/2026-08-24-slow-oos-and-reproducibility.md)
を直したあと確認済み）。

```bash
PYTHONPATH=src python3 scripts/prewarm_multi_cache.py --config configs/eval_v2.yaml   # 10〜15分
PYTHONPATH=src python3 -c "
import sys; sys.path.insert(0,'src')
from pathlib import Path
from autotrade.eval.multi import prepare_multi_lock
prepare_multi_lock('configs/eval_v2.yaml', lock_path=Path('eval/locks/eval_v2.lock.yaml'))"
PYTHONPATH=src python3 scripts/run_slow_pack.py --set C --logics sh01_tp_4atr
```

**`requirements.lock.txt` のバージョンを外すと数値が変わります。** 入力データを sha256 で
固定しても、それを読む numpy / pandas が違えば結果は一致しません（2026-08-24 に実測。
23本中11本がズレた）。各レポートの冒頭に実行環境と lock のハッシュが記録してあるので、
過去の数値と比べるときはまずそこを合わせてください。

### UI について

Phase 1 は Web UI なしです。確認するものは:

- コード: Cursor 中央のエディタ
- バックテスト結果: `artifacts/backtests/*/metrics.json` と `trades.csv`
- チャット: 右の Agent / Chat
- 将来の Dashboard: Phase 5 以降

PR のレビューだけなら、GitHub の PR ページまたは Cursor の PR 差分ビューでもコード確認できます。

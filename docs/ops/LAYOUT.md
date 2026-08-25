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
4. 画面がチャット中心なら、**Ctrl+Shift+P（Mac は Cmd+Shift+P）→ `Open IDE`** を実行（詳細は下の「Editor に切り替える」）
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

## 「Editor に切り替える」具体操作

チャットばかりで左にフォルダが見えないとき用。どれか1つでよい。

### いちばん確実（推奨）

1. キーボードで **Ctrl+Shift+P**（Mac は **Cmd+Shift+P**）
2. `Open IDE` と打つ
3. **Open IDE** を選んで Enter

これでコードを編集する画面（左にフォルダ）が開く。

### 画面のボタンでやる場合

1. ウィンドウの **一番上のバー** を見る（歯車の近く）
2. **Layout**（または Agent / Editor と書かれたメニュー）を開く
3. **Editor** を選ぶ

見つからないときは上の「Open IDE」を使う。

### それでもダメなとき

メニュー **File → Open Editor Window**  
または **File → Open Folder…** で `autotrade` を開き直す。

注意: チャット左下の Agent / Ask / Plan は AI の話し方の切替で、Editor 切替とは別です。

## うまくいかないとき

- 左がチャットのまま → 上の **Open IDE**
- フォルダが右にある → Ctrl/Cmd+Shift+P → `View: Toggle Primary Side Bar Position`
- 古い配置が残る → ウィンドウを閉じて、このフォルダを開き直す


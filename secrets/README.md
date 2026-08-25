# Secrets（APIキー・パスワード管理）

このフォルダに Bybit などの認証情報を置きます。  
**実キーは Git にコミットしません。** `.example` だけが「空の見本」としてリポジトリに入ります。

## デモのキー（これが正）

**左のフォルダ一覧から `secrets/demo/bybit.txt` を開いて書いてください。**

`.env` は Git に載せない設定のため、Cursor の一覧に出ません。以前の `bybit.env` が開けなかったのはそのためです。

1. リポジトリを最新にする
2. 左の Explorer → `secrets` → `demo` → **`bybit.txt`**
3. `BYBIT_API_KEY` と `BYBIT_API_SECRET` に testnet キーを書く
4. このファイルは **git add しない**

初回だけ、ターミナルで権限と git 保護を揃える:

```bash
PYTHONPATH=src python3 -m autotrade.cli secrets-init
```

キーを `.example` に書かないでください。GitHub に載ります。一度載ったキーは **Bybit で無効化して再発行** してください。

## ディレクトリ

| パス | 用途 |
|------|------|
| `demo/bybit.txt` | デモ（testnet）用キー。**ここを編集する** |
| `demo/bybit.env` | 旧パス。残っていれば読めるが、一覧には出ない |
| `live/` | 本番用（まだ使わない） |

## live の初期セットアップ

```bash
cp secrets/live/bybit.env.example secrets/live/bybit.env
```

live の `.env` も一覧に出ません。本番キーはパスワードマネージャ推奨。

## ルール

1. **出金権限は付けない**（取引に必要な権限のみ）
2. **demo と live でキーを分ける**
3. **IP制限を推奨**
4. キーをチャット・スクショ・ログに貼らない
5. 漏れたら Bybit 上でキーを即無効化し、再発行する
6. `chmod 600` はしない（Cursor がファイルを開けなくなることがある）

## Demo 起動

手順の正本: [docs/ops/DEMO.md](../docs/ops/DEMO.md)

```bash
PYTHONPATH=src python3 -m autotrade.cli demo --once
PYTHONPATH=src python3 -m autotrade.cli demo --submit
```

# Secrets（APIキー・パスワード管理）

このフォルダに Bybit などの認証情報を置きます。  
**実キーは Git にコミットしません。** `.example` だけがリポジトリに入ります。

## ディレクトリ

| パス | 用途 |
|------|------|
| `demo/` | デモ（testnet）用 |
| `live/` | 本番用 |

各ディレクトリに次を置いて使います（`.example` をコピーして作成）。

- `bybit.env` … APIキー / シークレット
- `account.env` … （任意）ログイン用メモ。パスワードはパスワードマネージャ推奨

## 初期セットアップ

```bash
cp secrets/demo/bybit.env.example secrets/demo/bybit.env
cp secrets/live/bybit.env.example secrets/live/bybit.env
# 任意
cp secrets/demo/account.env.example secrets/demo/account.env
cp secrets/live/account.env.example secrets/live/account.env
```

その後、各 `.env` に実際の値を記入してください。

## ルール

1. **出金権限は付けない**（取引に必要な権限のみ）
2. **demo と live でキーを分ける**（同じキーを使わない）
3. **IP制限を推奨**（Bybit の API キー設定画面）
4. `bybit.env` をチャット・スクショ・ログに貼らない
5. 漏れたら Bybit 上でキーを即無効化し、再発行する

## ファイル権限（任意・推奨）

```bash
chmod 600 secrets/demo/bybit.env secrets/live/bybit.env
```

## Demo 起動

手順の正本: [docs/ops/DEMO.md](../docs/ops/DEMO.md)

```bash
PYTHONPATH=src python3 -m autotrade.cli demo --once
PYTHONPATH=src python3 -m autotrade.cli demo --submit   # testnet キー必須
```

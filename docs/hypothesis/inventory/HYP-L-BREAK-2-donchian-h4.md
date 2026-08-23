---
id: L-BREAK-2
title: "Donchian 20/10 on 4H（サンプル確保）"
status: fail
primary_distortion: E1
created: 2026-08-22
updated: 2026-08-23
---

# Donchian 20/10 on 4H

## 1. メカニズム

- **主歪み:** E1 トレンド継続
- **なぜズレるか:** ブレイク後の追随フローは日足と同じだが、4H で測るとイベント回数が増える
- **負ける側:** 早すぎる逆張り、固定利確で大勝ちを切る側
- **個人が取れる理由:** 低〜中回転・構造退出。L-BREAK の方向性を保ちつつ n を確保

## 2. 証拠

- 親ラン L-BREAK: EV +54 / DD 3.8% / n=13（方向は良いがサンプル不足）
- リンク: `docs/workstreams/L-BREAK-donchian/` · formal batch report

## 3. 最小ルール

- **エントリー:** 4H 終値が Donchian20 高値上抜け（継続中は各4Hバケット先頭15m）
- **退出:** 4H Donchian10 安値割れ（ショートは対称）+ ATR×2 緊急 stop
- **サイズ / リスク:** `configs/eval_v1.yaml` fixed_margin
- **既存ロジックからの差分（1点）:** シグナル計算足を **日足 → 4H**（窓・退出定義は同一）

## 4. 棄却条件

- Set B で期待値 ≤ 0 または DD > 20%
- 4H でもトレード < 100 → ゲートとの相性を別議論（パラメータ弄り禁止）

## 5. データ・依存

- 必要データ: OHLCV 1d/4h/15m（4h が主シグナル）

## 6. 検証計画

- Formal set: B →（PASSなら）C
- logic_id: `donchian_h4_20_10_v1`
- workstream: `docs/workstreams/L-BREAK-2-donchian-h4/`

## 7. 結果（後で追記）

- run_id: 研究ログ INDEX 参照（L-BREAK-2 / donchian_h4_20_10_v1）
- gate: **FAIL**（期待値・DDはクリア、トレード 58 < 100）
- 学び: 4H でも単ポジ構造退出では年間100回に届きにくい。EV方向は残すが現行は採用しない

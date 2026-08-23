---
id: HYP-009
title: D-001 実証① だまし後の本突破初日
status: fail
primary_distortion: E1
created: 2026-08-22
updated: 2026-08-22
spot: SPOT-D001
logic_id: fake_then_rebreak_v1
PRIOR_TRIALS_SAME_DISTORTION: E1系の続き（002の別スポット）
---

# D-001 実証① — だまし後の本突破初日

## Formal eval Set B

| 項目 | 値 |
|------|-----|
| Gate | **FAIL**（n=1, EV-$0.81） |
| レポート | [eval/reports/20260822T095931Z_fake_then_rebreak_v1_setB.md](../../../eval/reports/20260822T095931Z_fake_then_rebreak_v1_setB.md) |

同カード再チューニング禁止。スポットは残し、測り方変更は新カード。

## 1. メカニズム

- **主歪み:** E1（ブレイク追随）＋ E6（圧縮）＋ E8（初回は撃たない）
- **なぜズレるか:** 初回ブレイクで焼けた資金が再突破に遅れる
- **負ける側:** 圧縮一発目の追随・だまし後に追えない参加者
- **個人が取れる理由:** 価格の圧縮・失敗・再突破だけ（清算データ不要）

## 2. 証拠

- スポット: [../spots/SPOT-D001-compress-fake-then-real-break.md](../spots/SPOT-D001-compress-fake-then-real-break.md)
- 深い①: [../craft/DEEP_COMPOSITE_SPOTS.md](../craft/DEEP_COMPOSITE_SPOTS.md) D-001

## 3. 最小ルール

- **エントリー:** 直近に圧縮あり → HH20上抜け後に同水準を割り込む（だまし）→ 再度 HH20 新規上抜けの初日＋4H確認
- **退出:** 日足 Donchian10 下抜け + ATRストップ
- **サイズ:** eval_v1.1（証拠金$30 / リスク$3）
- **差分:** HYP-002 は「新規上抜け」一般。本カードは**だまし後の二度目だけ**

## 4. 棄却条件

- Set B で費用後EV ≤ 0
- だまし条件を外すと説明が崩れる（二度目の意味が消える）

## 5. データ・依存

- 1d / 4h / 15m OHLCV のみ

## 6. 検証計画

- Formal set: B（Holdout C は B合格後）
- logic_id: `fake_then_rebreak_v1`
- workstream: `docs/workstreams/HYP-009-d001-fake-rebreak/`

## 5行

```text
CLAIM: 圧縮後のだまし→再突破初日は、初回ブレイクより費用後に残りやすい
WHY: 初回で焼けた追随が遅れ、二度目に流動性が乗りやすい
WHO LOSES: 圧縮一発目のブレイクハンター
DIES WHEN: 再突破後すぐ失敗水準へ回帰が続く
TESTABLE: Set B で平均トレード損益≤0 なら棄却
```

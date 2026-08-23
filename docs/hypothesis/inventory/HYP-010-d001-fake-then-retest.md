---
id: HYP-010
title: D-001 実証② だまし後本突破の再テスト支え
status: fail
primary_distortion: E1
created: 2026-08-22
updated: 2026-08-22
spot: SPOT-D001
logic_id: fake_then_retest_v1
PRIOR_TRIALS_SAME_DISTORTION: HYP-009の別測り方
---

# D-001 実証② — 本突破後の再テスト支え

## Formal eval Set B

| 項目 | 値 |
|------|-----|
| Gate | **FAIL**（n=1, EV-$0.62） |
| レポート | [eval/reports/20260822T095933Z_fake_then_retest_v1_setB.md](../../../eval/reports/20260822T095933Z_fake_then_retest_v1_setB.md) |

同カード再チューニング禁止。

## 1. メカニズム

- **主歪み:** E1 + E6 + E8
- **なぜズレるか:** 本突破の初動を逃した資金が、水準への戻りで乗る／ショートが支えで損切
- **負ける側:** 再テストを「失敗の始まり」と売る人、初動しか取れない人
- **個人が取れる理由:** だまし確定後のブレイク水準への回帰タッチ＋陽線

## 2. 証拠

- 同一スポット SPOT-D001（測り方だけ違う）

## 3. 最小ルール

- **エントリー:** HYP-009 と同じだまし→本突破のあと、ブレイク水準付近への押しで陽線確認（4H近傍）
- **退出:** Donchian10 下抜け + ATRストップ
- **サイズ:** eval_v1.1
- **差分:** ⑨は突破初日、⑩は**押し目での執行**

## 4. 棄却条件

- Set B で費用後EV ≤ 0
- 再テストが来ない／来ても支えにならない局面が大半

## 5. データ・依存

- 1d / 4h / 15m OHLCV

## 6. 検証計画

- Formal set: B
- logic_id: `fake_then_retest_v1`
- workstream: `docs/workstreams/HYP-010-d001-fake-retest/`

## 5行

```text
CLAIM: だまし後の本突破水準への再テスト支えは、突破初日より執行が安定しやすい
WHY: 遅れて乗る資金とショート損切が水準に集まりやすい
WHO LOSES: 再テストを戻り売りする人
DIES WHEN: 再テストでブレイク水準を明確に割り込む
TESTABLE: Set B で平均トレード損益≤0 なら棄却
```

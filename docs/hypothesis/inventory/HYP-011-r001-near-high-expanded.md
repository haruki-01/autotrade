---
id: HYP-011
title: R-001 高値圏×ボラ拡大
status: fail
primary_distortion: E1
created: 2026-08-22
updated: 2026-08-22
spot: SPOT-R001
logic_id: near_high_expanded_v1
PRIOR_TRIALS_SAME_DISTORTION: データ逆算由来（E1/E6）
---

# R-001 高値圏×ボラ拡大

## Formal eval Set B（eval_v1.1）

| 項目 | 値 |
|------|-----|
| Gate | **FAIL** |
| 期待値 | **-$0.60** / trade |
| DD | 0.9% |
| トレード数 | 2 |
| データ | binance_vision |
| レポート | [eval/reports/20260822T095930Z_near_high_expanded_v1_setB.md](../../../eval/reports/20260822T095930Z_near_high_expanded_v1_setB.md) |

Discovery の偏りは Holdout で再現せず。同カードの再チューニングはしない。

## 1. メカニズム

- **主歪み:** E1 + E6
- **なぜズレるか:** 高値圏＝逆張りという早とちりが払う側になる
- **負ける側:** 勢い付き高値での戻り売り
- **個人が取れる理由:** 価格位置とATR%のみ

## 2. 証拠

- [../spots/SPOT-R001-near-high-expanded.md](../spots/SPOT-R001-near-high-expanded.md)
- Discovery のみ: [../spots/DISCOVERED_FROM_DATA.md](../spots/DISCOVERED_FROM_DATA.md)（検証ではない）

## 3. 最小ルール

- **エントリー:** レンジ内位置>0.85 かつ ATR%が平均の1.25倍超 かつ close>SMA50 の**新規成立日**＋4H陽線
- **退出:** Donchian10 下抜け + ATRストップ
- **サイズ:** eval_v1.1
- **差分:** 圧縮ブレイクではなく**拡大しながらの高値圏**

## 4. 棄却条件

- Set B（Holdout）で平均トレード損益 ≤ 0
- Discovery と同期間でだけ効く場合はスヌーピング疑い

## 5. データ・依存

- 1d / 4h / 15m OHLCV

## 6. 検証計画

- Formal set: **B のみ**（Discovery 2022–2023 では合否を出さない）
- logic_id: `near_high_expanded_v1`
- workstream: `docs/workstreams/HYP-011-r001-near-high-expanded/`

## 5行

```text
CLAIM: 高値帯×ボラ拡大×中期上昇は、高値逆張りより費用後に残りやすい
WHY: 早すぎる逆張りが巻き戻される
WHO LOSES: 高値＝危険と決めつける短期ショート
DIES WHEN: 拡大が下方向ブレイクに転化する局面が大半
TESTABLE: Set B で平均トレード損益≤0 なら棄却
```

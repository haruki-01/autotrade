---
id: HYP-005
title: E6 ボラ・クラスタ — 高ボラ時はサイズ縮小または停止
status: draft
primary_distortion: E6
created: 2026-08-22
updated: 2026-08-22
family: structural
---

# E6 — ボラに合わせて撃つ量を変える（作成ドラフト）

## 作成ドラフト（検証禁止）

CLAIM:  
実現ボラが高い局面では、同じ証拠金・同じストップ％でも破産リスクとノイズ損切が増える。高ボラではサイズを落とす／新規を止めることが、方向予測なしでも期待生存を上げる。

WHY:  
ボラ・クラスタ（高ボラのあとも高ボラ）は時系列の定番事実。固定枚数・固定幅はE6を無視する（H01敗因の一部）。

WHO LOSES:  
荒い相場でも平日と同じサイズで殴り続ける個人・bot。

DIES WHEN:  
サイズ縮小が機会損失だけで、残したトレードの質が変わらない／低ボラに偏りすぎてサンプルが消える。

FAMILY: structural  
PRIMARY_DISTORTION: E6

TRANSLATION_NOTE:  
E6は方向エッジではない。**「勝つ」より「死なない」仮説。** 他の方向仮説（E1）のゲートとして後で結合しうるが、作成時点では独立主張。

COARSE_EVIDENCE_PLAN:  
`evidence/E6-vol-regime-stops.md` — ATR（または実現ボラ）高低レジームで、固定%損切のヒット率・平均不利幅を比較。

MINIMAL_PHENOMENON_RULE:  
「短期実現ボラが長期より十分高いときは、新規サイズを半分にするか新規停止」。方向シグナルは持たない。

DEGREES_OF_FREEDOM: 1（高ボラ判定の倍率）  
PRIOR_TRIALS_SAME_DISTORTION: 1本目  
WHY_NOT_H01_FAIL_MODE:  
利確・押し目を触らない。サイズ/停止のみ。  
READY_BLOCKERS: E6 evidence 未作成。サイジング$30/$3との結合方法未定義。

## チェックリスト（作成）

- [x] 方向予測でないことを明示
- [ ] evidence あり
- [ ] ready

status: **draft**

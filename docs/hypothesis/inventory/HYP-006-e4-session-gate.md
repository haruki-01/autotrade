---
id: HYP-006
title: E4 セッションゲート — 薄い時間は新規停止
status: draft
primary_distortion: E4
created: 2026-08-22
updated: 2026-08-22
family: structural
generation_method: A+L
---

# E4 — セッションゲート（作成ドラフト）

## 作成ドラフト（検証禁止）

CLAIM:  
価格発見と流動性が薄い時間帯では、同じシグナルでもスリッページ・ダマシが増え、費用後期待値が悪化する。薄い時間は新規を止める。

WHY:  
出来高・ボラはロンドン〜NYに集中しやすい（時間帯の周期性）。薄い時間に同じ閾値で撃つ側が不利。

WHO LOSES:  
アジア薄場や週末境界でも平日昼間と同じサイズ・同じ頻度で成行する個人・bot。

DIES WHEN:  
24hほぼ均質な流動性になる／ゲートがほぼ常時停止で機会損失が本体になる／時間帯効果が年によって反転。

FAMILY: structural  
PRIMARY_DISTORTION: E4  
SECONDARY: E5（週末は別カードでも可）

TRANSLATION_NOTE:  
方向予測ではなく執行ゲート。学術の「時間帯出来高」を単一BTCの新規許可マスクに翻訳。

COARSE_EVIDENCE_PLAN:  
`evidence/E4-session-liquidity.md` — UTC時間帯別の実現レンジ・出来高（または絶対リターン）。薄い帯を定義候補にする。

MINIMAL_PHENOMENON_RULE:  
「定義した薄い時間帯は新規エントリー禁止。既建玉の退出は許可」。

DEGREES_OF_FREEDOM: 1（薄い帯の境界）  
PRIOR_TRIALS_SAME_DISTORTION: 1本目  
CAPACITY_NOTE: 低回転と整合。$30単位向き。  
READY_BLOCKERS: evidence 未作成。

status: **draft**

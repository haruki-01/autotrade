---
id: HYP-003
title: E8 取引しない優位 — 往復コストを超えない見積もりでは撃たない
status: draft
primary_distortion: E8
created: 2026-08-22
updated: 2026-08-22
family: structural
---

# E8 — 取引しない優位（作成ドラフト）

## 作成ドラフト（検証禁止）

CLAIM:  
弱い・狭い値動きしか見込めない局面では、予測が当たっても往復コストで負ける。撃たないこと自体がエッジになる。

WHY:  
手数料・スリッページはほぼ確実。微小な予測力は不確実。算術的に「必要値動き ＜ 往復コスト＋余裕」なら期待値が負に寄る。

WHO LOSES:  
弱いシグナルを連打する個人・量産型bot・「毎日トレードしなければ」と思っている参加者。

DIES WHEN:  
コストが極小になる／本当に大きなエッジ局面までゲートが塞ぐ（機会損失が構造的に総EVを壊す）／ゲートが実質ノーオペで何も変えない。

FAMILY: structural  
PRIMARY_DISTORTION: E8

TRANSLATION_NOTE:  
E8は学術因子というより会計・執行の事実。L-COST formal FAILは「H01押し目に薄いゲートを足した」失敗であり、E8主張そのものの棄却ではない。本作は**独立した「撃たない」主張**として立て直す。

COARSE_EVIDENCE_PLAN:  
`evidence/E8-cost-floor.md` — 仮のシグナル密度（例: 日次ブレイク候補のATR%）分布に対し、往復0.15%＋余裕を下回る割合と、それを除いたあとのイベント後リターンを見る（レバなし）。

MINIMAL_PHENOMENON_RULE:  
「次の保有で必要な値動きの見積もり（例: ATR×係数）が、往復コスト×バッファ未満ならエントリー禁止」。エントリー自体の定義はこのカードでは持たない（別仮説のゲートとして後で結合可）。

DEGREES_OF_FREEDOM: 1（バッファ倍率のみ、証拠後に固定）  
PRIOR_TRIALS_SAME_DISTORTION: 2本目（L-COST は失敗実装。本カードは作り直し）  
WHY_NOT_H01_FAIL_MODE:  
押し目連打を前提にしない。ゲート単体の物語。固定利確とは無関係。  
READY_BLOCKERS: E8 evidence 未作成。独立ゲートとして測る土台シグナルの定義が未決。

## チェックリスト（作成）

- [x] WHO LOSES
- [x] DIES WHEN
- [ ] evidence あり
- [ ] ready

status: **draft**

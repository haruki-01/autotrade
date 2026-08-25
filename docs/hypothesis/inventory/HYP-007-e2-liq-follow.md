---
id: HYP-007
title: E2 清算継続の遅延追随（データ待ち・blocked）
status: blocked
primary_distortion: E2
created: 2026-08-22
updated: 2026-08-22
family: structural
generation_method: H
---

# E2 — 清算確認後の継続追随（作成・blocked）

## 作成ドラフト（検証禁止）

CLAIM:  
大規模清算の初動は取れないが、清算フロー確認後に同方向がしばらく続く局面がある。初動競争を避け、遅延して追随する。

WHY:  
強制決済は価格に鈍感な成行を生み、薄い板で継続を誘発しうる。

WHO LOSES:  
高レバで清算される側、および初動に遅れて逆張りする側。

DIES WHEN:  
遅延と費用で中央値が消える／清算データがノイズ／「必ず戻る」に堕ちる。

FAMILY: structural  
PRIMARY_DISTORTION: E2

TRANSLATION_NOTE:  
「やらない戦場＝初動」の裏返し。確認後のみ。

COARSE_EVIDENCE_PLAN:  
清算スパイク後の前方リターン（データ取得後）。

MINIMAL_PHENOMENON_RULE:  
「清算量スパイクを確認 → 一定の遅延 → 同方向のみ短期追随。サイズ小さめ」。

DEGREES_OF_FREEDOM: 1（遅延の長さ）  
BLOCKED_UNTIL: 清算（または同等）時系列がパイプラインに載る  
PRIOR_TRIALS_SAME_DISTORTION: 1本目  

status: **blocked**

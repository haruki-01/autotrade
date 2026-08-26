---
id: HYP-004
title: E1 週次モメンタム継続 — 単一BTCへの翻訳（希少イベント）
status: draft
primary_distortion: E1
created: 2026-08-22
updated: 2026-08-22
family: momentum
---

# E1 — 週次モメンタム継続（作成ドラフト）

## 作成ドラフト（検証禁止）

CLAIM:  
直近数週間の上昇が続いたあとも、短期的に同方向の継続が起きやすい（単一BTCの時系列モメンタム）。希少な「継続レジーム入り」だけを取る。

WHY:  
群衆の後追い・損切の同方向化。暗号はレバが強くトレンドが伸びやすい、という実務・一部実証の物語。学術のCMOMは多コインだが、「継続」現象のヒントにはなる。

WHO LOSES:  
早すぎる逆張り、トレンド中に平均回帰だけを当てにする側。大勝ちを小さく切る側。

DIES WHEN:  
モメンタムクラッシュ（急反転月）が費用後EVを消す／シグナルが日常化し回転が増えE8に負ける／単一BTCではクロスセクションほど歪みが薄い。

FAMILY: momentum  
PRIMARY_DISTORTION: E1

TRANSLATION_NOTE:  
Liu–Tsyvinski–Wu はクロスセクション。本作は「週次リターンが強いあとの前方リターン」に翻訳。**弱点を明示:** 単一銘柄・単年バイアスが大きい。Donchian日足ブレイク（HYP-001/002）とはイベント定義が異なる別試行。

COARSE_EVIDENCE_PLAN:  
`evidence/E1-weekly-momentum-forward.md` — 週次リターン上位/下位のあとの 5〜20日前方リターン分布（レバなし）。ロングのみ・ショートは別表。Buy&Holdとの差も記載。

MINIMAL_PHENOMENON_RULE:  
「確定した週のリターンが十分大きい（閾値は証拠で決める前は相対順位や単純な符号＋大きさ）→ 翌週〜数週間はロングのみ許可。退出は時間または構造割れ。固定小利確なし。」

DEGREES_OF_FREEDOM: 1（週次の強さの閾値 or 保有ホライズンのどちらか一方）  
PRIOR_TRIALS_SAME_DISTORTION: E1として3本目（001母体・002 Donchian v2の次）  
WHY_NOT_H01_FAIL_MODE:  
押し目連打しない。固定利確しない。日足インジANDにしない。  
WHY_NOT_002_ONLY:  
002は日足チャネル。件数不足。別イベント定義で希少性を保ったままサンプル構造を変える作成。  
READY_BLOCKERS: 週次モメンタム証拠未作成。閾値未契約。

## チェックリスト（作成）

- [x] WHO LOSES / 翻訳の弱点
- [ ] evidence あり
- [ ] ready

status: **draft**

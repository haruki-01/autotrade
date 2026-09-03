# Phase0 検証シート（閲覧用）

記入の正本は `phase0-verification-sheet.csv`。
定義: `phase0-stats.md` / 運用: `verification-workflow.md` / 蓄積: `knowledge-log.md`

行数: **62**

## バッチ一覧

| batch_id | purpose |
|---|---|
| B01 | 時間構造の歪みを低コストで確認し、フィルタ採用可否を決める |
| B02 | スパイク後に回帰と継続のどちらが優位か分岐する |
| B03 | 点火エッジが早期性に依存するか検証する |
| B04 | 点火亜型（圧縮解放・スイング連鎖）を独立候補にするか判断する |
| B05 | 上位トレンド内の行き過ぎ押しが再開エッジを持つか |
| B06 | 群集シグナルは即入りより押し待ち・上位整合か |
| B07 | 稀イベントに Phase1 載せる価値があるか |

## 一覧

| batch | metric_id | 仮説 | 優先 | 指標 | paired_with | status | verdict |
|---|---|---|---|---|---|---|---|
| B01 | P0-HE-RET | H-E | P0-必須 | FEE_WINDOWリターン分布 | — | todo | — |
| B01 | P0-HE-VS | H-E | P0-必須 | 他帯との差 | — | todo | — |
| B01 | P0-HE-VOL | H-E | P0-必須 | ボラ差 | — | todo | — |
| B01 | P0-HE-DIR | H-E | P0-必須 | 符号バイアス | — | todo | — |
| B01 | P0-HE-PREPOST | H-E | P0-必須 | 前30分vs後30分 | — | todo | — |
| B01 | P0-HC4-WDWE | H-C4 | P0-必須 | 平日vs土日 | — | todo | — |
| B01 | P0-HC4-FAKEBRK | H-C4 | P0-必須 | 土日の偽ブレイク率 | — | todo | — |
| B01 | P0-HC-RET | H-C | P0-必須 | セッション別平均リターン | — | todo | — |
| B01 | P0-HC-VOL | H-C | P0-必須 | セッション別ボラ | — | todo | — |
| B01 | P0-HC-TREND | H-C | P0-必須 | セッション別方向持続 | — | todo | — |
| B01 | P0-HC-REVERT | H-C | P0-必須 | セッション別回帰性 | — | todo | — |
| B02 | P0-HA-REVERT | H-A | P0-必須 | スパイク後回帰 | P0-HA-CONT | todo | — |
| B02 | P0-HA-CONT | H-A2 | P0-必須 | スパイク後継続 | P0-HA-REVERT | todo | — |
| B02 | P0-HA-REVERT15 | H-A | P0-必須 | 超短期回帰 | — | todo | — |
| B02 | P0-HA-PATH | H-A | P0-必須 | 逆行0.3ATR先 vs 同方向1ATR先 | — | todo | — |
| B02 | P0-HA-BY-SESS | H-A | P0-必須 | 回帰のセッション分割 | — | todo | — |
| B03 | P0-HB-EARLY | H-B | P0-必須 | 点火早期エッジ | P0-HB-LATE | todo | — |
| B03 | P0-HB-LATE | H-B | P0-必須 | 遅入サブサンプル | P0-HB-EARLY | todo | — |
| B03 | P0-HB-PULL | H-B | P0-必須 | 初押し後エッジ | — | todo | — |
| B03 | P0-HB-FREQ | H-B | P0-必須 | 月次点火回数 | — | todo | — |
| B03 | P0-HB-BODY | H-B | P0-必須 | 実体条件ありなし差 | — | todo | — |
| B04 | P0-HB2-DIR | H-B2 | P0-必須 | 圧縮解放の方向継続 | — | todo | — |
| B04 | P0-HB2-FAKE | H-B2 | P0-必須 | フェイク解放率 | — | todo | — |
| B04 | P0-HB2-FREQ | H-B2 | P0-必須 | 月次回数 | — | todo | — |
| B07 | P0-HA3-REVERT2 | H-A3 | P0-拡張 | 2回目スパイク後回帰 | — | todo | — |
| B07 | P0-HA3-RATE | H-A3 | P0-拡張 | 月次ダブルスパイク回数 | — | todo | — |
| B07 | P0-HA4-CONT | H-A4 | P0-拡張 | 反転失敗後継続 | — | todo | — |
| B07 | P0-HA4-FALSE | H-A4 | P0-拡張 | 定義の偽陽性 | — | todo | — |
| B04 | P0-HB3-CONT | H-B3 | P0-拡張 | 連続スイング更新後継続 | — | todo | — |
| B04 | P0-HB3-3RD | H-B3 | P0-拡張 | 3回目更新到達率 | — | todo | — |
| B07 | P0-HB4-POST | H-B4 | P0-拡張 | 12h確定後の継続 | P0-HB4-CTRL | todo | — |
| B07 | P0-HB4-CTRL | H-B4 | P0-拡張 | 確定直後入りとの差 | P0-HB4-POST | todo | — |
| B03 | P0-HB5-SPLIT | H-B5 | P0-拡張 | 高実体vs低実体 | — | todo | — |
| B07 | P0-HC2-GAP | H-C2 | P0-拡張 | 週明けギャップ分布 | — | todo | — |
| B07 | P0-HC2-CONT | H-C2 | P0-拡張 | gap方向継続 | P0-HC2-REVERT | todo | — |
| B07 | P0-HC2-REVERT | H-C2 | P0-拡張 | gap埋め | P0-HC2-CONT | todo | — |
| — | P0-HE2-RET | H-E2 | P0-拡張 | 追証時刻窓リターン | — | blocked_pending_rule | — |
| B06 | P0-HD-RAW | H-D | P0-拡張 | RSIシグナル即入り | P0-HD-PULL | todo | — |
| B06 | P0-HD-PULL | H-D | P0-拡張 | 初押し後 | P0-HD-RAW | todo | — |
| B06 | P0-HD-ALIGN | H-D | P0-拡張 | 12h同方向のみ | — | todo | — |
| B06 | P0-HD-FREQ | H-D | P0-拡張 | 月次回数 | — | todo | — |
| B06 | P0-HD2-MAG | H-D2 | P0-拡張 | キリ番吸引 | — | todo | — |
| B06 | P0-HD2-REJECT | H-D2 | P0-拡張 | キリ番反発 | — | todo | — |
| B06 | P0-HD2-THROUGH | H-D2 | P0-拡張 | キリ番貫通継続 | — | todo | — |
| B06 | P0-HD3-IMMEDIATE | H-D3 | P0-拡張 | EMAクロス直後 | P0-HD3-DELAY | todo | — |
| B06 | P0-HD3-DELAY | H-D3 | P0-拡張 | クロス後待機 | P0-HD3-IMMEDIATE | todo | — |
| B06 | P0-HD4-BOUNCE | H-D4 | P0-拡張 | ％水準での反発 | P0-HD4-BREAK | todo | — |
| B06 | P0-HD4-BREAK | H-D4 | P0-拡張 | ％水準での貫通 | P0-HD4-BOUNCE | todo | — |
| B06 | P0-HD5-FADE | H-D5 | P0-拡張 | ピンバー逆方向 | P0-HD5-CONT | todo | — |
| B06 | P0-HD5-CONT | H-D5 | P0-拡張 | ピンバー同方向 | P0-HD5-FADE | todo | — |
| B05 | P0-HF1-RESUME | H-F1 | P0-拡張 | 行き過ぎ押し後の再開 | P0-HF1-CTRL | todo | — |
| B05 | P0-HF1-CTRL | H-F1 | P0-拡張 | 押し待ちなし対照 | P0-HF1-RESUME | todo | — |
| B05 | P0-HF1-FREQ | H-F1 | P0-拡張 | 月次回数 | — | todo | — |
| — | P0-HF2-ABSREV | H-F2 | P0-拡張 | ショック後ボラ収縮 | — | todo | — |
| — | P0-HF2-MID | H-F2 | P0-拡張 | ショック足中点回帰 | — | todo | — |
| — | P0-HF3-EDGE | H-F3 | P0-拡張 | レンジ端回帰 | — | todo | — |
| — | P0-HF3-EV | H-F3 | P0-拡張 | 平均|edge|が+2%帯か | — | todo | — |
| — | P0-HF4-REV | H-F4 | P0-拡張 | 減速後の反転 | — | todo | — |
| — | P0-HF4-CONT | H-F4 | P0-拡張 | 減速後も継続 | — | todo | — |
| — | P0-HM1-SPLIT | H-M1 | 乗算器 | 12h順行vs逆行分割 | — | todo | — |
| — | P0-HM5-SPLIT | H-M5 | 乗算器 | 遅入禁止ありなし | — | todo | — |
| — | P0-HM4-SPLIT | H-M4 | 乗算器 | 曜日・セッション分割 | — | todo | — |

## 結果記入列（CSV）

`batch_id`, `purpose`, `decision_question`, `paired_with`, `n`, `hit_rate`, `mean_edge`, `median_edge`, `p25`, `p75`, `mean_abs_move`, `vs_baseline`, `verdict`, `sample_period`, `notes`

改訂: 2026-09-03

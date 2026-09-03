# Phase0 検証シート（閲覧用）

記入の正本は `phase0-verification-sheet.csv`。定義は `phase0-stats.md`。

`status`: todo / in_progress / done / blocked_pending_rule  
`verdict`: pass / weak / fail / insufficient_n / （未記入）

行数: **62**

## 一覧

| metric_id | 仮説 | 優先 | 指標 | イベント | h* | status | verdict | notes |
|---|---|---|---|---|---|---|---|---|
| P0-HE-RET | H-E | P0-必須 | FEE_WINDOWリターン分布 | FEE_WINDOW 05:30-06:30 | window | todo | — |  |
| P0-HE-VS | H-E | P0-必須 | 他帯との差 | FEE_WINDOW vs random | — | todo | — |  |
| P0-HE-VOL | H-E | P0-必須 | ボラ差 | FEE_WINDOW | window | todo | — |  |
| P0-HE-DIR | H-E | P0-必須 | 符号バイアス | FEE_WINDOW | window | todo | — |  |
| P0-HE-PREPOST | H-E | P0-必須 | 前30分vs後30分 | 05:00-05:30 / 06:30-07:00 | 30m | todo | — |  |
| P0-HC4-WDWE | H-C4 | P0-必須 | 平日vs土日 | WD vs WE buckets | h60 | todo | — |  |
| P0-HC4-FAKEBRK | H-C4 | P0-必須 | 土日の偽ブレイク率 | WE ∩ SPIKE | h60 | todo | — |  |
| P0-HC-RET | H-C | P0-必須 | セッション別平均リターン | TOKYO/EUROPE_US/OFF | h60 | todo | — |  |
| P0-HC-VOL | H-C | P0-必須 | セッション別ボラ | 同上 | — | todo | — |  |
| P0-HC-TREND | H-C | P0-必須 | セッション別方向持続 | 同上 | — | todo | — |  |
| P0-HC-REVERT | H-C | P0-必須 | セッション別回帰性 | SPIKE by session | h60 | todo | — |  |
| P0-HA-REVERT | H-A | P0-必須 | スパイク後回帰 | SPIKE | h60 | todo | — |  |
| P0-HA-CONT | H-A2 | P0-必須 | スパイク後継続 | SPIKE | h60 | todo | — |  |
| P0-HA-REVERT15 | H-A | P0-必須 | 超短期回帰 | SPIKE | h15 | todo | — |  |
| P0-HA-PATH | H-A | P0-必須 | 逆行0.3ATR先 vs 同方向1ATR先 | SPIKE | path | todo | — |  |
| P0-HA-BY-SESS | H-A | P0-必須 | 回帰のセッション分割 | SPIKE×SESSION | h60 | todo | — |  |
| P0-HB-EARLY | H-B | P0-必須 | 点火早期エッジ | IGNITE@3本目 | h120 | todo | — |  |
| P0-HB-LATE | H-B | P0-必須 | 遅入サブサンプル | IGNITE及び+1.5%超 | h120 | todo | — |  |
| P0-HB-PULL | H-B | P0-必須 | 初押し後エッジ | IGNITE後20-40%戻し | h120 | todo | — |  |
| P0-HB-FREQ | H-B | P0-必須 | 月次点火回数 | IGNITE | — | todo | — |  |
| P0-HB-BODY | H-B | P0-必須 | 実体条件ありなし差 | IGNITE split | h120 | todo | — |  |
| P0-HB2-DIR | H-B2 | P0-必須 | 圧縮解放の方向継続 | SQUEEZE_RELEASE | h120 | todo | — |  |
| P0-HB2-FAKE | H-B2 | P0-必須 | フェイク解放率 | SQUEEZE_RELEASE | h30 | todo | — |  |
| P0-HB2-FREQ | H-B2 | P0-必須 | 月次回数 | SQUEEZE_RELEASE | — | todo | — |  |
| P0-HA3-REVERT2 | H-A3 | P0-拡張 | 2回目スパイク後回帰 | DOUBLE_SPIKE | h60 | todo | — |  |
| P0-HA3-RATE | H-A3 | P0-拡張 | 月次ダブルスパイク回数 | DOUBLE_SPIKE | — | todo | — |  |
| P0-HA4-CONT | H-A4 | P0-拡張 | 反転失敗後継続 | FAILED_EDGE_REVERSAL | h120 | todo | — |  |
| P0-HA4-FALSE | H-A4 | P0-拡張 | 定義の偽陽性 | FAILED_EDGE_REVERSAL | h120 | todo | — |  |
| P0-HB3-CONT | H-B3 | P0-拡張 | 連続スイング更新後継続 | SWING_CHAIN | h120 | todo | — |  |
| P0-HB3-3RD | H-B3 | P0-拡張 | 3回目更新到達率 | SWING_CHAIN | — | todo | — |  |
| P0-HB4-POST | H-B4 | P0-拡張 | 12h確定後の継続 | PRE_12H_CLOSE | h240 | todo | — |  |
| P0-HB4-CTRL | H-B4 | P0-拡張 | 確定直後入りとの差 | 12h close only | h240 | todo | — |  |
| P0-HB5-SPLIT | H-B5 | P0-拡張 | 高実体vs低実体 | IGNITE body split | h120 | todo | — |  |
| P0-HC2-GAP | H-C2 | P0-拡張 | 週明けギャップ分布 | Fri close→Mon open | — | todo | — |  |
| P0-HC2-CONT | H-C2 | P0-拡張 | gap方向継続 | WEEK_OPEN | h240 | todo | — |  |
| P0-HC2-REVERT | H-C2 | P0-拡張 | gap埋め | WEEK_OPEN | h240 | todo | — |  |
| P0-HE2-RET | H-E2 | P0-拡張 | 追証時刻窓リターン | 公式時刻窓 | window | blocked_pending_rule | — | GMO追証判定時刻を定数化してから実施 |
| P0-HD-RAW | H-D | P0-拡張 | RSIシグナル即入り | RSI_EXIT_OS | h120 | todo | — |  |
| P0-HD-PULL | H-D | P0-拡張 | 初押し後 | RSI_EXIT_OS pull | h120 | todo | — |  |
| P0-HD-ALIGN | H-D | P0-拡張 | 12h同方向のみ | RSI_EXIT_OS∩12h | h120 | todo | — |  |
| P0-HD-FREQ | H-D | P0-拡張 | 月次回数 | RSI_EXIT_OS | — | todo | — |  |
| P0-HD2-MAG | H-D2 | P0-拡張 | キリ番吸引 | ROUND_TOUCH | h60 | todo | — |  |
| P0-HD2-REJECT | H-D2 | P0-拡張 | キリ番反発 | ROUND_TOUCH | h60 | todo | — |  |
| P0-HD2-THROUGH | H-D2 | P0-拡張 | キリ番貫通継続 | ROUND_TOUCH | h120 | todo | — |  |
| P0-HD3-IMMEDIATE | H-D3 | P0-拡張 | EMAクロス直後 | EMA_CROSS_1H | h120 | todo | — |  |
| P0-HD3-DELAY | H-D3 | P0-拡張 | クロス後待機 | EMA_CROSS_1H +delay | h120 | todo | — |  |
| P0-HD4-BOUNCE | H-D4 | P0-拡張 | ％水準での反発 | PCT_LEVEL | h60 | todo | — |  |
| P0-HD4-BREAK | H-D4 | P0-拡張 | ％水準での貫通 | PCT_LEVEL | h60 | todo | — |  |
| P0-HD5-FADE | H-D5 | P0-拡張 | ピンバー逆方向 | PIN_12H | h240 | todo | — |  |
| P0-HD5-CONT | H-D5 | P0-拡張 | ピンバー同方向 | PIN_12H | h240 | todo | — |  |
| P0-HF1-RESUME | H-F1 | P0-拡張 | 行き過ぎ押し後の再開 | TREND_EXCESS_PULL | h240 | todo | — |  |
| P0-HF1-CTRL | H-F1 | P0-拡張 | 押し待ちなし対照 | trend thrust no pull | h240 | todo | — |  |
| P0-HF1-FREQ | H-F1 | P0-拡張 | 月次回数 | TREND_EXCESS_PULL | — | todo | — |  |
| P0-HF2-ABSREV | H-F2 | P0-拡張 | ショック後ボラ収縮 | VOL_SHOCK | h120 | todo | — |  |
| P0-HF2-MID | H-F2 | P0-拡張 | ショック足中点回帰 | VOL_SHOCK | h120 | todo | — |  |
| P0-HF3-EDGE | H-F3 | P0-拡張 | レンジ端回帰 | RANGE_BOUND edge | h120 | todo | — |  |
| P0-HF3-EV | H-F3 | P0-拡張 | 平均|edge|が+2%帯か | RANGE_BOUND edge | h120 | todo | — |  |
| P0-HF4-REV | H-F4 | P0-拡張 | 減速後の反転 | THRUST_DECAY | h240 | todo | — |  |
| P0-HF4-CONT | H-F4 | P0-拡張 | 減速後も継続 | THRUST_DECAY | h240 | todo | — |  |
| P0-HM1-SPLIT | H-M1 | 乗算器 | 12h順行vs逆行分割 | any core metric | varies | todo | — | 主指標に対する分割行 |
| P0-HM5-SPLIT | H-M5 | 乗算器 | 遅入禁止ありなし | H-B系 | h120 | todo | — | P0-HB-EARLY/LATEと重複記録可 |
| P0-HM4-SPLIT | H-M4 | 乗算器 | 曜日・セッション分割 | any core metric | varies | todo | — | HC/HC4と共用 |

## 結果記入列（CSV）

CSV には次も含まれる: `n`, `hit_rate`, `mean_edge`, `median_edge`, `p25`, `p75`, `mean_abs_move`, `vs_baseline`, `sample_period`

改訂: 2026-09-03

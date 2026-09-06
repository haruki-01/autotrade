# Phase3 検証仕様

Phase0 延長（B08+）および新 L1 候補の Phase1 同等検証。  
L0 / Gate 定義: [SPEC.md](../SPEC.md)、運用: [verification-roadmap.md](verification-roadmap.md)。

---

## 1. バッチ一覧

| batch_id | 前提 | 主仮説 | 問い |
|---|---|---|---|
| **B08** | — | H-F2 | ボラ急騰後に平均回帰 edge が残るか？ |
| **B09** | — | H-F3 | レンジ端タッチから回帰 edge があるか？ |
| **P3-A** | B08 conditional+ | H-F2 MID | 中点回帰は執行込み Gate1/2 pass か？ |
| **P3-B** | B09 promote | H-F3 REVERT | Gate1/2 pass か？ |
| **P3-B-NR** | P3-B N 不足 | H-F3 | N 帯 40–60 に到達できるか？ |
| **P3-C** | P3-B-NR Gate1 | H-F3 + H-D zone | zone 内 H-F3 で edge 増幅するか？ |

---

## 2. B08 — H-F2 Phase0

| 項目 | 定義 |
|---|---|
| イベント | `VOL_SHOCK`: rv_20 上位 10% **or** range ≥ median×2.5 |
| P0-HF2-MID | ショック足 close がレンジ中点より上→short edge、下→long edge（h120） |
| P0-HF2-ABSREV | ショック後 24 本平均 range が shock range より縮小するか |
| 対照 | P0-HF2-CONT（ショック継続方向） |

```bash
python3 -m scripts.phase0.run_batch B08
python3 -m scripts.phase0.run_batch B09
```

---

## 3. P3-A — H-F2 Phase1

| 項目 | 定義 |
|---|---|
| トリガー | VOL_SHOCK 確定 bar |
| エントリー | close が mid より上→short、下→long（ショック bar close） |
| R | max(1.0% × entry, 0.5×ATR14) |
| SL / TP | RR 1:2、時間切れ 24 本 |
| フィルタ | H-M4 土日停止 |
| cooldown | N≈50 目標で調整 |
| 対照 | P3-HF2-CONT-CTRL（ショック継続） |

Preflight（必須）:

- シグナル数 ≥ 50（ALL）
- Phase0 MID mean_edge 符号 vs Phase1 理論 EV 符号一致（warn）

```bash
python3 -m scripts.phase1.run_p3_batch P3-A
python3 -m scripts.phase1.run_p3_batch P3-B
```

---

## 4. P3-C — H-D zone + H-F3 合成

| 項目 | 定義 |
|---|---|
| 前提 | H-F3 Gate1 pass 設定 `cd4_q40_at20`（P3-B-NR） |
| フィルタ | H-D RSI exit-OS トリガー後 **48 本以内** の zone のみ H-F3 エントリー許可 |
| 合成ルール | H-F3 単体 Gate1 必須（P2-C 教訓） |
| tuning | **VALIDATION のみ**（TEST ロック） |

```bash
python3 -m scripts.phase1.run_p3_batch P3-C
```

**結果（2026-09-06）**: conditional — OOS2 P≈¥339（H-F3 単体 +22%）、Gate1 fail（N=36）

---

## 5. 合格ゲート（二層）

[phase1-spec.md §6](phase1-spec.md) / [validation-spec.md](validation-spec.md) と同一。

| 層 | Gate | 条件 |
|---|---|---|
| Research | Research Gate | EV>0, PF≥1.15, WF≥60%, MC, Robustness |
| Business | Gate1 | 執行 EV > 0、N = 40–60/月 |
| Business | Gate2 | 執行 P ≥ ¥2,500（OOS 平均） |

Gate1 pass 候補は **V1** で Research Gate を確認してから Paper へ。

---

## 6. 成果物

| パス | 内容 |
|---|---|
| `data/phase0/b08_results.json` | B08 結果 |
| `data/phase0/b09_results.json` | B09 結果 |
| `data/phase3/p3a_results.json` | P3-A 結果 |
| `data/phase3/p3b_results.json` | P3-B 結果 |
| `data/phase3/p3c_results.json` | P3-C 結果 |
| `data/validation/v1_all_results.json` | V1 Research Gate |
| [validation-verification-sheet.csv](validation-verification-sheet.csv) | 記入シート |

改訂: 2026-09-06（P3-C, Hybrid Validation）

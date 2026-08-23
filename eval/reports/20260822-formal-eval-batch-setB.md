# Formal Eval 一括レポート — Set B（2026-08-22）

## 環境

| 項目 | 値 |
|------|-----|
| eval_version | `eval_v1` |
| 期間 | 2024-01-01 → 2024-12-31（Set B） |
| データ | **binance_vision** 実足（Bybit 不通のため。live 前に Bybit 再確認） |
| 初期資金 | 10,000 USDT |
| レバ | 3.0 |
| コスト | fee 5.5bps/side + slip 2bps/side |
| ゲート | 期待値>0 **かつ** トレード≥100 **かつ** DD≤20% |
| Lock | `eval/locks/eval_v1.lock.yaml` |

**結論: 5本すべて Gate FAIL。デモ/本番には進まない。**

---

## サマリー比較

| 仮説 | logic_id | Gate | 期待値 (USDT) | DD | トレード | 総リターン | 最終残高 |
|------|-----------|------|---------------|-----|----------|------------|----------|
| H01 | mtf_ema_pullback_v1 | **FAIL** | -3.10 | 49.4% | 594 | -43.3% | 5,672 |
| L-COST | cost_gate_v1 | **FAIL** | -3.73 | 51.6% | 570 | -45.0% | 5,501 |
| L-MOM-VOL | vol_scaled_trend_v1 | **FAIL** | -6.59 | 98.4% | 1,064 | -98.3% | 169 |
| L-BREAK | donchian_20_10_v1 | **FAIL*** | +54.34 | 3.8% | **13** | +7.0% | 10,697 |
| H21 | donchian_20_10_long_only | **FAIL*** | +122.43 | 2.0% | **8** | +9.7% | 10,973 |

\* 期待値・DDはクリアだが、**トレード数不足（≥100）** で判定保留扱い＝ゲート不合格。

---

## モデル別所見

### 1. H01 — MTF EMA押し目（ベースライン）

- 回転過多 + 固定利確で費用負け（既知の敗因を再確認）
- 不合格要因: 期待値マイナス、DD超過

### 2. L-COST — 費用ゲート

- トレードは 594→570 とわずかに減ったが、**期待値・DDとも H01 より悪化**
- 「弱いシグナルを切る」効果は、この実装・この年では確認できず
- 次: ゲート閾値の微調整より、**エントリー自体の見直し（L-BREAK 系）を優先**

### 3. L-MOM-VOL — ボラ調整トレンド・トレール

- 最悪成績。トレード過多（1,064）・勝率 29%・DD ほぼ全損
- ATR トレール + 押し目執行が、実足では過回転・深い損切になっている
- 次: 現行ルールのままの再探索は禁止。**レジーム or 執行の1点だけ**を変えるか、一旦 archived 候補

### 4. L-BREAK — Donchian 20/10

- 期待値プラス・DD 小さいが **n=13 で統計不足**
- 方向性としては最もマシ（費用も極小）
- 次: 期間延長（A+B）や 15m 執行頻度の上げ方を **サンプル確保目的で**検討（カーブフィット禁止）

### 5. H21 — Donchian Long only

- L-BREAK より期待値・リターンは良いが **n=8**
- 2024 の BTC 上昇バイアスの可能性。サンプル不足のため採用不可
- L-BREAK とセットでサンプル確保後に再判定

---

## 推奨ネクスト（1系統だけ）

1. **最優先:** L-BREAK / H21 のサンプル不足を解消する設計変更を1点（例: 日足ブレイク後の 4H 確認エントリーで回数を増やす）→ 再び formal eval  
2. H01 / L-COST / L-MOM-VOL の現行版は **採用しない**（research に FAIL 蓄積済み）  
3. live 前には必ず **Bybit 実足**で同 lock 数値を再確認

---

## 成果物

| 仮説 | 個別レポート | Artifacts |
|------|--------------|-----------|
| H01 | `eval/reports/20260822T073301Z_mtf_ema_pullback_v1_setB.md` | `artifacts/evals/20260822T073301Z_setB_mtf_ema_pullback_v1` |
| L-COST | `eval/reports/20260822T073303Z_cost_gate_v1_setB.md` | `artifacts/evals/20260822T073303Z_setB_cost_gate_v1` |
| L-MOM-VOL | `eval/reports/20260822T073305Z_vol_scaled_trend_v1_setB.md` | `artifacts/evals/20260822T073305Z_setB_vol_scaled_trend_v1` |
| L-BREAK | `eval/reports/20260822T073307Z_donchian_20_10_v1_setB.md` | `artifacts/evals/20260822T073307Z_setB_donchian_20_10_v1` |
| H21 | `eval/reports/20260822T073309Z_donchian_20_10_long_only_setB.md` | `artifacts/evals/20260822T073309Z_setB_donchian_20_10_long_only` |

詳細エントリは `docs/research/INDEX.md` と各 `docs/workstreams/<id>/` を参照。

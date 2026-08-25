# 検証・評価環境（Formal Eval）

## 合成データ smoke とは何か

| 用語 | 意味 | 合否に使えるか |
|------|------|----------------|
| **synthetic / smoke** | 乱数で作った偽のローソク足。コードが動くかの確認用 | **不可** |
| **formal eval（本検証）** | 過去の実市場データ + 固定コスト・固定設定 | **可（唯一の合否）** |

以前の「5仮説 smoke」はパイプライン確認だけ。採用判断には使わない。

## この環境の約束

1. **実データのみ**（Bybit 優先。不通時のみ Binance Vision を lock に記録して許可）
2. **実装と同じ数値** → 正本は [`configs/eval_v1.yaml`](../configs/eval_v1.yaml)
3. **再現性** → `eval/locks/eval_v1.lock.yaml` にデータ SHA256・設定・git commit を固定
4. **合否** → Set B が主判定。合格後のみ Set C

## 使い方

```bash
# 1) 実データ取得 + lock 生成（初回 / データ更新時）
PYTHONPATH=src python3 -m autotrade.cli eval-prepare --config configs/eval_v1.yaml

# 2) 本検証（1ロジック）
PYTHONPATH=src python3 -m autotrade.cli eval --logic-id cost_gate_v1

# 3) 複数ロジック
PYTHONPATH=src python3 -m autotrade.cli eval --logic-id mtf_ema_pullback_v1,cost_gate_v1,vol_scaled_trend_v1,donchian_20_10_v1,donchian_20_10_long_only
```

エージェントは `.cursor/skills/backtest-eval/SKILL.md` に従う。

## ディレクトリ

```text
configs/eval_v1.yaml     ← 数値の正本（コスト・期間・ゲート）
eval/
  README.md              ← 本ファイル
  locks/                 ← データ指紋・実行条件の固定
  reports/               ← 評価レポート（gitignore 可）
artifacts/evals/         ← ラン成果物
```

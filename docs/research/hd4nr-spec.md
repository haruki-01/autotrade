# H-D4-NR 研究ループ仕様

H-D4（％水準群集損切）の 30 サイクル research loop。

## 仮説

- **break**: スイング高値から −1.5% 等の深い水準タッチ → ショート（貫通継続）
- **bounce**: −1.0% 等の浅い水準タッチ → ロング（群集損切反発）

Phase0（B06）: P0-HD4-BREAK weak+（hit 54.7%）、P0-HD4-BOUNCE weak

## 実行

```bash
python3 -m scripts.research.hd4_loop
```

## サイクル構成

| Phase | Cycles | 内容 |
|---|---|---|
| 1 | 1–10 | mode/pct/cooldown/swing/entry/exit/N |
| 2 | 11–25 | 全局 best 周辺 adaptive 微調整 |
| 3 | 26–30 | top3 収束 validation |

## 出力

- `data/research/hd4_loop/iter_XX.json`
- `data/research/hd4_loop/hd4_loop_summary.json`
- `docs/research/hd4-research-report.md`

改訂: 2026-09-06

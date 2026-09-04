# L1 仮説探索（Phase2）

H-D 単体で Gate2 未到達のため、新 L1 仮説を Phase1 同等の執行込み検証で評価する。

| batch | 仮説 | 問い |
|---|---|---|
| **P2-A** | H-B EARLY | 点火3本目 + H-M5 + H-M4 で Gate1/2 pass か？ |
| **P2-B** | H-B PULL | 初押し（20–40%戻し）執行は EARLY より優位か？ |
| **P2-C** | H-B + H-D | 合成で Gate2 到達可能か？ |
| **P2-D** | H-B × セッション | EU_US / TOKYO 限定で edge 増幅するか？ |

```bash
python3 -m scripts.phase1.run_l1_batch ALL
```

改訂: 2026-09-04（pullback フィルタ修正・再実行結果反映）

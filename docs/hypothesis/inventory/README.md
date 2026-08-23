# 仮説インベントリ

フロー: [../FLOW.md](../FLOW.md) · 作成: [../craft/CREATION_FLOW.md](../craft/CREATION_FLOW.md) · ストック技法: [../craft/HYPOTHESIS_STOCK_METHODS.md](../craft/HYPOTHESIS_STOCK_METHODS.md)

| ID | タイトル | 歪み | status | 生成法 | メモ |
|----|----------|------|--------|--------|------|
| [HYP-009](./HYP-009-d001-fake-then-rebreak.md) | D-001 本突破初日 | E1/E6/E8 | fail | 深い複合 | Set B n=1 |
| [HYP-010](./HYP-010-d001-fake-then-retest.md) | D-001 再テスト | E1/E6/E8 | fail | 深い複合 | Set B n=1 |
| [HYP-011](./HYP-011-r001-near-high-expanded.md) | R-001 高値×拡大 | E1/E6 | fail | データ逆算 | Set B n=2 EV- |
| [HYP-003](./HYP-003-e8-do-not-trade.md) | E8 撃たない | E8 | draft | A+B | 証拠最優先 |
| [HYP-004](./HYP-004-e1-weekly-momentum.md) | E1 週次モメンタム | E1 | draft | D+E | 002と別翻訳 |
| [HYP-005](./HYP-005-e6-vol-sizing.md) | E6 ボラサイズ | E6 | draft | A+G | 生存仮説 |
| [HYP-006](./HYP-006-e4-session-gate.md) | E4 セッション | E4 | draft | A+L | 執行ゲート |
| [HYP-007](./HYP-007-e2-liq-follow.md) | E2 清算追随 | E2 | blocked | H | データ待ち |
| [HYP-008](./HYP-008-e1-breakout-fade-adversary.md) | E1 対立・回帰 | E1 | draft | J | 証拠で棄却予定可 |
| [HYP-002](./HYP-002-e1-breakout-long-v2.md) | E1 Long v2 | E1 | fail* | — | 検証済 |
| [HYP-001](./HYP-001-e1-breakout.md) | E1 母体 | E1 | archived | — | |
| — | H01/L-COST/L-MOM-VOL | — | archived | — | 再探索禁止 |

\* formal: EV+/DD良・n不足。

## 次に検証する10本（価格外データ）

価格のみの族（ダブルボトム51本・4H系41本）は全滅したため、次は建玉・資金調達・現物先物のズレを使う。  
正本: [../EDGE_HYPOTHESES.md](../EDGE_HYPOTHESES.md) / [../edge_hypotheses.yaml](../edge_hypotheses.yaml)

## 作成の次

優先議論: ゲート n=100 を運用に合わせるか / 有望4H系の**15m執行化**（新カード）。  
10サイクル結果: [../../eval/reports/20260822-hypothesis-10-cycles-FINAL.md](../../eval/reports/20260822-hypothesis-10-cycles-FINAL.md)  
HYP-009〜011 およびサイクル内ロジックの同値再チューニングは禁止。

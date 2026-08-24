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

## 低速側（SH-01）— コストから逆算した設計

| ID | status | 一言 |
|----|--------|------|
| SH-01 日足規模のトレンド継続 | **3期間PASS・近傍も面（採用は保留）** | プロジェクト初。EVの桁が変わった |
| SH-01N 近傍14本 | **A13/B13/C12 通過・42通り全てEV+** | 点ではなく面だった |
| SH-01 宣言外4銘柄 | **Set C で消える** | 銘柄依存。バスケット外に広げない |

`sh01_tp_4atr`: EV +0.706 / +0.619 / +0.671、DD 13〜17%、n=126/132/194（6銘柄合計）。
買い持ちが −33.1% だった Set C で +43.4%（DD 17.0% 対 64.2%）。
1日遅らせても3期間プラス。1e-6 の価格擾乱でもトレード数は不変＝きわどい同値判定に乗っていない。

**保留の理由:** 宣言外バスケット（LTC/DOT/AVAX/LINK）では Set C の EV が −0.090。
崩れるのはロング側だけで、その期間の買い持ちは −64.2%＝走る銘柄が無かった。
「主要銘柄なら効く」は事前に予測していない後付けの説明なので、一般化しない。

**次の判断（春希さん待ち）:** A=宣言6銘柄限定で紙トレードへ / B=銘柄選択フィルタを
別バスケット宣言のうえで検証 / C=打ち止め。推奨は A。

> **再現性:** 2026-08-23 以前の数値は再現しません（VM 再構築で23本中11本が変化）。
> 正は 08-24 の再実行。`requirements.lock.txt` で環境を固定済み。

正本: [../SLOW_HYPOTHESES.md](../SLOW_HYPOTHESES.md) ·
postmortem: [SH-01](../postmortems/2026-08-23-slow-sh01.md) ·
[宣言外追試と再現性](../postmortems/2026-08-24-slow-oos-and-reproducibility.md) ·
[コスト測定](../../../eval/reports/20260823-cost-horizon.md)

## 価格外データの10仮説（EH-01〜EH-10）— 一巡完了

| ID | status | 一言 |
|----|--------|------|
| EH-06 個人vs上位の乖離 | **機構あり（3期間）** | 向きは本物。水準がコストに届かず単独では不可 → 拒否フィルタへ |
| EH-01 建玉裏付けの突破 | **機構あり** | 退出の改良は打ち止め。次は入口条件 |
| EH-07 清算洗浄後の戻り | **希少エッジ** | 両期間プラスだが年60〜80回でゲート未達 |
| EH-10 funding リセット | 検証不能 | n=7/0。ショート側は成立せず |
| EH-09 成行買いの吸収 | **棄却** | Set A(2023) で符号が反転。2024年限定 |
| EH-02 現物先行 | **棄却** | n を増やして測り直したら消えた |
| EH-03 / EH-04 / EH-05 / EH-08 | **棄却** | 再探索禁止 |

100サイクル: Set B 11/100 → Set C 2/11。改良63本: EH-01R 3→0、EH-07R 0、EH-02R 0。
EH-06R/09R 54本を3期間（A/B/C）で検証し、**3期間PASS 0本**。
**累計217本・採用なし。**

> **手数料バグ（修正済み）:** エントリー手数料が1トレードあたり損益から抜けており、
> 2026-08-23 以前の全評価で EV が約 +0.05 USDT 過大でした。不合格の結論は不変ですが、
> ゼロ近辺のプラスは実際にはマイナスです。

**コストの床:** 1トレード往復 0.135 USDT ＝ 元本の 0.150% ＝ 許容損失の 4.5%。
測ってきたエッジ（0.05〜0.25 USDT）と同じオーダーで、これが最大の制約です。

正本: [../EDGE_HYPOTHESES.md](../EDGE_HYPOTHESES.md) / [../edge_hypotheses.yaml](../edge_hypotheses.yaml)  
postmortem: [100サイクル](../postmortems/2026-08-23-edge-100-cycles.md) · [改良3フェーズ](../postmortems/2026-08-23-edge-refine-cycles.md) · [EH-06R/09Rと手数料バグ](../postmortems/2026-08-23-edge-06-09-and-fee-bug.md)

## 作成の次

優先議論: ゲート n=100 を運用に合わせるか / 有望4H系の**15m執行化**（新カード）。  
10サイクル結果: [../../eval/reports/20260822-hypothesis-10-cycles-FINAL.md](../../eval/reports/20260822-hypothesis-10-cycles-FINAL.md)  
HYP-009〜011 およびサイクル内ロジックの同値再チューニングは禁止。

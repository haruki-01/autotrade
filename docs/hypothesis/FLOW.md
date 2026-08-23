# フロー索引

**正の理解（春希さん）:**

```text
① トレードスポット仮説（場面・形）
② 実装ロジック（実証①②… インジ等）
③ 検証（正しさ・費用後EV）
```

詳細: [craft/THREE_LAYER_MODEL.md](./craft/THREE_LAYER_MODEL.md)

| 層 | 何をするか | 文書 / 置き場 |
|----|------------|----------------|
| **① スポット** | 勝てる場面の仮説を書く | [craft/TRADE_SPOT_HYPOTHESIS.md](./craft/TRADE_SPOT_HYPOTHESIS.md) · [spots/](./spots/) |
| **② ロジック** | 同じスポットの測り方を複数書く | [inventory/](./inventory/) · [craft/CREATION_FLOW.md](./craft/CREATION_FLOW.md) |
| **③ 検証** | ロジック単位で formal eval | [craft/VALIDATION_FLOW.md](./craft/VALIDATION_FLOW.md) · `eval/` |
| 規律 | 再現性・多重検定などの衛生 | [craft/RESEARCH_HYGIENE.md](./craft/RESEARCH_HYGIENE.md) |

### ①の作り方（2系統・別ファイル）

| 系統 | 何をするか | 文書 |
|------|------------|------|
| **A. 演繹（深い複合）** | 見落とし＋複合条件＋攻め方で①を書く | [craft/DEEP_COMPOSITE_SPOTS.md](./craft/DEEP_COMPOSITE_SPOTS.md)（地図は [spots/CATALOG.md](./spots/CATALOG.md)） |
| **B. 帰納（データ逆算）** | 過去の伸びた局面から条件を逆算し①にする | [craft/REVERSE_DISCOVERY.md](./craft/REVERSE_DISCOVERY.md) · [spots/DISCOVERED_FROM_DATA.md](./spots/DISCOVERED_FROM_DATA.md) |

```text
系統A or B で①を増やす（深いもの優先）
   ↓
各①に実証ロジック②を2案
   ↓ ready な②だけ
formal eval ③（逆算の Discovery 期間では合否を出さない）
```

**注意:** 研究衛生だけでは①は生まれない。浅い定番カタログだけでも弱い。深い複合か、データ逆算のどちらかで厚みを出す。

### ゲート注記（春希さん向け）

- `min_trades=100` は **Set B（通常1年）の合計トレード数**。1ヶ月あたり100ではない。
- 足を短くして回数を増やすのはあり。ただし **1分未満の足は使わない**。

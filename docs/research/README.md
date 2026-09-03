# リサーチ成果物（仕様書とは分離）

このディレクトリは **仮説カタログ・検証シート・ナレッジ** を置く場所です。

| 文書 | 役割 | 更新方針 |
|---|---|---|
| [`../SPEC.md`](../SPEC.md) | プロジェクト正本（資金・目標・変数構造・検証ルール） | **安易に追記しない。状態を維持** |
| [`edge-catalog.md`](edge-catalog.md) | エッジ仮説の網羅カタログ | 仮説の追加・棄却・Phase移動で更新 |
| [`phase0-stats.md`](phase0-stats.md) | Phase0 記述統計の定義書 | 統計項目の定義変更時のみ更新 |
| [`phase0-verification-sheet.csv`](phase0-verification-sheet.csv) | Phase0 検証用シート（記入用） | 計測結果・判定を記入 |
| [`phase0-verification-sheet.md`](phase0-verification-sheet.md) | 同上の閲覧用テーブル | CSV と同期 |

## Phase の意味

| Phase | 内容 |
|---|---|
| **0** | トレードしない。イベント後リターン等の記述統計だけで歪みの有無を見る |
| 1 | OHLCV でロジック化。理論値／執行込みの二列で P を採点 |
| 2 | 板・USDT先行・清算・指標カレンダーなど追加データが必要 |

資金・N・執行仮置きなどの定数は SPEC を参照し、ここでは繰り返して固定値を増やしすぎない。

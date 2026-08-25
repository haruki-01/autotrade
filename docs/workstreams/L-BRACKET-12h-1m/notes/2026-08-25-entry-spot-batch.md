# 入口スポット一括起票（2026-08-25）

案2（15分陽線・EMA押し目・直前15分高値）は Set Y で棄却。  
枠と「上位足で場面、1分は瞬間」は維持したまま、**別の場面**を8本起票した。検証③はしていない。

比較の軸: 案2で死んだ定義を使っていないか、目で説明できるか、無効化があるか。

| ID | 場面（上位足） | 1分の瞬間 | 案2との差 |
|---|---|---|---|
| [BR-001](../../../hypothesis/spots/SPOT-BR-001-htf-swing-1m-break.md) | 1時間の HH/HL | スイング高値更新 | 1本の陽線ではなくスイング |
| [BR-002](../../../hypothesis/spots/SPOT-BR-002-asia-box-active-break.md) | アジアの箱 | 厚い時間に箱抜け | 時間帯構造。ローソク色ではない |
| [BR-003](../../../hypothesis/spots/SPOT-BR-003-flagpole-1m-break.md) | 15分の旗竿 | 旗面を竿方向へ抜け | 「いつもそこにあるEMA」ではない |
| [BR-004](../../../hypothesis/spots/SPOT-BR-004-15m-inside-1m-break.md) | 確定インサイド | 箱の片側抜け | 圧縮してから。毎15分ではない |
| [BR-005](../../../hypothesis/spots/SPOT-BR-005-htf-hold-1m-sweep-reclaim.md) | 1時間はHL維持 | 狩り→取り戻し→高値更新 | 最初の押しでは入らない |
| [BR-006](../../../hypothesis/spots/SPOT-BR-006-second-break-equal-highs.md) | 同じ高値で二度止め | 初回失敗後の二度目抜け | HTF-002の「毎回の高値更新」ではない |
| [BR-007](../../../hypothesis/spots/SPOT-BR-007-hour-opening-range-1m.md) | その時間の狭い始値箱 | 後半の片側抜け | セッション箱の毎時版。幅フィルタ必須 |
| [BR-008](../../../hypothesis/spots/SPOT-BR-008-impulse-half-retrace-1m.md) | 15分の急なレッグ | 半値で止まって再開 | 押しの質をレッグ半値で測る |

## まだやらないこと

- 8本を一度に実装して総当たりすること
- 決済EVが黒になる前に8年を回すこと
- 枠（12h / 1.00% / RR）を同時に変えること

## 次

春希さんが短リストを決める（例: 3本）。選ばれた①だけ②を実装し、直近1年で測る。

**追記:** この8本は優位軸で不採用。後継は [advantage-rescore](./2026-08-25-advantage-rescore.md)。

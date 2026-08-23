# DB-21 — 1H × 上昇 × 鮮度 × 高値奪還

| 項目 | 値 |
|------|-----|
| logic_id | `db_1h_up_fresh_reclaim_v1` |
| スポット | SPOT-001 |
| ステータス | ready → formal |
| 由来 | 20サイクルでEV+だった質ノブを1Hへ移植 |

## 変更点（親DB-10比）

1. 日足上昇構造のみ  
2. 突破後48h以内の再テスト  
3. 反発確定 = 突破時高値の奪還  

（DB-20比: 反発を高%戻し→高値奪還、鮮度を追加）

## 棄却

- Set B: EV≤0 or DD>20% or n<100  
- Set C: EV符号崩壊  

## 最新

- [LATEST.md](./LATEST.md)（eval後）

---
id: DB-10
title: "ダブルボトム 1H構造（SPOT-001）"
status: holdout_fail
primary_distortion: E1
created: 2026-08-23
updated: 2026-08-23
spot: SPOT-001
---

# ダブルボトム 1H構造

## 主張

ダブルボトム→ネック突破→ネック反発を **1H構造**で測ると、年次サンプルは足りるが、費用後エッジは薄い／直近で消える。

## 結果

| Set | Gate | EV | DD | n |
|-----|------|----|----|---|
| B | PASS | +0.004 | 6.0% | 109 |
| C | FAIL | -0.101 | 11.1% | 209 |

## 学び

- 構造足を短くすると n は増えるが、仮説の「厚い反発」は薄まる
- Set B のギリギリPASSは採用根拠にしない（holdout必須）

logic_id: `db_struct_1h_v1`

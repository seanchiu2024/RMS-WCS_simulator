讀取 equip_handshaking_function_v1.2.md
讀取 wcs_simulator.md

sourcepoint 來自 caller 的 sourcecode
sourcepoint_W 使用 sourcepoint 到 HS_lookup_table 查詢
targetpoint 來自 caller 的 targetcode
targetpoint_W 使用 targetpoint 到 HS_lookup_table 查詢

HS_lookup_table 範例如下:
| point_id | wait_point | machine_type | need_hs |
|----------|------------|--------------|---------|
| R01_P01 | R01WP01 | Station | yes |
| WRP_501 | WRPW501 | Wrap | yes |

WCS 送出的 mission 範例如下:

```json
{
  "sequence": "HS_HS_M001", //唯一
  "timestamp": "2026-07-10 09:00:01.0000",
  "priority": "128",
  "sub_missions": [
    { "space": "sourcepoint_W", "action": "start" }, //直接回覆Ack
    { "space": "sourcepoint_W", "action": "idle" }, //交握後，再回覆Ack  申請進入
    { "space": "sourcepoint", "action": "load" }, //直接回覆Ack
    { "space": "sourcepoint_W", "action": "idle" }, //直接回覆Ack    交接給設備及等待結果
    { "space": "targetpoint_W", "action": "idle" }, //交握後，再回覆Ack 申請進入
    { "space": "targetpoint", "action": "unload" }, //直接回覆Ack
    { "space": "targetpoint_W", "action": "idle" }, //交握後，再回覆Ack 交接給設備及等待結果
    { "space": "targetpoint", "action": "end" } //直接回覆Ack
  ]
}
```

sub_missions 中 action 有 start, idle, load, unload, end 等相關動作

當收到 RMS 針對 各 action 回覆 result 為 ok 時，WCS 端回復 ack 的動作如下:

當 action 為idle時，代表需進行設備交握後 才回復 ack OK
若 action 為 第1個 idle 時，
call 申請進入 (POST /api/request-enter)。進行設備交握，當收到交握結果為 OK 時，send ack OK 回復Ack
若 action 為 第2個 idle 時，
call prepareation_complete (POST /api/preparation-complete) 通知設備可以動作，
並接續 call result_query_takeover (POST /api/result-query-takeover) 等待設備完工後 執行結果(或通知完成)。釋放資源並於完成後 send ack OK 回復Ack
若 action 為 第3個 idle 時，
call 申請進入 (POST / api/request-enter)。進行設備交握，當收到交握結果為 OK 時，send ack OK 回復Ack
若 action 為 第4 個 idle 時，
call prepareation_complete (POST /api/preparation-complete) 通知設備可以動作，
並接續 call result_query_takeover (POST /api/result-query-takeover) 等待設備完工後 執行結果(或通知完成)。釋放資源並於完成後 send ack OK 回復Ack

其餘 action 都先直接 回復 ack ok

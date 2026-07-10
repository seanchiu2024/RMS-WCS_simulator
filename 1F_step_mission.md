## 入庫流程

### DOCK_ALN

說明: 收到 3.6 入庫指令後執行 DOCK [>TMP]> ALN
      TMP 到位完成，WES 自主啟動 TMP > ALN, <mark>啟動及具體作法待討論</mark>

Action_Type: DOCK_ALN
source point : Dock or Temp Point
target point: ALN machine

step_type: <mark>ALN_IN</mark>

source point : Dock or Temp Point
relay point: ALN Wait Point
target point: ALN machine

```json
{
  "sequence": "M10000001",
  "timestamp": "2026-07-07 09:00:01.0000",
  "priority": "128",
  "sub_missions": [
    { "space": "Dock", "action": "start" },
    { "space": "Dock", "action": "load" },
    { "space": "ALN-W", "action": "idle" }, // send ack ok when grant the permission
    { "space": "ALN", "action": "unload" },
    { "space": "ALN-W", "action": "idle" }, // inform to ALN machine and Wait for result and reply to WES
    { "space": "ALN-W", "action": "end" }
  ]
}
```

### DOCK_TMP

說明: 收到 3.6 入庫指令後執行 DOCK > TMP, TMP 到位完成，自主啟動 TMP > ALN, 啟動及具體作法待討論

Action_Type: DOCK_TMP
source point : Dock Point
target point: TEMP Point

step_type: MOVE

source point : Dock Point
target point: TEMP Point

```json
{
  "sequence": "M10000001",
  "timestamp": "2026-07-07 09:00:01.0000",
  "priority": "128",
  "sub_missions": [
    { "space": "Dock", "action": "start" },
    { "space": "Dock", "action": "load" },
    { "space": "TEMP", "action": "unload" },
    { "space": "TEMP", "action": "end" }
  ]
}
```

### ALN_ASRS_IPORT

說明: 經由 DOCK_ALN 的 result，3.8A 入庫申請，3.9 入庫回覆。得到 TargetPoint。

#### 正常入庫

Action_Type: ALN_IPORT
source point : ALN Point
target point: IPORT point



source point : ALN Point
relay  point:  HandOver

target point: IPOprt

[step １] Move to HandOver

step_type: <mark>ALN_OUT</mark>

source point : ALN Point
target point: HandOver

```json
{
  "sequence": "M10000002",
  "timestamp": "2026-07-07 09:00:01.0000",
  "priority": "128",
  "sub_missions": [
    { "space": "ALN", "action": "start" },  // 申請進入設備 取貨 OK 後回 Ack 
    { "space": "ALN", "action": "load" },  
    { "space": "HandOver", "action": "unload" }, // 釋放 ALN 資源
    { "space": "HandOver", "action": "end" }
  ]
}
```

[step 2] Move >  IPort > HandOver

step_type: <mark>ASRS_IPORT</mark>

source point : HandOver Point

relay Point: IPOrt
target point: HandOver

```json
{
  "sequence": "M10000003",
  "timestamp": "2026-07-07 09:00:01.0000",
  "priority": "128",
  "sub_missions": [
    { "space": "HandOver", "action": "start" },
    { "space": "HandOver", "action": "load" },
    { "space": "IPort-W", "action": "idle" }, // Grant permission for put goods to enter
    { "space": "IPort", "action": "unload" },
    { "space": "IPort-W", "action": "idle" }, // HandOver to ASRS crane Wait for the result from crane , Grant permission to grab rack
    { "space": "IPort", "action": "load" }, 
    { "space": "HandOver", "action": "unload" }, // release IPORT resource,
    { "space": "HandOver", "action": "end" }
  ]
}
```




#### 異常流程

Action_Type: ALN_ABN
source pont: ALN machine
target point: abnormal point



step_type<mark>: ALN_OUT</mark>

source point : ALN machine
target point: abnormal point

```json
{
  "sequence": "M10000004",
  "timestamp": "2026-07-07 09:00:01.0000",
  "priority": "128",
  "sub_missions": [
    { "space": "ALN", "action": "start" },  // 申請進入設備 取貨 OK 後回 Ack 
    { "space": "ALN", "action": "load" }, 
    { "space": "abnormal", "action": "unload" }, // 釋放 ALN 資源
    { "space": "abnormal", "action": "end" }
  ]
}
```



#### 等待人工調整後，call API inform WES continue

WES 下指令

說明: 收到 3.6 入庫指令後執行 DOCK [>TMP] > ALN
      TMP 到位完成，自主啟動 TMP > ALN, 啟動及具體作法待討論
Action_Type: <mark>ALN_IN</mark>
source point : Abnormal Point
reply point: ALN Wait Point
target point: ALN machine



step_type: <mark>ALN_IN</mark>

source point : Dock or Temp Point
relay point: ALN Wait Point
target point: ALN machine



```json
{
  "sequence": "M10000001",
  "timestamp": "2026-07-07 09:00:01.0000",
  "priority": "128",
  "sub_missions": [
    { "space": "abnormal", "action": "start" },
    { "space": "abnormal", "action": "load" },
    { "space": "ALN-W", "action": "idle" }, // ack ok when grant the permission
    { "space": "ALN", "action": "unload" },
    { "space": "ALN-W", "action": "idle" }, // inform to ALN machine and Wait for result and reply to WES
    { "space": "ALN-W", "action": "end" }
  ]
}
```

 



## 岀庫流程

### ASRS_TMP

### TMP_DOCK

### 可用 RMS_ID Point

// RMS_ID for test as followings:

```json
{
  "sequence": "M10000001",
  "timestamp": "2026-07-07 09:00:01.0000",
  "priority": "128",
  "sub_missions": [
    { "space": "Repeat-A-0", "action": "start" },
    { "space": "Repeat-A-0", "action": "load" },
    { "space": "Repeat-B-0", "action": "idle" },
    { "space": "GD-01-0", "action": "unload" },
    { "space": "Repeat-B-0", "action": "idle" },
    { "space": "GD-01-0", "action": "load" },
    { "space": "Repeat-C-0", "action": "unload" },
    { "space": "L-01-0", "action": "idle" },
    { "space": "L-01-0", "action": "end" }
  ]
}
```

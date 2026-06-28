# WCS - RMS 搬運控制與目的地變更流程設計 (L-01-0 到 Repeat-C-0)

本設計文件根據 `00-2025-08-09_WCS-RMS 協議_登彥科技機密_V09_TBD.pdf` 的三階段回應原則（Request - Result - Ack），規劃 AMR 從 **A-01-2** 搬運貨物時，在取貨完成後由 WCS 下達 `replace` 控制指令變更卸貨終點為 **Repeat-C-0** 的完整 API 交互步驟與對應的 JSON Payload。

---

## 搬運任務規劃說明

- **原始任務動作序列：**
  1. `Repeat-A-0`：`start` (任務開始)
  2. `Repeat-A-0`：`load` (執行取貨，取走指定的棧板)
  3. `L-01-0`：`unload` (執行放貨) -> **任務執行中將被變更為 `Repeat-C-0`**
  4. `L-01-0`：`end` (任務結束) -> **任務執行中將被變更為 `Repeat-C-0`**
- **車輛名稱：** `AMR01`
- **指令序號：** `M1000001`
- **控制指令序號：** `M222`
- **棧板 ID：** `01`

---

## 完整 API 交互流程

### 步驟 1: WCS 下達搬運任務請求 (Request)

* **方向：** WCS $\rightarrow$ RMS
* **API Endpoint：** `POST http://<RMS_IP>:31111/awd/rms/set_mission_request`
* **說明：** WCS 發派任務路徑規劃。

POST "http://<RMS_IP>:31111/awd/rms/set_mission_request"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:40:00.000",
  "priority": "128",
  "sub_missions": [
  { "space": "Repeat-A-0", "action": "start"},
    { "space": "Repeat-A-0", "action": "load"},   
    {
      "space": "L-01-0",
      "action": "unload"
    },
    {
      "space": "L-01-0",
      "action": "end"
    }
  ]
}
```

### 步驟 2: RMS 立即回應任務發派結果 (Reply)

* **方向：** RMS $\rightarrow$ WCS (同步 HTTP 200 OK 回應)
* **說明：** RMS 檢查 JSON 格式及邏輯正確後，回傳確認。

HTTP/1.1 200 OK

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:40:01.000",
  "priority": "128",
  "reply": "ACK",
  "sub_missions": [],
  "reason": "NA"
}
```

---

### 步驟 3: RMS 回報開始執行任務 (Result - start)

* **方向：** RMS $\rightarrow$ WCS
* **API Endpoint：** `POST http://<WCS_IP>:31112/awd/rms/set_mission_result`
* **說明：** AMR01 抵達 `A-01-2` 並回報開始執行任務。

POST "http://<WCS_IP>:31112/awd/rms/set_mission_result"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:41:00.000",
  "priority": "128",
  "space": "Repeat-A-0",
  "action": "start",
  "result": "OK",
  "reason": "NA"
}
```

### 步驟 4: WCS 確認收到開始訊號 (Ack - start)

* **方向：** WCS $\rightarrow$ RMS
* **API Endpoint：** `POST http://<RMS_IP>:31111/awd/rms/set_mission_ack`
* **說明：** WCS 回應確認，允許車輛繼續執行取貨動作。

POST "http://<RMS_IP>:31111/awd/rms/set_mission_ack"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:41:02.000",
  "priority": "128",
  "action": "start",
  "ack": "OK"
}
```

---

### 步驟 5: RMS 回報取貨完成 (Result - load)

* **方向：** RMS $\rightarrow$ WCS
* **API Endpoint：** `POST http://<WCS_IP>:31112/awd/rms/set_mission_result`
* **說明：** AMR01 在 `A-01-2` 載入棧板 `01` 完成，回報取貨成功。

POST "http://<WCS_IP>:31112/awd/rms/set_mission_result"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:42:00.000",
  "priority": "128",
  "space": "Repeat-A-0",
  "action": "load",
  "result": "OK",
  "reason": "01"
}
```

### 

### 步驟 R1: WCS 下達任務狀態變更請求 (Status Request - replace)

* **方向：** WCS $\rightarrow$ RMS
* **API Endpoint：** `POST http://<RMS_IP>:31111/awd/rms/set_mission_status_request`
* **說明：** WCS 因調度需求，下達狀態變更指令為 `replace`。

POST "http://<RMS_IP>:31111/awd/rms/set_mission_status_request"

```json
{
  "protocol_version": "2.0",
  "sequence": "M222",
  "timestamp": "2026-06-17 21:42:05.000",
  "priority": "128",
  "mission_sequence": "M1000001",
  "command": "replace"
}
```

### 步驟 R2: RMS 立即回應狀態變更請求接收結果 (Status Reply)

* **方向：** RMS $\rightarrow$ WCS (同步 HTTP 200 OK 回應)
* **說明：** RMS 檢查任務控制格式及邏輯正確後，回傳確認。

HTTP/1.1 200 OK

```json
{
  "protocol_version": "2.0",
  "sequence": "M222",
  "timestamp": "2026-06-17 21:42:06.000",
  "priority": "128",
  "reply": "ACK",
  "mission_sequence": "M1000001",
  "reason": "NA"
}
```

---

### 步驟 R3: RMS 回報任務狀態變更完成 (Status Result)

* **方向：** RMS $\rightarrow$ WCS
* **API Endpoint：** `POST http://<WCS_IP>:31112/awd/rms/set_mission_status_result`
* **說明：** RMS 已成功收到 Replace command。

POST "http://<WCS_IP>:31112/awd/rms/set_mission_status_result"

```json
{
  "protocol_version": "2.0",
  "sequence": "M222",
  "timestamp": "2026-06-17 21:42:10.000",
  "priority": "128",
  "mission_sequence": "M1000001",
  "command": "replace",
  "result": "OK",
  "reason": "NA"
}
```

### 步驟 R4: WCS 確認收到狀態變更完成訊號 (Status Ack)

* **方向：** WCS $\rightarrow$ RMS
* **API Endpoint：** `POST http://<RMS_IP>:31111/awd/rms/set_mission_status_ack`
* **說明：** WCS 回應確認收到變更結果，車輛隨後按新路徑執行搬運。

POST "http://<RMS_IP>:31111/awd/rms/set_mission_status_ack"

```json
{
  "protocol_version": "2.0",
  "sequence": "M222",
  "timestamp": "2026-06-17 21:42:12.000",
  "priority": "128",
  "ack": "OK"
}
```

## **原已執行任務 轉成 idle, cancel by user.**

### 步驟 R5: WCS 下達<mark>新後續任務請求 (Request)</mark>

- **方向：** WCS $\rightarrow$ RMS
- **API Endpoint：** `POST http://<RMS_IP>:31111/awd/rms/set_mission_request`
- **說明：** WCS 發派任務路徑規劃。

POST "http://<RMS_IP>:31111/awd/rms/set_mission_request"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:40:00.000",
  "priority": "128",
  "sub_missions": [
    {
      "space": "Repeat-C-0",
      "action": "unload"
    },
    {
      "space": "Repeat-C-0",
      "action": "end"
    }
  ]
}
```

### 步驟 R6: RMS 立即回應任務發派結果 (Reply)

- **方向：** RMS $\rightarrow$ WCS (同步 HTTP 200 OK 回應)
- **說明：** RMS 檢查 JSON 格式及邏輯正確後，回傳確認。

HTTP/1.1 200 OK

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:40:01.000",
  "priority": "128",
  "reply": "ACK",
  "sub_missions": [],
  "reason": "NA"
}
```

---

### 步驟 N1 : WCS 改派 ack <mark>start</mark> 啟動新流程

- **方向：** WCS $\rightarrow$ RMS
- **API Endpoint：** `POST http://<RMS_IP>:31111/awd/rms/set_mission_ack`
- **說明：** WCS 回應確認，指示車輛載貨駛向終點。

POST "http://<RMS_IP>:31111/awd/rms/set_mission_ack"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:42:02.000",
  "priority": "128",
  "action": "start",
  "ack": "OK"
}
```

--- 



### 步驟 N2: RMS 回報放貨完成 (Result - unload)

* **方向：** RMS $\rightarrow$ WCS
* **API Endpoint：** `POST http://<WCS_IP>:31112/awd/rms/set_mission_result`
* **說明：** AMR01 抵達新的目的地 `repeat-A-0` 並完成卸貨，回報放貨成功。

POST "http://<WCS_IP>:31112/awd/rms/set_mission_result"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:44:00.000",
  "priority": "128",
  "space": "Repeat-C-0",
  "action": "unload",
  "result": "OK",
  "reason": "NA"
}
```

### 步驟 N3: WCS 確認卸貨完成 (Ack - unload)

* **方向：** WCS $\rightarrow$ RMS
* **API Endpoint：** `POST http://<RMS_IP>:31111/awd/rms/set_mission_ack`
* **說明：** WCS 回應確認，允許車輛執行收尾結束。

POST "http://<RMS_IP>:31111/awd/rms/set_mission_ack"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:44:02.000",
  "priority": "128",
  "action": "unload",
  "ack": "OK"
}
```

---

### 步驟 N4: RMS 回報任務結束 (Result - end)

* **方向：** RMS $\rightarrow$ WCS
* **API Endpoint：** `POST http://<WCS_IP>:31112/awd/rms/set_mission_result`
* **說明：** AMR01 在 `repeat-A-0` 完成所有路徑與動作，回報整體任務結束。

POST "http://<WCS_IP>:31112/awd/rms/set_mission_result"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:45:00.000",
  "priority": "128",
  "space": "Repeat-C-0",
  "action": "end",
  "result": "OK",
  "reason": "NA"
}
```

### 步驟 N5: WCS 發送最終確認以關閉任務 (Ack - end)

* **方向：** WCS $\rightarrow$ RMS
* **API Endpoint：** `POST http://<RMS_IP>:31111/awd/rms/set_mission_ack`
* **說明：** WCS 回傳最終 ACK，此 `M1000001` 任務在兩端皆宣告結案 (closed)。

POST "http://<RMS_IP>:31111/awd/rms/set_mission_ack"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:45:02.000",
  "priority": "128",
  "action": "end",
  "ack": "OK"
}
```

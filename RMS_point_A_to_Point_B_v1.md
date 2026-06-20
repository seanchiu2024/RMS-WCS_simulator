# WCS - RMS 搬運控制流程設計 (A-01-2 到 L-01-0)

本設計文件根據 `00-2025-08-09_WCS-RMS 協議_登彥科技機密_V09_TBD.pdf` 的三階段回應原則（Request - Result - Ack），規劃 AMR 從 **A-01-2** 搬運貨物至 **L-01-0** 的完整 API 交互步驟與對應的 JSON Payload。

---

## 搬運任務規劃說明

- **任務動作序列：**
  1. `A-01-2`：`start` (任務開始)
  2. `A-01-2`：`load` (執行取貨，取走指定的棧板)
  3. `L-01-0`：`unload` (執行放貨)
  4. `L-01-0`：`end` (任務結束)
- **車輛名稱：** `AMR01`
- **指令序號：** `M1000001`
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
    {
      "space": "A-01-2",
      "action": "start"
    },
    {
      "space": "A-01-2",
      "action": "load"
    },
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
  "space": "A-01-2",
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
  "space": "A-01-2",
  "action": "load",
  "result": "OK",
  "reason": "01"
}
```

### 步驟 6: WCS 確認取貨並指示前往終點 (Ack - load)

* **方向：** WCS $\rightarrow$ RMS
* **API Endpoint：** `POST http://<RMS_IP>:31111/awd/rms/set_mission_ack`
* **說明：** WCS 回應確認，指示車輛載貨駛向終點 `L-01-0`。

POST "http://<RMS_IP>:31111/awd/rms/set_mission_ack"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:42:02.000",
  "priority": "128",
  "action": "load",
  "ack": "OK"
}
```

---

### 步驟 7: RMS 回報放貨完成 (Result - unload)

* **方向：** RMS $\rightarrow$ WCS
* **API Endpoint：** `POST http://<WCS_IP>:31112/awd/rms/set_mission_result`
* **說明：** AMR01 抵達 `L-01-0` 並完成卸貨，回報放貨成功.

POST "http://<WCS_IP>:31112/awd/rms/set_mission_result"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:44:00.000",
  "priority": "128",
  "space": "L-01-0",
  "action": "unload",
  "result": "OK",
  "reason": "NA"
}
```

### 步驟 8: WCS 確認卸貨完成 (Ack - unload)

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

### 步驟 9: RMS 回報任務結束 (Result - end)

* **方向：** RMS $\rightarrow$ WCS
* **API Endpoint：** `POST http://<WCS_IP>:31112/awd/rms/set_mission_result`
* **說明：** AMR01 完成所有路徑與動作，回報整體任務結束。

POST "http://<WCS_IP>:31112/awd/rms/set_mission_result"

```json
{
  "protocol_version": "2.0",
  "sequence": "M1000001",
  "timestamp": "2026-06-17 21:45:00.000",
  "priority": "128",
  "space": "L-01-0",
  "action": "end",
  "result": "OK",
  "reason": "NA"
}
```

### 步驟 10: WCS 發送最終確認以關閉任務 (Ack - end)

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

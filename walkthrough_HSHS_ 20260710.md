# WCS 設備交握 Web API 整合與驗證紀錄

本文件記錄了將 WCS 模擬器中原本的 `idle` 動作處理改為呼叫對應 EAP RESTful Web API，並實作特定步驟編號分支交握邏輯的修改與驗證結果。

## 修改內容

在 `[wcs_simulator.py](file:///c:/Sean_Documents/RMS+WCS_sim+Handshaking/wcs_simulator.py)` 中：
- 封裝了三個 EAP Web API 呼叫的 HTTP 請求方法（Port 8000），使用內建 `urllib`：
  - `call_request_enter` 呼叫 `POST /api/request-enter`
  - `call_preparation_complete` 呼叫 `POST /api/preparation-complete`
  - `call_result_query_takeover` 呼叫 `POST /api/result-query-takeover`
- 實作了 `idle_counters` 字典與 `get_idle_counter(seq)` 函式，用以追蹤與取得特定任務累積遭遇的 `idle` 步數。
- 在 `pending_acks` 主迴圈中，當 `action == "idle"` 時，使用硬寫死的條件分支（`if-elif` 結構）進行交握參數呼叫：
  - **`idle_count == 1`**：呼叫 `call_request_enter`（設備: `PalletSupply`、ID: `PalletSupply#1`）。
  - **`idle_count == 2`**：呼叫 `call_preparation_complete` 與 `call_result_query_takeover`（對應 `PalletSupply#1`）。
  - **`idle_count == 3`**：呼叫 `call_request_enter`（設備: `Station`、ID: `Robot_n`）。
  - **`idle_count == 4`**：呼叫 `call_preparation_complete` 與 `call_result_query_takeover`（對應 `Robot_n`）。
- 當任務為 `end` 動作時，自動清除 `idle_counters` 以釋放計數器資源。

---

## 整合測試與驗證

### 測試方式
1. 啟動 `[rms_simulator.py](file:///c:/Sean_Documents/RMS+WCS_sim+Handshaking/rms_simulator.py)` 與 `[wcs_simulator.py](file:///c:/Sean_Documents/RMS+WCS_sim+Handshaking/wcs_simulator.py)`。
2. 啟動 EAP Web 服務 `[app.py](file:///c:/Sean_Documents/RMS+WCS_sim+Handshaking/equip_handshaking/app.py)` (監聽 Port 8000)。
3. 使用 `test_mission_trigger.py` 腳本向 RMS 發送 `HS_HS.json` 搬運任務。
4. 觀察 WCS 與 EAP 日誌，確認 4 次 `idle` 交握皆是透過 HTTP 呼叫 Web API 執行，並在其完成後才回覆 ACK 給 RMS。

### 驗證日誌

#### 1. WCS 模擬器主日誌：
依據 `[wcs_simulator.py](file:///c:/Sean_Documents/RMS+WCS_sim+Handshaking/wcs_simulator.py)` 執行輸出：
* **步驟 1 (Repeat-A-0, idle - 第 1 個 idle)**：
  ```
  [設備交握] 偵測到 'idle' 動作 (第 1 個 idle)...
  [設備交握 #1] 向 PalletSupply 發送進入申請 (wes_id: PalletSupply#1)...
  [EAP Web API] 呼叫 request-enter (設備: PalletSupply, ID: PalletSupply#1, 模式: 1)...
  [EAP Web API] request-enter 回應: OK
  [發送確認] 發送 ACK (action='idle') 給 RMS...
  ```
* **步驟 2 (Repeat-B-0, load)**：直接回覆 ACK (非 idle 動作無須交握，正常推進)。
* **步驟 3 (Repeat-A-0, idle - 第 2 個 idle)**：
  ```
  [設備交握] 偵測到 'idle' 動作 (第 2 個 idle)...
  [設備交握 #2] 向 PalletSupply 發送準備完成通知，並等待完工 (wes_id: PalletSupply#1)...
  [EAP Web API] 呼叫 preparation-complete (設備: PalletSupply, ID: PalletSupply#1, 模式: 1)...
  [EAP Web API] preparation-complete 回應: OK
  [EAP Web API] 呼叫 result-query-takeover (設備: PalletSupply, ID: PalletSupply#1, 模式: 1)...
  [EAP Web API] result-query-takeover 回應: {'status': 'OK', 'palletNo': 'PLT_SUPPLY_BOTTOM_PalletSupply#1'}
  [發送確認] 發送 ACK (action='idle') 給 RMS...
  ```
* **步驟 4 (L-01-0, idle - 第 3 個 idle)**：
  ```
  [設備交握] 偵測到 'idle' 動作 (第 3 個 idle)...
  [設備交握 #3] 向 Station 發送進入申請 (wes_id: Robot_n)...
  [EAP Web API] 呼叫 request-enter (設備: Station, ID: Robot_n, 模式: 1)...
  [EAP Web API] request-enter 回應: OK
  [發送確認] 發送 ACK (action='idle') 給 RMS...
  ```
* **步驟 5 (Repeat-C-0, unload)**：直接回覆 ACK。
* **步驟 6 (L-01-0, idle - 第 4 個 idle)**：
  ```
  [設備交握] 偵測到 'idle' 動作 (第 4 個 idle)...
  [設備交握 #4] 向 Station 發送準備完成通知，並等待完工 (wes_id: Robot_n)...
  [EAP Web API] 呼叫 preparation-complete (設備: Station, ID: Robot_n, 模式: 1)...
  [EAP Web API] preparation-complete 回應: OK
  [EAP Web API] 呼叫 result-query-takeover (設備: Station, ID: Robot_n, 模式: 1)...
  [EAP Web API] result-query-takeover 回應: {'status': 'OK'}
  [發送確認] 發送 ACK (action='idle') 給 RMS...
  ```

#### 2. EAP Web 服務日誌 (`[app.py](file:///c:/Sean_Documents/RMS+WCS_sim+Handshaking/equip_handshaking/app.py)`)：
FastAPI 成功接獲全部 6 次交握 POST 請求，均返回 HTTP 200 OK：
```
INFO:     127.0.0.1:61567 - "POST /api/request-enter HTTP/1.1" 200 OK
INFO:     127.0.0.1:61600 - "POST /api/preparation-complete HTTP/1.1" 200 OK
INFO:     127.0.0.1:61604 - "POST /api/result-query-takeover HTTP/1.1" 200 OK
INFO:     127.0.0.1:61635 - "POST /api/request-enter HTTP/1.1" 200 OK
INFO:     127.0.0.1:61691 - "POST /api/preparation-complete HTTP/1.1" 200 OK
INFO:     127.0.0.1:61695 - "POST /api/result-query-takeover HTTP/1.1" 200 OK
```

驗證結果已成功通過，所有 `idle` 動作皆在背景透過 Web API 進行了正確的設備交握。

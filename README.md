# WCS - RMS 搬運控制模擬系統

本專案實作了一套 AMR 搬運任務控制流程模擬器，用以模擬 RMS (Robot Management System)、WCS (Warehouse Control System) 兩者之間的 API 互動，以及 EAP 實體設備訊號交握（Handshaking）。

系統遵循**「Request（請求） - Result（執行結果） - Ack（步驟確認）」**三階段互動原則，並整合了實體機台的 Web API 交握控制。

---

## 系統運作架構

本系統由三大核心模組構成，彼此之間透過 HTTP RESTful API 進行通訊：

```mermaid
graph TD
    WCS["WCS 模擬器 (wcs_simulator.py)<br>Port: 31112"]
    RMS["RMS 模擬器 (rms_simulator.py)<br>Port: 31111"]
    EAP["EAP Web 服務 (app.py)<br>Port: 8000"]

    WCS -->|1. set_mission_request| RMS
    RMS -->|2. set_mission_result| WCS
    WCS -->|3. EAP Handshake (POST)| EAP
    EAP -->|4. OK / WAIT / Result| WCS
    WCS -->|5. set_mission_ack| RMS
```

1. **RMS 模擬器 (`[rms_simulator.py](file:///c:/Sean_Documents/RMS+WCS_sim+Handshaking/rms_simulator.py)`)**：負責車隊狀態機、任務調配佇列、與模擬 AMR 車輛運行。
2. **WCS 模擬器 (`[wcs_simulator.py](file:///c:/Sean_Documents/RMS+WCS_sim+Handshaking/wcs_simulator.py)`)**：發送搬運工單，並監聽任務執行結果，若收到 `idle` 交握點時，主動發起 Web API 交握，解除後回覆 ACK 推進狀態。
3. **EAP Web 服務 (`[equip_handshaking/app.py](file:///c:/Sean_Documents/RMS+WCS_sim+Handshaking/equip_handshaking/app.py)`)**：為 FastAPI 服務，提供實體設備（如包膜機、檢驗站、棧板機等）的狀態交互與模擬交握阻塞（`time.sleep`）。

---

## 運作邏輯

### 1. WCS 設備交握流程 (EAP RESTful API)
* 當 WCS 收到 `action == "idle"` 的任務結果時，會判定為設備交握點，並依據特定步驟編號分支呼叫對應的 EAP Web API：
  * **第 1 個 `idle`** (申請進入設備#1)：呼叫 `POST /api/request-enter` (對應 `PalletSupply#1`)。
  * **第 2 個 `idle`** (設備#1完工與接手)：呼叫 `POST /api/preparation-complete` 與 `POST /api/result-query-takeover` (對應 `PalletSupply#1`)。
  * **第 3 個 `idle`** (申請進入設備#2)：呼叫 `POST /api/request-enter` (對應 `Robot_n`)。
  * **第 4 個 `idle`** (設備#2完工與接手)：呼叫 `POST /api/preparation-complete` 與 `POST /api/result-query-takeover` (對應 `Robot_n`)。
* WCS 會被 HTTP 請求同步阻塞，直到 EAP Web 服務回覆 `OK`，才發送 ACK 給 RMS，允許車輛駛入或離開。
* 非 `idle` 動作 (如 `load`, `unload` 等) 則由 WCS 直接回覆 ACK，不進行設備交握。

### 2. RMS 多任務與 2 台車限制
* **車輛資源限制**：系統限制可用車輛為 2 台（`AMR01`、`AMR02`），支援最多兩個任務併發執行。
* **任務排隊機制 (Queueing)**：當收到新搬運請求時，若車輛皆在忙碌中，RMS 會立即同步回覆 `ACK`，並將任務放入等待佇列中排隊。
* **自動資源釋放與佇列觸發**：當任務正常結束或中斷時，車輛釋放後系統會自動指派給排隊中最舊的任務。

---

## 配置文件說明 (`[config.json](file:///c:/Sean_Documents/RMS+WCS_sim+Handshaking/config.json)`)

* **本機調試建議**：預設將 `rms.host` 與 `wcs.host` 設定為 `"localhost"`。

---

## API 端點說明

### 1. RMS 伺服器 (預設 Port: `31111`)
* `POST /awd/rms/set_mission_request`：接收 WCS 任務指派。
* `POST /awd/rms/set_mission_ack`：接收 WCS 的步驟 ACK。

### 2. WCS 伺服器 (預設 Port: `31112`)
* `POST /awd/rms/set_mission_result`：接收 RMS 回報之任務步驟結果。
* `POST /awd/rms/online`：接收 RMS 上線報告。

### 3. EAP Web 服務 (預設 Port: `8000`)
* `POST /api/request-enter`：申請進入設備。
* `POST /api/preparation-complete`：準備完成通知。
* `POST /api/result-query-takeover`：等待處理結果並接手。

---

## 啟動與使用方式

整合測試需要啟動三個服務。請分別開啟三個獨立的終端機執行：

### 步驟 1: 啟動 EAP Web 服務
```powershell
cd equip_handshaking
python app.py
```
*(啟動後將在 `http://0.0.0.0:8000` 聆聽)*

### 步驟 2: 啟動 RMS 模擬器
```powershell
python rms_simulator.py --wcs-host localhost
```

### 步驟 3: 啟動 WCS 模擬器
```powershell
python wcs_simulator.py --rms-host localhost
```

### 步驟 4: 下發測試工單
在 WCS 的命令行 `WCS> ` 中輸入：
```
send HS_HS.json
```
即可觀察完整包含 4 次 EAP 交握的模擬搬運流程。

---

## 如何自訂與更換 IP 及 Port Number

本系統的所有模組皆支援在啟動時，使用命令行引數來自訂監聽 IP/Port 以及指定對方的連線位址：

### 1. 更換 EAP 服務 (Port 8000) 的監聽端點
若需要將 EAP 服務改監聽在 `192.168.1.100` 的 `9000` Port：
```powershell
python equip_handshaking/app.py --host 192.168.1.100 --port 9000
```

### 2. 更換 RMS 模擬器 (Port 31111) 監聽端點，並連線至自訂 WCS
若 RMS 需要改監聽在 `32111` Port，且其對接的 WCS 在 `192.168.1.101:32112`：
```powershell
python rms_simulator.py --port 32111 --wcs-host 192.168.1.101 --wcs-port 32112
```

### 3. 更換 WCS 模擬器 (Port 31112) 監聽端點，連線至自訂 RMS 與 EAP
若 WCS 需要改監聽在 `32112` Port，對接的 RMS 在 `192.168.1.102:32111`，且對接的 EAP 在 `192.168.1.100:9000`：
```powershell
python wcs_simulator.py --port 32112 --rms-host 192.168.1.102 --rms-port 32111 --eap-host 192.168.1.100 --eap-port 9000
```

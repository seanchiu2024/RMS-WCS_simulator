# WCS - RMS 搬運控制模擬系統

本專案實作了一套 AMR 搬運任務控制流程模擬器，用以模擬 RMS (Robot Management System) 與 WCS (Warehouse Control System) 之間的 API 互動。

系統遵循**「Request（請求） - Result（執行結果） - Ack（步驟確認）」**三階段互動原則，並支援多任務併發、車輛資源調配與任務排隊、互動式確認等進階控制。

---

## 運作邏輯

任務流程以 AMR 搬運貨物為例，子任務包含 `start`、`load`、`idle`、`unload`、`end` 等。

### 1. WCS 自動設備交握與多指令下發
- **非阻塞 CLI 控制台**：WCS 使用獨立背景執行緒讀取 Stdin，不會因等待 RMS 網路包而阻塞控制台。
- **自動設備交握 (Handshaking) 模擬**：當 WCS 收到來自 RMS 的子任務執行結果 (`set_mission_result`) 時，系統不再需要使用者手動輸入 `y/n` 回覆，而是會**自動等待 3 秒**以模擬設備交握 (Handshaking) 延時，並在交握完成後自動發送 ACK 給 RMS，允許車輛繼續下一步。
- **未來實體設備交握對接位置**：在程式碼中的 `time.sleep(3)` 區塊旁已加上詳細註解，未來可以直接在此處擴充實體 PLC、Modbus/TCP 或 Socket 通訊程式碼以實現真實的設備交握。
- **支援自訂 JSON 檔案與序號**：發送指令時支援指定不同的任務 JSON 設定檔與任務序號。

### 2. RMS 多任務與 2 台車限制
- **車輛資源限制**：系統限制可用車輛為 2 台（`AMR01`、`AMR02`），支援最多兩個任務併發執行。
- **任務排隊機制 (Queueing)**：當收到新搬運請求時，若車輛皆在忙碌中，RMS 會立即同步回覆 `ACK`（代表成功接收任務），並將任務放入等待佇列中排隊。
- **自動資源釋放與佇列觸發**：當任務正常結束或異常中斷時，車輛資源會確實釋放，系統會**自動從排隊等待佇列中取出最舊的任務指派給空閒車輛**並開始執行。

---

## 配置文件說明 (`config.json`)

```json
{
  "rms": {
    "host": "localhost",
    "port": 31111,
    "log_file": "rms_simulator.log"
  },
  "wcs": {
    "host": "localhost",
    "port": 31112,
    "log_file": "wcs_simulator.log"
  },
  "simulation": {
    "step_delay_seconds": 10.0,
    "ack_delay_seconds": 10.0,
    "default_pallet_id": "01",
    "request_timeout_seconds": 10.0,
    "ack_timeout_seconds": 300.0
  }
}
```
* **本機調試建議**：將 `rms.host` 與 `wcs.host` 設定為 `"localhost"` 以便於在本機環境運行與測試。

---

## API 端點說明

### 1. RMS 伺服器 (預設 Port: `31111`)

- **`POST /awd/rms/set_mission_request`**：接收 WCS 任務指派，若無重複序號則將其排隊或指派車輛。
- **`POST /awd/rms/set_mission_ack`**：接收 WCS 對目前子任務步驟的確認訊號。

### 2. WCS 伺服器 (預設 Port: `31112`)

- **`POST /awd/rms/set_mission_result`**：接收 RMS 回報之子任務執行結果。
- **`POST /awd/rms/online`**：接收 RMS 上線狀態報告。

---

## 啟動與使用方式

本專案完全基於 **Python 內建標準庫** 實作，無需安裝額外套件（免 `pip install`）。

### 步驟 1: 啟動 RMS 模擬器

開啟一個終端機，執行：

```powershell
python rms_simulator.py
```

### 步驟 2: 啟動 WCS 模擬器

開啟第二個終端機，執行：

```powershell
python wcs_simulator.py
```

### 步驟 3: 觸發與操控測試任務

在 WCS 模擬器的控制台畫面中，將顯示命令列提示符 `WCS> `，支援以下指令：

- **`send`**：使用隨機產生序號與預設 `mission.json` 發送任務。
- **`send <自訂序號>`** (例如 `send M20260620`)：使用自訂序號與預設 `mission.json` 發送任務。
- **`send <JSON檔名>`** (例如 `send RMS_02_mission.json`)：使用自訂 JSON 設定檔與隨機產生的序號發送任務。
- **`send <自訂序號> <JSON檔名>`** (例如 `send M9999 RMS_02_mission.json`)：使用指定的序號與指定的 JSON 設定檔發送任務。
- **`exit`**：退出程式。

#### 任務控制流程：
1. 當發送任務後，RMS 會分派車輛或將其排隊。
2. 執行中的任務在到達各個步驟時，會向 WCS 回報結果。
3. WCS 收到步驟結果後，會自動印出設備交握模擬日誌，並等待 3 秒以模擬設備交握。
4. 交握完成後，WCS 會自動向 RMS 發送 ACK 以推進流程。
5. 任務全部完成後，RMS 釋放車輛資源，若等待佇列中有排隊的任務，會自動啟動執行。

---

## 日誌紀錄說明

每次 API 呼叫的接收與發送皆會詳實紀錄於日誌中：

* **RMS 日誌**：儲存於 `rms_simulator.log` 並輸出至 Console。
* **WCS 日誌**：儲存於 `wcs_simulator.log` 並輸出至 Console。

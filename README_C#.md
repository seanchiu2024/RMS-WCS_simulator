# WCS - RMS 搬運控制模擬系統 (C# / .NET 8 版本)

本專案將原本以 Python 撰寫的 AMR 搬運任務控制流程模擬器，使用 **C# (.NET 8)** 與 **ASP.NET Core Minimal APIs** 進行了 1:1 的高性能重新開發。用以模擬 RMS (Robot Management System) 與 WCS (Warehouse Control System) 之間的 API 互動。

系統同樣遵循**「Request（請求） - Result（執行結果） - Ack（步驟確認）」**三階段互動原則，並支援多任務併發、車輛資源調配與任務排隊、互動式確認等進階控制。

---

## 運作邏輯

任務流程以 AMR 搬運貨物為例，子任務包含 `start`、`load`、`idle`、`unload`、`end` 等。

### 1. WCS 互動確認與多指令下發
- **非阻塞 CLI 控制台**：WCS 使用 `BackgroundService` 搭配背景 `Task` 監聽鍵盤輸入，不會因為等待 RMS 網路封包或等待使用者回覆而阻塞控制台或 API 伺服器。
- **互動式 ACK 詢問**：當 WCS 收到來自 RMS 的子任務執行結果 (`set_mission_result`) 時，系統會**暫停並進入互動確認模式**，於控制台詢問：
  `是否針對任務 {seq} 動作 {action} (位置: {space}) 回覆 ACK? (y/n): `
  - 輸入 `y` 或 `yes`：WCS 發送 ACK 給 RMS，允許車輛繼續下一步。
  - 輸入 `n` 或 `no`：WCS 拒絕發送 ACK，暫停任務推進。**拒絕後系統每隔 5 秒會重新詢問一次，若自首次拒絕起 30 秒內仍未獲得 `y` 的確認，將會自動回覆該步驟的 ACK**，以防任務永久卡死。
- **支援自訂 JSON 檔案與序號**：發送指令時支援指定不同的任務 JSON 設定檔與任務序號。

### 2. RMS 多任務與 2 台車限制
- **車輛資源限制**：系統限制可用車輛為 2 台（`AMR01`、`AMR02`），支援最多兩個任務併發執行。
- **任務排隊機制 (Queueing)**：當收到新搬運請求時，若車輛皆在忙碌中，RMS 會立即同步回覆 `ACK`（代表成功接收任務），並將任務放入內部等待佇列中排隊。
- **自動資源釋放與佇列觸發**：當任務正常結束或異常中斷時，車輛資源會確實釋放，系統會**自動從排隊等待佇列中取出最舊的任務指派給空閒車輛**並開始執行。

---

## 配置文件說明 (`config.json`)

C# 版本透過 `Microsoft.Extensions.Configuration` 載入位於根目錄下的 `config.json`（啟動時會自動向上搜尋父目錄以共用此檔案）：

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

本專案使用 **.NET 8.0 SDK** 開發。請確保您的開發環境已安裝對應的 SDK。

### 步驟 0: 編譯專案
開啟終端機，切換至 `csharp` 資料夾目錄並執行編譯：
```powershell
cd csharp
dotnet build
```

### 步驟 1: 啟動 RMS 模擬器

開啟第一個終端機，執行：
```powershell
cd csharp/src/RmsWcsSimulator.Rms
dotnet run
```

### 步驟 2: 啟動 WCS 模擬器

開啟第二個終端機，執行：
```powershell
cd csharp/src/RmsWcsSimulator.Wcs
dotnet run
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
3. WCS 畫面上會出現：`是否針對任務 {seq} 動作 {action} (位置: {space}) 回覆 ACK? (y/n): `
4. 輸入 **`y`** 傳送確認，任務會繼續前往下一個步驟（等待 10 秒）；輸入 **`n`** 拒絕發送確認，系統將每 5 秒重新詢問，若 30 秒內未回覆 y 則會自動發送 ACK 推進流程。
5. 任務全部完成後，RMS 釋放車輛資源，若等待佇列中有排隊的任務，會自動啟動執行。

---

## 日誌紀錄說明

每次 API 呼叫的接收與發送皆會詳實紀錄於日誌檔中（輸出到控制台的同時，也會附加到檔案中）：

* **RMS 日誌**：儲存於 `rms_simulator.log`。
* **WCS 日誌**：儲存於 `wcs_simulator.log`。

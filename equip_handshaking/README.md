# EAP 設備交握模擬與 API 服務

本專案提供 AGV/AMR (自動導引車/自主移動機器人) 與 EAP (設備自動化協定) 之間交握 (Handshaking) 的模擬邏輯與 HTTP RESTful API 服務。專案以 **同步式等待 (Sync Blocking Wait)** 進行設計，確保物流搬運過程的流暢性與資源排他性。

---

## 1. 主要程式與檔案簡介

專案中各個程式檔案的角色與功能如下：

*   **[equip_handshaking.py](file:///c:/Sean_Documents/equip_handshaking/equip_handshaking.py)**：
    底層核心交握邏輯與模擬工作流。包含三個核心交握函式：
    1.  `request_enter`：申請進入設備干涉區。
    2.  `preparation_complete`：準備完成通知（同步等待機台接手）。
    3.  `result_query_takeover`：同步等待設備處理結果，完成後釋放資源。
    檔案直接執行時會運行預設的模擬情境 (模擬 Wrap 包膜機、Check 檢驗站、ASRS 入庫等流程)。

*   **[app.py](file:///c:/Sean_Documents/equip_handshaking/app.py)**：
    基於 **FastAPI** 框架建立的 Web API 服務。將底層 `equip_handshaking.py` 的核心函式封裝為 HTTP POST 介面，便於外部系統進行整合。
    提供以下端點：
    *   `/api/request-enter` (或 `/api/enter-request`)：申請進入設備。
    *   `/api/preparation-complete`：準備完成通知。
    *   `/api/result-query-takeover`：等待處理結果並接手。

*   **[test_api.py](file:///c:/Sean_Documents/real_equip_handshaking/test_api.py)**：
    API 測試腳本。模擬 AGV 發送不同格式 (使用別名或內嵌 `extra_args`) 的 JSON 請求至 Web 服務，用於快速驗證 API 服務是否正常運作。

*   **[eap_config.py](file:///c:/Sean_Documents/real_equip_handshaking/eap_config.py)**：
    EAP 設備 URL 設定查詢模組。使用 PyYAML 套件解析 `EAP_url_config.yaml`，提供查詢對應的 `equipment_POST_url`、`equipment_GET_url`、`sensor_POST_url` 並回傳字典的類別與方法。

*   **[EAP_url_config.yaml](file:///c:/Sean_Documents/real_equip_handshaking/EAP_url_config.yaml)**：
    EAP 設備 URL 對照設定檔 (YAML 格式)。儲存了各設備工位樓層的 POST、GET 以及 RFID 等感測器 URL 訊號位置。

*   **[equip_handshaking_function_v1.1.md](file:///c:/Sean_Documents/real_equip_handshaking/equip_handshaking_function_v1.1.md)**：
    詳細的 EAP 設備交握規範說明文件，包含支援的設備類型 (Wrap, Check, Aligner, PalletSupply, ASRS_IPORT, ASRS_OPORT, LIFT)、目的模式定義、交握時序圖 (Mermaid) 以及 API 呼叫範例。

*   **[EAP_data_extract_method.md](file:///c:/Sean_Documents/equip_handshaking/EAP_data_extract_method.md)**：
    EAP 設備交握狀態資料解析規範，說明如何解析 `data` 欄位以逗號與冒號區隔的訊號字串，並提供 Python 解析實作範例。

---

## 2. 重要設定與環境依賴

### 環境需求
*   **Python 3.10+** (因核心邏輯採用了 `match-case` 模式分流語法)。

### 套件依賴
執行 Web 服務與測試需要安裝以下 Python 套件：
*   `fastapi`：Web 框架
*   `uvicorn`：ASGI 伺服器
*   `pydantic`：資料驗證
*   `requests`：發送測試 HTTP 請求
*   `pyyaml`：YAML 檔案載入與解析 (用於 `eap_config.py`)

### 日誌設定 (Logging)
*   系統執行時，交握過程的詳細記錄會自動寫入專案根目錄下的 **`handshaking.log`** 檔案。
*   同時，日誌亦會輸出至主控台 (Console) 供即時檢視。

### Port 號碼調整說明
Web 服務與測試腳本預設運作於 **Port 8000**。若有需要修改該埠號，請調整以下程式碼位置：
1.  **Web 服務端 (app.py)**：
    開啟 [app.py](file:///c:/Sean_Documents/equip_handshaking/app.py)，在檔案的最下方：
    ```python
    if __name__ == "__main__":
        # 啟動 Web Server，聆聽 port 8000
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    ```
    將 `port=8000` 修改為您所需的埠號（例如 `8080`）。

2.  **API 測試腳本與外部呼叫端 (test_api.py)**：
    開啟 [test_api.py](file:///c:/Sean_Documents/equip_handshaking/test_api.py)，在檔案上方：
    ```python
    url = 'http://127.0.0.1:8000/api/request-enter'
    ```
    將 URL 中的埠號 `8000` 修改為與 `app.py` 相同的值（例如 `http://127.0.0.1:8080/api/request-enter`）。

---

## 3. 使用與啟動方式

在開始之前，請確保已切換至專案根目錄。

### 步驟 1：安裝套件依賴
在終端機中執行以下指令安裝所需套件：
```bash
pip install fastapi uvicorn pydantic requests
```

### 步驟 2：運行核心流程模擬 (Mock Mode)
若要單獨驗證底層交握邏輯與工作流，可直接執行 `equip_handshaking.py`：
```bash
python equip_handshaking.py
```
此動作將會在控制台輸出三個場景的模擬步驟，並將日誌寫入 `handshaking.log`。

### 步驟 3：啟動 Web API 服務
若要啟動 HTTP API 服務以供外部系統呼叫，請執行 `app.py`：
```bash
python app.py
```
服務啟動後，預設監聽 `http://localhost:8000`。

---

## 4. 人工 / 手動測試指南

啟動 Web API 服務後，您可以透過以下幾種方式進行人工測試：

### 方式 A：使用 FastAPI Swagger UI (最推薦)
FastAPI 自動生成互動式 API 文件。
1.  啟動 Web API 服務後，在瀏覽器打開：[http://localhost:8000/docs](http://localhost:8000/docs)。
2.  在頁面中，點選您想要測試的 API（例如 `POST /api/request-enter`）。
3.  點擊右側的 **"Try it out"** 按鈕。
4.  在 **Request body** 欄位中，填入 JSON 測試參數。例如：
    ```json
    {
      "equipment_type": "ASRS_IPORT",
      "wes_id": "WES_MANUAL_01",
      "purpose_mode": 1,
      "PalletNo": "PLT_MANUAL_123",
      "CargoHeight": "High",
      "RackInPlace": true
    }
    ```
5.  點擊下方藍色的 **"Execute"** 按鈕發送請求，即可於頁面上查看到 Response 狀態碼與 JSON 回應內容。

### 方式 B：使用 curl 命令列工具手動測試
您可以使用 `curl` 指令直接在終端機中對 API 進行請求測試。

#### 1. 測試：申請進入設備 (Request Enter)
以 ASRS_IPORT 為例，發送請求：
```bash
curl -X POST "http://localhost:8000/api/request-enter" \
     -H "Content-Type: application/json" \
     -d "{\"equipment_type\": \"ASRS_IPORT\", \"wes_id\": \"WES_CURL_01\", \"purpose_mode\": 1, \"PalletNo\": \"PLT_CURL_01\", \"CargoHeight\": \"Normal\", \"RackInPlace\": true}"
```
*預期回應：* `{"status":"OK"}`

#### 2. 測試：準備完成通知 (Preparation Complete)
```bash
curl -X POST "http://localhost:8000/api/preparation-complete" \
     -H "Content-Type: application/json" \
     -d "{\"equipment_type\": \"ASRS_IPORT\", \"wes_id\": \"WES_CURL_01\", \"purpose_mode\": 1}"
```
*預期回應：* `{"status":"OK"}`

#### 3. 測試：等待處理結果並接手 (Result Query Takeover)
```bash
curl -X POST "http://localhost:8000/api/result-query-takeover" \
     -H "Content-Type: application/json" \
     -d "{\"equipment_type\": \"ASRS_IPORT\", \"wes_id\": \"WES_CURL_01\", \"purpose_mode\": 1}"
```
*預期回應：* `{"status":"OK"}`

### 方式 C：執行內建的 API 測試腳本
在保持 Web 服務運行的終端機外，開啟另一個終端機視窗並執行：
```bash
python test_api.py
```
這會模擬發送兩種不同 Payload 格式至 `/api/request-enter` 端點並輸出結果。

---

## 5. EAP URL 設定查詢器 (YAML)

專案中提供了 `EAPUrlConfig` 類別，能直接自 YAML 檔案中查詢對應設備與任務 ID 的三個重要端點網址（`equipment_POST_url`, `equipment_GET_url`, `sensor_POST_url`）。

### 使用步驟

1. 確保已安裝 `pyyaml`：
   ```bash
   pip install pyyaml
   ```
2. 在您的 Python 程式碼中匯入與呼叫：
   ```python
   from eap_config import EAPUrlConfig

   # 初始化讀取器 (預設讀取 EAP_url_config.yaml)
   config_reader = EAPUrlConfig()

   # 代入 equipment_type 與 wes_id 查詢
   res = config_reader.get_urls(equipment_type="ASRS_OPORT", wes_id="OPT_104")

   if res:
       # 將取得的 URL 指派給 3 個變數
       post_url = res["equipment_POST_url"]
       get_url = res["equipment_GET_url"]
       sensor_url = res["sensor_POST_url"]

       # 之後使用變數印出或呼叫 API
       print(f"Post URL: {post_url}")
       print(f"Get URL: {get_url}")
       print(f"Sensor URL: {sensor_url}")
   ```
3. 您可以直接在終端機中執行該模組進行功能測試：
   ```bash
   python eap_config.py
   ```


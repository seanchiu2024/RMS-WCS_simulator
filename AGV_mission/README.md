# 任務生成模組 (generate_mission)

本模組提供 Python 函數 `generate_mission`，能依據指定的起點 (`sourcepoint`) 與終點 (`targetpoint`)，自動對照站點等待暫存點對照表，生成符合搬送規範的任務 JSON 資料。

---

## 1. 功能介紹

本模組主要功能為將搬送起訖點對照「站點/等待暫存點 (wait_point)」的映射關係，並根據起迄點是否有對應的等待暫存點，動態展開為以下四種不同的子任務序列 (`sub_missions`)：

* **分支 1**：起點無 wait_point，終點無 wait_point
  * 任務結構：`start` -> `load` -> `unload` -> `end`
* **分支 2**：起點有 wait_point，終點無 wait_point
  * 任務結構：`start (起點等待)` -> `idle (起點等待)` -> `load (起點)` -> `idle (起點等待)` -> `unload (終點)` -> `end (終點)`
* **分支 3**：起點無 wait_point，終點有 wait_point
  * 任務結構：`start (起點)` -> `load (起點)` -> `idle (終點等待)` -> `unload (終點)` -> `idle (終點等待)` -> `end (終點等待)`
* **分支 4**：起點有 wait_point，終點有 wait_point
  * 任務結構：`start (起點等待)` -> `idle (起點等待)` -> `load (起點)` -> `idle (起點等待)` -> `idle (終點等待)` -> `unload (終點)` -> `idle (終點等待)` -> `end (終點等待)`

---

## 2. 搭配條件與設定說明

運作此模組需要以下兩項設定與檔案：

### A. 設定檔 `config.json`
本程式會在**模組同目錄下**讀取 `config.json`。若該檔案不存在，程式會在第一次執行時自動建立預設內容：
```json
{
    "hs_lookup_table_path": "hs_lookup_table.csv"
}
```
* `hs_lookup_table_path`：指定對照表 CSV 檔案的路徑（支援絕對路徑或相對於本 Python 程式的相對路徑）。

### B. 對照表 CSV 格式 (`hs_lookup_table.csv`)
對照表應為 CSV 格式，建議使用 `utf-8-sig` (包含 BOM) 或 `utf-8` 編碼，且必須包含以下兩個欄位：
* `point_id`：站點 ID
* `wait_point_id`：與該站點對照的等待/暫存點 ID（若無對照則留空）

**範例內容：**
```csv
point_id,wait_point_id
IPT_101,IPTW101
OPT_101,OPTW101
ARE_101,
```

---

## 3. 如何測試

本模組內建了測試區塊，您可以直接執行該 Python 檔案進行功能驗證。

### 測試步驟
1. 確保工作目錄下有 `hs_lookup_table.csv`。
2. 打開終端機並切換至專案目錄，執行以下指令：
   ```bash
   python generate_mission.py
   ```
3. 執行後將會：
   * 自動在同目錄產生 `config.json`（若尚未建立）。
   * 於終端機印出 4 個分支的測試任務 JSON 結果。

---

## 4. 整合至其他程式之建議做法 (方案 A)

如果您想在其他 Python 程式中呼叫並使用此功能，建議採用模組化直接導入的做法：

### 推薦目錄架構
確保您的主程式與 `generate_mission.py`、`config.json` 及對照表檔案的位置關係如下：
```text
your_project/
│
├── main.py (您的主程式)
├── generate_mission.py (本模組)
├── config.json (設定檔)
└── hs_lookup_table.csv (對照表)
```

### 主程式整合範例 (`main.py`)
在您的程式中直接 `import` 該函數即可呼叫：

```python
import json
# 導入任務生成函數
from generate_mission import generate_mission

def run_agv_system():
    # 設定搬送起訖點
    source = "IPT_101"
    target = "ARE_101"
    
    # 產生任務 (可選傳入唯一的 sequence 序號與優先權 priority)
    try:
        mission_data = generate_mission(
            sourcepoint=source, 
            targetpoint=target, 
            sequence="M_TEST_999",
            priority="128"
        )
        
        # 輸出結果
        print("產生的任務 JSON:")
        print(json.dumps(mission_data, indent=2, ensure_ascii=False))
        
    except FileNotFoundError as e:
        print(f"錯誤：找不到對照表檔案，請檢查設定與路徑：{e}")
    except Exception as e:
        print(f"產生任務時發生預期外錯誤：{e}")

if __name__ == "__main__":
    run_agv_system()
```

### 整合注意事項
1. **設定檔定位基準**：`generate_mission.py` 會自動以 **它自身所在的目錄** 來定位 `config.json`，因此 `config.json` 必須與 `generate_mission.py` 放在同一個資料夾下。
2. **相對路徑解析**：若在 `config.json` 中設定 `hs_lookup_table_path` 為相對路徑（例如 `"hs_lookup_table.csv"`），該模組會優先在 `generate_mission.py` 所在的同目錄下尋找；若不存在，則會在當前執行目錄 (CWD) 下尋找。

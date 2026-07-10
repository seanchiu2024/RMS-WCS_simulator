# EAP 設備交握狀態資料解析規範 (EAP_data.md)

本文件整理並說明 EAP 設備在交握過程中回傳的 JSON 狀態包格式，並詳細列出 `data` 欄位內部所含的各項訊號狀態定義，同時提供 Python 的通用解析實作範例。

---

## 1. JSON 回傳資料格式

當向 EAP 設備或 Web 服務發送交握請求時，回傳的 JSON 回應格式如下所示：

```json
{
    "isSuccess": true,
    "code": 0,
    "msg": "",
    "data": "IsReady:True,IsConnected:True,errorCode:0,AGVInbound:True,AGVOutbound:False,IsStationFull:False,IsMaterialShort:False,Next:1,Mod:0"
}
```

- **`isSuccess`** (bool): 請求執行是否成功。
- **`code`** (int): 系統回傳狀態碼 (0 代表正常)。
- **`msg`** (str): 錯誤或提示訊息內容。
- **`data`** (str): 實體設備交握訊號狀態字串，欄位以逗號 `,` 區隔，鍵值對以冒號 `:` 連接。

---

## 2. data 內部交握訊號欄位說明

`data` 字串解析後，所含的各個訊號鍵值規格定義如下：

| 訊號名稱 (Key) | 資料型態 | 範例值 | 功能與含意說明 |
| :--- | :--- | :--- | :--- |
| **`IsReady`** | `bool` | `True` | 設備是否已就緒 (允許 AGV/AMR 開始動作) |
| **`IsConnected`** | `bool` | `True` | 設備與 EAP 上游系統是否連線正常 |
| **`errorCode`** | `int` | `0` | 設備內部錯誤碼 (0 代表無異常) |
| **`AGVInbound`** | `bool` | `True` | AGV 是否處於放貨進入狀態 |
| **`AGVOutbound`** | `bool` | `False` | AGV 是否處於取貨退出狀態 |
| **`IsStationFull`** | `bool` | `False` | 設備站點工位是否為滿料狀態 (已有貨物) |
| **`IsMaterialShort`** | `bool` | `False` | 設備是否缺料中 |
| **`Next`** | `int` | `1` | 設備指引的下一步交握步驟代碼 |
| **`Mod`** | `int` | `0` | 設備當前運作模式代碼 |

---

## 3. Python 欄位解析實作範例

以下是直接可執行的 Python 程式碼，展示如何讀取此 JSON 回傳內容，並將 `data` 內部所有的訊號字串轉換為正確的 Python 資料型態 (`bool`、`int`、`str`)。

```python
import json

# 1. 模擬 EAP 設備回傳的原始 JSON 資料
json_response = """
{
    "isSuccess": true,
    "code": 0,
    "msg": "",
    "data": "IsReady:True,IsConnected:True,errorCode:0,AGVInbound:True,AGVOutbound:False,IsStationFull:False,IsMaterialShort:False,Next:1,Mod:0"
}
"""

def parse_eap_data(data_str: str) -> dict:
    """
    將 data 欄位的以逗號和冒號連接的字串，解析為對應型態的字典。
    """
    result = {}
    if not data_str:
        return result
        
    for item in data_str.split(","):
        if ":" not in item:
            continue
        key, val = item.split(":", 1)
        
        # 轉譯為布林值
        if val.lower() == "true":
            result[key] = True
        elif val.lower() == "false":
            result[key] = False
        # 轉譯為整數
        elif val.isdigit() or (val.startswith("-") and val[1:].isdigit()):
            result[key] = int(val)
        # 保持為原始字串
        else:
            result[key] = val
            
    return result


# ==========================================
# 測試解析流程
# ==========================================

# 第一步：載入 JSON
resp_dict = json.loads(json_response)

# 第二步：取得 data 字串並解析
eap_signals = parse_eap_data(resp_dict.get("data", ""))

# 第三步：列印解析後的結果
print("=== 解析後的字典內容 ===")
print(json.dumps(eap_signals, indent=4))

print("\n=== 特定訊號讀取測試 ===")
print("IsReady:       ", eap_signals.get("IsReady"))          # 輸出: True (bool)
print("IsStationFull: ", eap_signals.get("IsStationFull"))    # 輸出: False (bool)
print("errorCode:     ", eap_signals.get("errorCode"))        # 輸出: 0 (int)
```

import requests
import json
import time

url = 'http://127.0.0.1:8000/api/request-enter'

# 測試用 Payload 1: 使用別名 RackInPlace
payload_alias = {
    "equipment_type": "ASRS_IPORT",
    "wes_id": "WES_TEST_01",
    "purpose_mode": 1,
    "PalletNo": "PLT_TEST_ALIAS",
    "CargoHeight": "Normal",
    "RackInPlace": True
}

# 測試用 Payload 2: 使用 extra_args 中的 rack_in_place
payload_extra = {
    "equipment_type": "ASRS_IPORT",
    "wes_id": "WES_TEST_02",
    "purpose_mode": 1,
    "extra_args": {
        "pallet_no": "PLT_TEST_EXTRA",
        "cargo_height": "High",
        "rack_in_place": True
    }
}

# 等待伺服器啟動
time.sleep(2)

print("--- 測試 Payload 1 (使用別名 RackInPlace) ---")
resp = requests.post(url, json=payload_alias)
print('Status:', resp.status_code)
print('Response:', resp.json())

print("\n--- 測試 Payload 2 (使用 extra_args 欄位) ---")
resp = requests.post(url, json=payload_extra)
print('Status:', resp.status_code)
print('Response:', resp.json())

import os
import json

# 預設設定值
DEFAULT_CONFIG = {
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
    "request_timeout_seconds": 5.0,
    "ack_timeout_seconds": 60.0
  }
}

config_path = "config.json"

# 載入或建立預設設定檔
if not os.path.exists(config_path):
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"無法建立預設設定檔: {e}")

# 讀取設定檔
_config = DEFAULT_CONFIG.copy()
if os.path.exists(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
            # 更新設定項目
            for section in DEFAULT_CONFIG:
                if section in user_config:
                    _config[section].update(user_config[section])
    except Exception as e:
        print(f"讀取 {config_path} 失敗，使用預設設定。錯誤: {e}")

# 導出模組全域變數，供其它程式直接 import
RMS_HOST = _config["rms"]["host"]
RMS_PORT = int(_config["rms"]["port"])
RMS_LOG_FILE = _config["rms"]["log_file"]

WCS_HOST = _config["wcs"]["host"]
WCS_PORT = int(_config["wcs"]["port"])
WCS_LOG_FILE = _config["wcs"]["log_file"]

STEP_DELAY = float(_config["simulation"]["step_delay_seconds"])
ACK_DELAY = float(_config["simulation"]["ack_delay_seconds"])
DEFAULT_PALLET_ID = _config["simulation"]["default_pallet_id"]
REQUEST_TIMEOUT = float(_config["simulation"]["request_timeout_seconds"])
ACK_TIMEOUT = float(_config["simulation"]["ack_timeout_seconds"])

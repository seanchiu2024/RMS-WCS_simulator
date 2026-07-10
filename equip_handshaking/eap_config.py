import yaml
import os
from typing import Dict, Optional

class EAPUrlConfig:
    """
    用於讀取 EAP_url_config.yaml 檔案並根據 equipment_type 與 wes_id 查詢對應的 URL。
    """
    def __init__(self, yaml_path: str = "EAP_url_config.yaml"):
        self.yaml_path = yaml_path
        self.configs = []
        self.load_config()

    def load_config(self):
        """
        載入並解析 YAML 設定檔，過濾無效資料。
        """
        if not os.path.exists(self.yaml_path):
            raise FileNotFoundError(f"找不到設定檔: {self.yaml_path}")

        with open(self.yaml_path, mode='r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if not isinstance(data, list):
                return
            
            for item in data:
                eq_type = item.get("equipment_type")
                wes_id = item.get("wes_id")
                if not eq_type or not wes_id or not str(eq_type).strip() or not str(wes_id).strip():
                    continue
                
                self.configs.append({
                    "equipment_type": str(eq_type).strip(),
                    "wes_id": str(wes_id).strip(),
                    "equipment_POST_url": str(item.get("equipment_POST_url") or "").strip(),
                    "equipment_GET_url": str(item.get("equipment_GET_url") or "").strip(),
                    "sensor_POST_url": str(item.get("sensor_POST_url") or "").strip(),
                })

    def get_urls(self, equipment_type: str, wes_id: str) -> Optional[Dict[str, str]]:
        """
        依傳入的 equipment_type 與 wes_id 提取對應的 URLs，並使用 print 顯示。
        
        :param equipment_type: 設備類型 (例如: ASRS_IPORT, LIFT, Wrap)
        :param wes_id: 任務編號或設備 ID (例如: IPT_101, LFT_101)
        :return: 包含三個 URL 的 dict，若找不到則回傳 None
        """
        target = None
        for config in self.configs:
            if config["equipment_type"] == equipment_type and config["wes_id"] == wes_id:
                target = config
                break

        print(f"=== 查詢結果: equipment_type='{equipment_type}', wes_id='{wes_id}' ===")
        if target:
            # 將三個 URL assign 給 3 個變數
            equipment_POST_url = target["equipment_POST_url"]
            equipment_GET_url = target["equipment_GET_url"]
            sensor_POST_url = target["sensor_POST_url"]

            # 用 print 印出變數
            print(f"  equipment_POST_url : {equipment_POST_url}")
            print(f"  equipment_GET_url  : {equipment_GET_url}")
            print(f"  sensor_POST_url     : {sensor_POST_url}")
            print("==================================================================")
            return {
                "equipment_POST_url": equipment_POST_url,
                "equipment_GET_url": equipment_GET_url,
                "sensor_POST_url": sensor_POST_url
            }
        else:
            print("  [錯誤] 找不到對應的設定！")
            print("==================================================================")
            return None


if __name__ == "__main__":
    # 測試執行示範
    print("開始測試 EAPUrlConfig 類別...")
    try:
        config_reader = EAPUrlConfig()
        
        # 測試正常查詢 1: ASRS_IPORT - IPT_101
        res = config_reader.get_urls("ASRS_OPORT", "OPT_104")
        if res:
            # 外部 assign 給 3 個變數並印出
            post_url = res["equipment_POST_url"]
            get_url = res["equipment_GET_url"]
            sensor_url = res["sensor_POST_url"]
            print("  [外部變數印出測試]")
            print(f"    Post URL  : {post_url}")
            print(f"    Get URL   : {get_url}")
            print(f"    Sensor URL: {sensor_url}")
            print("==================================================================")
            
        # 測試正常查詢 2: Aligner - ALN_101
        config_reader.get_urls("Aligner", "ALN_101")
        
        # 測試不存在的設定
        config_reader.get_urls("NonExistType", "DummyID")

        
    except Exception as e:
        print(f"測試過程中發生異常: {e}")

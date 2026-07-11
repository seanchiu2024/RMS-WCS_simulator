import csv
import os
import json
from datetime import datetime

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def get_config_lookup_table_path():
    default_config = {
        "hs_lookup_table_path": "hs_lookup_table.csv"
    }
    if not os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
        except Exception:
            pass
        return default_config["hs_lookup_table_path"]
    
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("hs_lookup_table_path", "hs_lookup_table.csv")
    except Exception:
        return "hs_lookup_table.csv"

def load_lookup_table(hs_lookup_table=None):
    """
    載入對照表。
    :param hs_lookup_table: 可以是 csv 檔案路徑，或是 dict 字典。若為 None 則從設定檔讀取。
    :return: dict，key 為 point_id，value 為 wait_point_id
    """
    if hs_lookup_table is None:
        hs_lookup_table = get_config_lookup_table_path()
        
        # 處理相對路徑，相對於 python 檔案同目錄
        if not os.path.isabs(hs_lookup_table):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            abs_path = os.path.join(base_dir, hs_lookup_table)
            if os.path.exists(abs_path):
                hs_lookup_table = abs_path

    if isinstance(hs_lookup_table, dict):
        return hs_lookup_table
    
    lookup = {}
    if isinstance(hs_lookup_table, str):
        if not os.path.exists(hs_lookup_table):
            raise FileNotFoundError(f"找不到對照表檔案: {hs_lookup_table}")
        
        # 讀取 CSV 檔案，採用編碼容錯處理
        try:
            with open(hs_lookup_table, mode='r', encoding='utf-8-sig', errors='ignore') as f:
                rows = list(csv.DictReader(f))
        except UnicodeDecodeError:
            with open(hs_lookup_table, mode='r', encoding='cp950', errors='ignore') as f:
                rows = list(csv.DictReader(f))

        for row in rows:
            pid = row.get('point_id')
            wpid = row.get('wait_point_id')
            if pid:
                pid_clean = pid.strip()
                wpid_clean = wpid.strip() if wpid else ""
                # 若為空字串或無效，則設定為 None (等同於 null)
                lookup[pid_clean] = wpid_clean if wpid_clean else None
    return lookup

def generate_mission(sourcepoint, targetpoint, sequence=None, priority="128"):
    """
    生成任務 JSON
    :param sourcepoint: 起點 point_id
    :param targetpoint: 終點 point_id
    :param sequence: 唯一的 sequence 序號，若為 None 則自動生成
    :param priority: 優先權
    :return: dict 格式的任務資訊
    """
    lookup = load_lookup_table()
    
    # 查找 wait_point_id，查不到則為 None
    sourcepoint_W = lookup.get(sourcepoint) if lookup else None
    targetpoint_W = lookup.get(targetpoint) if lookup else None
    
    # 生成 sequence，若未指定則自動生成唯一序號 (M + timestamp)
    if not sequence:
        sequence = f"M{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        
    # 生成 timestamp (格式如 2026-07-07 09:00:01.0000)
    # Python %f 為 6 位微秒，切片截取前 4 位毫秒
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-2]
    
    # 判斷分支邏輯
    if sourcepoint_W is None and targetpoint_W is None:
        sub_missions = [
            { "space": sourcepoint, "action": "start"},      
            { "space": sourcepoint, "action": "load"},       
            { "space": targetpoint, "action": "unload"},  
            { "space": targetpoint, "action": "end"}      
        ]
    elif sourcepoint_W is not None and targetpoint_W is None:
        sub_missions = [
            { "space": sourcepoint_W, "action": "start"},
            { "space": sourcepoint_W, "action": "idle"},      
            { "space": sourcepoint, "action": "load"}, 
            { "space": sourcepoint_W, "action": "idle"},    
            { "space": targetpoint, "action": "unload"},  
            { "space": targetpoint, "action": "end"}      
        ]
    elif sourcepoint_W is None and targetpoint_W is not None:
        sub_missions = [
            { "space": sourcepoint, "action": "start"},
            { "space": sourcepoint, "action": "load"}, 
            { "space": targetpoint_W, "action": "idle"},    
            { "space": targetpoint, "action": "unload"},  
            { "space": targetpoint_W, "action": "idle"},      
            { "space": targetpoint_W, "action": "end"}      
        ]
    else: # sourcepoint_W is not None and targetpoint_W is not None
        sub_missions = [
            { "space": sourcepoint_W, "action": "start"},
            { "space": sourcepoint_W, "action": "idle"},    
            { "space": sourcepoint, "action": "load"}, 
            { "space": sourcepoint_W, "action": "idle"}, 
            { "space": targetpoint_W, "action": "idle"},    
            { "space": targetpoint, "action": "unload"},  
            { "space": targetpoint_W, "action": "idle"},      
            { "space": targetpoint_W, "action": "end"}      
        ]
        
    mission = {
        "sequence": sequence,
        "timestamp": timestamp,
        "priority": str(priority),
        "sub_missions": sub_missions
    }
    
    return mission

if __name__ == "__main__":
    # 測試程式碼
    print("=== 測試 1: IPT_101 (有 wait) -> ARE_101 (無 wait) ===")
    m1 = generate_mission("IPT_101", "ARE_101", sequence="M10000003")
    print(json.dumps(m1, indent=2, ensure_ascii=False))
    
    print("\n=== 測試 2: ARE_101 (無 wait) -> ARE_102 (無 wait) ===")
    m2 = generate_mission("ARE_101", "ARE_102", sequence="M10000004")
    print(json.dumps(m2, indent=2, ensure_ascii=False))

    print("\n=== 測試 3: ARE_101 (無 wait) -> IPT_101 (有 wait) ===")
    m3 = generate_mission("ARE_101", "IPT_101", sequence="M10000005")
    print(json.dumps(m3, indent=2, ensure_ascii=False))

    print("\n=== 測試 4: IPT_101 (有 wait) -> OPT_101 (有 wait) ===")
    m4 = generate_mission("IPT_101", "OPT_101", sequence="M10000006")
    print(json.dumps(m4, indent=2, ensure_ascii=False))


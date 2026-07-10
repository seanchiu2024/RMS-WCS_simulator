#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
永聯聯華觀音廠 - EAP 設備交握 Python 實作範例
本檔案定義了與 EAP 系統進行同步交握的客戶端類別，並包含完整的流程模擬。
"""

import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

class EAPEquipmentClient:
    def __init__(self, base_url: str, equipment_id: str, equipment_type: str, mock_mode: bool = True):
        """
        初始化 EAP 設備交握客戶端
        
        :param base_url: EAP API 伺服器的基礎 URL (例如 'http://localhost:8080')
        :param equipment_id: 設備識別 ID (例如 'WRAP_01')
        :param equipment_type: 設備類型 (例如 'Wrap', 'Check', 'Aligner', 'PalletSupply', 'Robot')
        :param mock_mode: 是否啟用模擬模式。若為 True，將不會發送真實 HTTP 請求，而是模擬回傳值。
        """
        self.base_url = base_url.rstrip('/')
        self.equipment_id = equipment_id
        self.equipment_type = equipment_type
        self.mock_mode = mock_mode

    def _send_request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        發送 HTTP 請求的輔助方法 (在 mock_mode=False 時使用)
        """
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode('utf-8') if payload else None
        headers = {'Content-Type': 'application/json'}
        
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.URLError as e:
            print(f"[Error] 連線至 {url} 失敗: {e}")
            return {"status": "ERROR", "message": str(e)}

    def request_enter(self, wes_id: str, purpose_mode: int) -> str:
        """
        ［1］ 申請進入設備 (Request Enter)
        
        :param wes_id: WES 任務 ID
        :param purpose_mode: 申請目的模式 (1=預包膜, 2=全包膜, 3=單板進出, 4=整板進出)
        :return: "OK" 或 "WAIT"
        """
        path = "/api/v1/equipment/request-enter"
        payload = {
            "equipment_type": self.equipment_type,
            "equipment_id": self.equipment_id,
            "wes_id": wes_id,
            "purpose_mode": purpose_mode
        }
        
        print(f"\n[RequestEnter] 任務 {wes_id} 申請進入設備 {self.equipment_id}...")
        print(f"  -> Payload: {json.dumps(payload, ensure_ascii=False)}")
        
        if self.mock_mode:
            time.sleep(0.5)
            return "OK"
        
        resp = self._send_request("POST", path, payload)
        return resp.get("status", "WAIT")

    def preparation_complete(self, wes_id: str, purpose_mode: int) -> str:
        """
        ［2］ 準備完成通知 (Preparation Complete) - 同步式等待
        
        :param wes_id: WES 任務 ID
        :param purpose_mode: 申請目的模式
        :return: "OK" 或 "WAIT"
        """
        path = "/api/v1/equipment/action-complete"
        payload = {
            "equipment_id": self.equipment_id,
            "wes_id": wes_id,
            "purpose_mode": purpose_mode,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        print(f"\n[PreparationComplete] 設備 {self.equipment_id} 準備完成通知，同步等待機台接手確認...")
        print(f"  -> Payload: {json.dumps(payload, ensure_ascii=False)}")
        
        if self.mock_mode:
            print("  -> [Sync Wait] 正在同步等待機台發送接手訊號...")
            time.sleep(2.0)  # 模擬等待機台接手時間
            print("  -> 機台已接手機制。")
            return "OK"
            
        resp = self._send_request("POST", path, payload)
        return resp.get("status", "WAIT")

    def result_query_takeover(self, wes_id: str, purpose_mode: int) -> str:
        """
        ［3］ 等待處理結果並接手 (ResultQuery_TakeOver) - 同步式等待
        針對不同 equipment_type 展開成 match-case，各 case 預設 sleep 10 秒後回傳。
        
        :param wes_id: WES 任務 ID
        :param purpose_mode: 申請目的模式
        :return: "OK" 或 "WAIT"
        """
        print(f"\n[ResultQuery_TakeOver] 設備 {self.equipment_id} ({self.equipment_type}) 開始同步等待作業結果...")
        
        if self.mock_mode:
            match self.equipment_type:
                case "Wrap":
                    print("  -> [Match-Case] 進入 [Wrap] 包膜機分支，預設等待作業 10 秒...")
                    time.sleep(10)
                    print("  -> [Wrap] 包膜作業完成，成功回報 WES 並釋放資源。")
                    return "OK"
                case "Check":
                    print("  -> [Match-Case] 進入 [Check] 檢驗設備分支，預設等待作業 10 秒...")
                    time.sleep(10)
                    print("  -> [Check] 檢驗作業完成，成功回報 WES 並釋放資源。")
                    return "OK"
                case "Aligner":
                    print("  -> [Match-Case] 進入 [Aligner] 糾偏機分支，預設等待作業 10 秒...")
                    time.sleep(10)
                    print("  -> [Aligner] 糾偏作業完成，成功回報 WES 並釋放資源。")
                    return "OK"
                case "PalletSupply":
                    print("  -> [Match-Case] 進入 [PalletSupply] 棧板供應機分支，預設等待作業 10 秒...")
                    time.sleep(10)
                    print("  -> [PalletSupply] 棧板供應完成，成功回報 WES 並釋放資源。")
                    return "OK"
                case "Robot":
                    print("  -> [Match-Case] 進入 [Robot] 機械手臂分支，預設等待作業 10 秒...")
                    time.sleep(10)
                    print("  -> [Robot] 手臂抓取搬運完成，成功回報 WES 並釋放資源。")
                    return "OK"
                case _:
                    print(f"  -> [Match-Case] 未知設備類型 {self.equipment_type}，預設等待 10 秒...")
                    time.sleep(10)
                    return "OK"
        else:
            # 真實連線狀態下的同步輪詢與設備分流處理
            path = f"/api/v1/equipment/status?equipment_id={self.equipment_id}&wes_id={wes_id}"
            start_time = time.time()
            
            # 真實環境亦可使用 match-case 來設定不同設備類型的專屬輪詢間隔與超時限制
            poll_interval = 2.0
            timeout_limit = 60.0
            
            match self.equipment_type:
                case "Wrap" | "Robot":
                    poll_interval = 2.5
                    timeout_limit = 120.0  # 包膜與手臂可能需要較長等待超時
                case "Check":
                    poll_interval = 1.0
                    timeout_limit = 30.0
            
            while True:
                resp = self._send_request("GET", path)
                if resp.get("process_status") == "COMPLETED":
                    # 此處內部可自動發送釋放訊號並通知 WES
                    print("  -> 設備完成作業，資源已釋放。")
                    return "OK"
                
                time.sleep(poll_interval)
                if time.time() - start_time > timeout_limit:
                    print("  -> [Timeout] 同步等待設備處理結果超時。")
                    return "WAIT"

    def send_heartbeat(self, node_id: str) -> dict:
        """
        ［4］ 心跳機制 (Heartbeat)
        
        :param node_id: 發送心跳的節點 ID
        """
        path = "/api/v1/equipment/heartbeat"
        payload = {
            "node_id": node_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        print(f"\n[Heartbeat] 發送心跳包, 節點: {node_id}...")
        
        if self.mock_mode:
            return {
                "status": "ALIVE",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
        return self._send_request("POST", path, payload)


# ==============================================================================
# 模擬執行流程 (Simulation Workflow)
# ==============================================================================
def run_simulation():
    print("==================================================")
    print("      開始 EAP 設備交握流程模擬 (Mock Mode)       ")
    print("==================================================")
    
    # 建立一個模擬的包膜機 (Wrap) 客戶端
    client = EAPEquipmentClient(
        base_url="http://127.0.0.1:8080", 
        equipment_id="WRAP_01", 
        equipment_type="Wrap", 
        mock_mode=True
    )
    
    wes_task_id = "WES_TASK_20260703_001"
    agv_id = "AGV_01"
    
    # 步驟 0: 發送心跳
    hb_resp = client.send_heartbeat(node_id=agv_id)
    print(f"<- Response: {json.dumps(hb_resp, ensure_ascii=False)}")
    time.sleep(0.5)

    # 步驟 1: AGV 抵達，申請進入設備放貨 (purpose_mode=1: 預包膜)
    if client.request_enter(wes_id=wes_task_id, purpose_mode=1) == "OK":
        print("\n>>> AGV 進入干涉區，執行放貨作業...")
        time.sleep(0.5)  # 模擬放貨物理時間
        print(">>> AGV 完成放貨，退回安全區域。")
        
        # 步驟 2: 通知準備完成 (同步等待機台接手)
        if client.preparation_complete(wes_id=wes_task_id, purpose_mode=1) == "OK":
            # 步驟 3: 同步等待設備處理結果並接手 (預設 sleep 10 秒)
            if client.result_query_takeover(wes_id=wes_task_id, purpose_mode=1) == "OK":
                print("\n>>> 設備處理完成且資源已釋放。AGV 準備重新進入接手取貨...")
                
                # 步驟 4: 重新申請進入取貨 (purpose_mode=3: 單板進出)
                if client.request_enter(wes_id=wes_task_id, purpose_mode=3) == "OK":
                    print("\n>>> AGV 重新進入干涉區，執行取貨作業...")
                    time.sleep(0.5)  # 模擬取貨物理時間
                    print(">>> AGV 完成取貨，攜帶貨物退出安全區域。")
                    
                    # 步驟 5: 通知取貨完成
                    client.preparation_complete(wes_id=wes_task_id, purpose_mode=3)
                    print("\n>>> 任務交握流程順利結束，釋放設備資源。")
                else:
                    print("設備拒絕再次進入，停止模擬。")
            else:
                print("等待設備處理結果失敗。")
        else:
            print("機台接手失敗。")
    else:
        print("設備拒絕進入，停止模擬。")

if __name__ == "__main__":
    run_simulation()

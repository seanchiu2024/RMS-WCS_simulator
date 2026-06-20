import os
import sys
import json
import datetime
import http.server
import urllib.request
import urllib.error
import threading
import time
import logging

import config

# 配置 Logging 同時輸出至 Console 與檔案
log_file = config.RMS_LOG_FILE
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def get_timestamp():
    """取得當下符合規定的 timestamp 格式 (YYYY-MM-DD HH:MM:SS.mmm)"""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // 1000:03d}"

def send_post_request(url, payload):
    """使用內建 urllib 發送 POST 請求"""
    data = json.dumps(payload, indent=2, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    try:
        # 使用設定檔中的 Request 超時時間
        with urllib.request.urlopen(req, timeout=config.REQUEST_TIMEOUT) as response:
            res_body = response.read().decode('utf-8')
            logging.info(f"HTTP POST 成功 -> {url}\n回應狀態: {response.status}\n回應內容:\n{res_body}")
            return True, res_body
    except urllib.error.HTTPError as e:
        res_body = e.read().decode('utf-8') if e else ""
        logging.error(f"HTTP POST 失敗 -> {url} [HTTP {e.code} - {e.reason}]\n回應內容:\n{res_body}")
        return False, f"HTTPError {e.code}"
    except Exception as e:
        logging.error(f"HTTP POST 連線失敗 -> {url}: {e}")
        return False, str(e)

# 用於 online 狀態上報的序號計數器
online_sequence_counter = 0

def send_online_status(wcs_url, status="remote"):
    """向 WCS 發送 RMS 上線狀態"""
    global online_sequence_counter
    online_sequence_counter += 1
    seq = f"{online_sequence_counter:06d}"
    
    payload = {
        "protocol_version": "2.0",
        "sequence": seq,
        "timestamp": get_timestamp(),
        "priority": "128",
        "device": "RMS01",
        "status": status
    }
    url = f"{wcs_url}/awd/rms/online"
    logging.info(f"\n[主動上報] 向 WCS 發送上線狀態 (status: {status})...")
    send_post_request(url, payload)

class MissionManager:
    """任務狀態管理與執行狀態機"""
    def __init__(self, wcs_url):
        self.wcs_url = wcs_url
        self.active_mission = None
        self.active_thread = None
        self.lock = threading.Lock()
        
        # 用於等待 WCS ACK 的同步信號與變數
        self.ack_event = threading.Event()
        self.expected_action = None
        self.expected_sequence = None
        self.ack_status = None

    def start_mission(self, request_data):
        with self.lock:
            # 檢查是否有正在執行中的任務
            if self.active_thread and self.active_thread.is_alive():
                logging.warning("目前已有任務正在執行中，拒絕新的任務請求。")
                return False, "Mission already in progress"
            
            self.active_mission = request_data
            self.ack_event.clear()
            self.expected_action = None
            self.expected_sequence = None
            self.ack_status = None
            
            # 啟動狀態機執行緒
            self.active_thread = threading.Thread(target=self._run_mission, daemon=True)
            self.active_thread.start()
            return True, "NA"

    def _run_mission(self):
        mission = self.active_mission
        seq = mission.get("sequence", "UNKNOWN")
        priority = mission.get("priority", "128")
        sub_missions = mission.get("sub_missions", [])
        
        logging.info(f"==================================================")
        logging.info(f"[狀態機啟動] 任務序號: {seq}, 共 {len(sub_missions)} 個子任務。")
        logging.info(f"==================================================")
        
        for idx, sub in enumerate(sub_missions):
            space = sub.get("space")
            action = sub.get("action")
            
            # load 動作的回覆 reason 帶設定檔中的棧板 ID，其他均為 "NA"
            reason = config.DEFAULT_PALLET_ID if action == "load" else "NA"
            
            # 準備任務執行結果 payload
            result_payload = {
                "protocol_version": "2.0",
                "sequence": seq,
                "timestamp": get_timestamp(),
                "priority": priority,
                "space": space,
                "action": action,
                "result": "OK",
                "reason": reason
            }
            
            # 發送執行結果至 WCS
            url = f"{self.wcs_url}/awd/rms/set_mission_result"
            logging.info(f"\n[任務步驟 {idx+1}/{len(sub_missions)}] 發送任務執行結果 ({action}於{space})...")
            
            # 設定預期要收到的 ACK 資訊
            self.expected_sequence = seq
            self.expected_action = action
            self.ack_event.clear()
            
            # 發送 API 請求
            send_post_request(url, result_payload)
            
            # 開始等待 WCS 回傳 set_mission_ack
            logging.info(f"[任務步驟 {idx+1}/{len(sub_missions)}] 等待 WCS 發送 ACK (action='{action}')...")
            
            # 使用設定檔中的 ACK 等待超時
            acked = self.ack_event.wait(timeout=config.ACK_TIMEOUT)
            if not acked:
                logging.error(f"[超時錯誤] 超過 {config.ACK_TIMEOUT} 秒未收到 WCS ACK (action='{action}')！任務終止。")
                return
            
            if self.ack_status != "OK":
                logging.error(f"[狀態錯誤] 收到非 OK 的 ACK 狀態: '{self.ack_status}'！任務終止。")
                return
            
            logging.info(f"[步驟確認] 成功收到 WCS ACK (action='{action}')。")
            
            # 若不是最後一個子任務，則於收到 ACK 後，等待設定檔中的延遲秒數再發送下一個 result
            if idx < len(sub_missions) - 1:
                logging.info(f"[延遲等待] 依照規範，等待 {config.STEP_DELAY} 秒後再執行下一步子任務...")
                time.sleep(config.STEP_DELAY)
                
        logging.info(f"==================================================")
        logging.info(f"[任務完成] 任務 {seq} 搬運執行完成！")
        logging.info(f"==================================================")

    def receive_ack(self, ack_data):
        seq = ack_data.get("sequence")
        action = ack_data.get("action")
        ack = ack_data.get("ack")
        
        # 比對是否為目前步驟正在等待的 ACK
        if seq == self.expected_sequence and action == self.expected_action:
            self.ack_status = ack
            self.ack_event.set()
            return True, "ACK matched"
        else:
            msg = f"未預期的 ACK 或非目前等待的步驟 (收到: seq={seq}, action={action} | 預期: seq={self.expected_sequence}, action={self.expected_action})"
            logging.warning(msg)
            return False, msg

# 建立全域 MissionManager 實體 (預設呼叫 config.py 設定的 WCS 服務)
WCS_BASE_URL = f"http://{config.WCS_HOST}:{config.WCS_PORT}"
mission_manager = MissionManager(WCS_BASE_URL)

class RMSRequestHandler(http.server.BaseHTTPRequestHandler):
    """處理 HTTP 請求"""
    def log_message(self, format, *args):
        # 覆寫此方法以避免 http.server 內建 log干擾我們配置的 logger
        pass

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # 格式化紀錄 incoming request log
        local_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        logging.info(f"\n======== 接收到 POST 請求 ========")
        logging.info(f"時間: {local_time}")
        logging.info(f"端點: {self.path}")
        logging.info(f"方法: POST")
        logging.info(f"Body 內容:\n{post_data}")
        logging.info(f"==================================")

        try:
            payload = json.loads(post_data) if post_data else {}
        except json.JSONDecodeError:
            self.send_error_response(400, "無效的 JSON 格式")
            return

        if self.path == "/awd/rms/set_mission_request":
            self.handle_set_mission_request(payload)
        elif self.path == "/awd/rms/set_mission_ack":
            self.handle_set_mission_ack(payload)
        else:
            self.send_error_response(404, "找不到此端點")

    def handle_set_mission_request(self, payload):
        seq = payload.get("sequence")
        priority = payload.get("priority", "128")
        protocol_version = payload.get("protocol_version", "2.0")
        
        if not seq:
            self.send_error_response(400, "缺少必要欄位 'sequence'")
            return

        # 啟動任務狀態機
        success, reason = mission_manager.start_mission(payload)
        reply_val = "ACK" if success else "NAK"
        
        # 準備即時的 HTTP 同步回覆 payload
        reply_payload = {
            "protocol_version": protocol_version,
            "sequence": seq,
            "timestamp": get_timestamp(),
            "priority": priority,
            "reply": reply_val,
            "sub_missions": [],
            "reason": reason
        }
        
        status_code = 200 if success else 400
        self.send_json_response(status_code, reply_payload)

    def handle_set_mission_ack(self, payload):
        success, msg = mission_manager.receive_ack(payload)
        reply_payload = {
            "status": "success" if success else "error",
            "message": msg
        }
        status_code = 200 if success else 400
        self.send_json_response(status_code, reply_payload)

    def send_json_response(self, status_code, data):
        response_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)
        logging.info(f"已回覆響應 [{status_code}]:\n{json.dumps(data, indent=2, ensure_ascii=False)}")

    def send_error_response(self, status_code, message):
        reply_payload = {
            "status": "error",
            "message": message
        }
        self.send_json_response(status_code, reply_payload)

def run_server(port):
    # 使用 ThreadingHTTPServer 以處理高併發/多執行緒請求
    server_address = ('', port)
    httpd = http.server.ThreadingHTTPServer(server_address, RMSRequestHandler)
    logging.info(f"==================================================")
    logging.info(f"RMS 模擬伺服器已啟動，監聽 Port: {port} ...")
    logging.info(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("RMS 伺服器正在關閉...")
        httpd.server_close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RMS 模擬器服務")
    parser.add_argument("--port", type=int, default=config.RMS_PORT, help="RMS 監聽的 Port")
    parser.add_argument("--wcs-host", type=str, default=config.WCS_HOST, help="WCS 服務 Host")
    parser.add_argument("--wcs-port", type=int, default=config.WCS_PORT, help="WCS 服務 Port")
    args = parser.parse_args()
    
    # 根據參數或設定檔更新 WCS URL
    mission_manager.wcs_url = f"http://{args.wcs_host}:{args.wcs_port}"
    
    # 啟動後背景延遲 1.5 秒自動發送 RMS 上線狀態給 WCS
    def trigger_online_on_startup(wcs_url):
        time.sleep(1.5)
        try:
            send_online_status(wcs_url, "remote")
        except Exception as e:
            logging.error(f"啟動時自動發送上線狀態失敗: {e}")
            
    threading.Thread(target=trigger_online_on_startup, args=(mission_manager.wcs_url,), daemon=True).start()

    run_server(args.port)

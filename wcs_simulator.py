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
log_file = config.WCS_LOG_FILE
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

# 全域設定，預設連線到設定檔中定義的 RMS 服務
RMS_BASE_URL = f"http://{config.RMS_HOST}:{config.RMS_PORT}"

class WCSRequestHandler(http.server.BaseHTTPRequestHandler):
    """處理 HTTP 請求"""
    def log_message(self, format, *args):
        # 覆寫此方法以避免 http.server 內建 log 干擾我們配置的 logger
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

        if self.path == "/awd/rms/set_mission_result":
            self.handle_set_mission_result(payload)
        elif self.path == "/awd/rms/online":
            self.handle_online(payload)
        else:
            self.send_error_response(404, "找不到此端點")

    def handle_set_mission_result(self, payload):
        seq = payload.get("sequence")
        action = payload.get("action")
        priority = payload.get("priority", "128")
        protocol_version = payload.get("protocol_version", "2.0")
        
        if not seq or not action:
            self.send_error_response(400, "缺少必要欄位 'sequence' 或 'action'")
            return

        # 立即同步回覆已接收到任務結果
        reply_payload = {
            "status": "success",
            "message": f"成功收到步驟 {action} 的結果"
        }
        self.send_json_response(200, reply_payload)
        
        # 開啟背景執行緒，依設定時間非同步延遲後，發送 ACK 給 RMS
        threading.Thread(
            target=self.send_ack_to_rms,
            args=(seq, action, priority, protocol_version),
            daemon=True
        ).start()

    def handle_online(self, payload):
        device = payload.get("device", "UNKNOWN")
        status = payload.get("status", "UNKNOWN")
        logging.info(f"收到 RMS 上線狀態報告 -> 設備: {device}, 狀態: {status}")
        
        reply_payload = {
            "status": "success",
            "message": f"成功收到 {device} 的上線狀態: {status}"
        }
        self.send_json_response(200, reply_payload)

    def send_ack_to_rms(self, seq, action, priority, protocol_version):
        logging.info(f"\n[等待延遲] 依設定於發送 ACK 前，先等待 {config.ACK_DELAY} 秒...")
        time.sleep(config.ACK_DELAY)
        ack_payload = {
            "protocol_version": protocol_version,
            "sequence": seq,
            "timestamp": get_timestamp(),
            "priority": priority,
            "action": action,
            "ack": "OK"
        }
        url = f"{RMS_BASE_URL}/awd/rms/set_mission_ack"
        logging.info(f"\n[發送確認] 非同步發送 ACK (action='{action}') 給 RMS...")
        send_post_request(url, ack_payload)

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

def start_http_server(port):
    server_address = ('', port)
    httpd = http.server.ThreadingHTTPServer(server_address, WCSRequestHandler)
    logging.info(f"WCS 模擬伺服器已啟動，監聽 Port: {port} ...")
    try:
        httpd.serve_forever()
    except Exception as e:
        logging.error(f"WCS 伺服器異常終止: {e}")

def trigger_test_mission(seq="M1000001"):
    """發送搬運任務請求給 RMS"""
    # 預設任務步驟 (A-01-2 ➜ L-01-0)
    sub_missions = [
        {"space": "A-01-2", "action": "start"},
        {"space": "A-01-2", "action": "load"},
        {"space": "L-01-0", "action": "unload"},
        {"space": "L-01-0", "action": "end"}
    ]
    priority = "128"
    
    # 嘗試從同目錄下的 mission.json 讀取自訂任務組合
    config_file = "mission.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                custom_data = json.load(f)
                if "sub_missions" in custom_data:
                    sub_missions = custom_data["sub_missions"]
                    logging.info(f"成功自 {config_file} 載入自訂子任務組合，共 {len(sub_missions)} 個步驟。")
                if "priority" in custom_data:
                    priority = str(custom_data["priority"])
        except Exception as e:
            logging.error(f"讀取 {config_file} 失敗，使用預設任務。錯誤: {e}")

    mission_payload = {
      "protocol_version": "2.0",
      "sequence": seq,
      "timestamp": get_timestamp(),
      "priority": priority,
      "sub_missions": sub_missions
    }
    url = f"{RMS_BASE_URL}/awd/rms/set_mission_request"
    logging.info(f"\n[主動派工] 向 RMS 發送任務請求 (sequence: {seq})...")
    send_post_request(url, mission_payload)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WCS 模擬器與測試工具")
    parser.add_argument("--port", type=int, default=config.WCS_PORT, help="WCS 監聽的 Port")
    parser.add_argument("--rms-host", type=str, default=config.RMS_HOST, help="RMS 服務 Host")
    parser.add_argument("--rms-port", type=int, default=config.RMS_PORT, help="RMS 服務 Port")
    args = parser.parse_args()
    
    RMS_BASE_URL = f"http://{args.rms_host}:{args.rms_port}"

    # 在背景執行緒啟動 WCS HTTP 伺服器
    server_thread = threading.Thread(target=start_http_server, args=(args.port,), daemon=True)
    server_thread.start()
    
    # 稍等一下確保伺服器印出啟動訊息
    time.sleep(0.5)

    print("\n" + "="*60)
    print(" 互動指令選單:")
    print(" - 輸入 'send'  : 發送預設的 A-01-2 -> L-01-0 搬運任務 (seq: M1000001)")
    print(" - 輸入 'send <序號>' : 發送自訂序號 the 搬運任務 (例如: send M20260619)")
    print(" - 輸入 'exit'  : 退出程式")
    print("="*60 + "\n")

    try:
        while True:
            # 由於 logging 會寫入 stdout，我們使用 sys.stdout.write 與 flush 提供一個提示符
            sys.stdout.write("WCS> ")
            sys.stdout.flush()
            user_input = sys.stdin.readline().strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'exit':
                logging.info("結束 WCS 模擬器。")
                break
            elif user_input.lower() == 'send':
                trigger_test_mission()
            elif user_input.lower().startswith('send '):
                parts = user_input.split(maxsplit=1)
                custom_seq = parts[1] if len(parts) > 1 else "M1000001"
                trigger_test_mission(custom_seq)
            else:
                print("無法辨識的指令，請輸入 'send'、'send <序號>' 或 'exit'")
    except KeyboardInterrupt:
        logging.info("WCS 模擬器正在關閉...")

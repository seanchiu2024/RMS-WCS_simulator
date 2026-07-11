import os
import sys
import csv
import json
import datetime
import http.server
import urllib.request
import urllib.error
import threading
import time
import logging
import queue

# 將 AGV_mission 加入 path，以便 import generate_mission
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "AGV_mission"))
from generate_mission import generate_mission
import config

# 全域佇列
received_results_queue = queue.Queue()

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
        with urllib.request.urlopen(req, timeout=config.REQUEST_TIMEOUT) as response:
            res_body = response.read().decode('utf-8')
            logging.info(f"HTTP POST 成功 -> {url}\n回應狀態: {response.status}\n回應內容: {res_body.strip()}")
            return True, res_body
    except urllib.error.HTTPError as e:
        res_body = e.read().decode('utf-8') if e else ""
        logging.error(f"HTTP POST 失敗 -> {url} [HTTP {e.code} - {e.reason}]\n回應內容: {res_body.strip()}")
        return False, f"HTTPError {e.code}"
    except Exception as e:
        logging.error(f"HTTP POST 連線失敗 -> {url}: {e}")
        return False, str(e)

# 設備與服務連線端點設定
RMS_BASE_URL = f"http://localhost:{config.RMS_PORT}"
EAP_BASE_URL = "http://localhost:8000"

# 載入等待點與設備對照表
def load_lookup_table():
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AGV_mission", "hs_lookup_table.csv")
    lookup = {}
    if not os.path.exists(csv_path):
        logging.warning(f"找不到對照表檔案: {csv_path}")
        return lookup
    try:
        try:
            with open(csv_path, mode='r', encoding='utf-8-sig', errors='ignore') as f:
                rows = list(csv.DictReader(f))
        except UnicodeDecodeError:
            with open(csv_path, mode='r', encoding='cp950', errors='ignore') as f:
                rows = list(csv.DictReader(f))

        for row in rows:
            pid = row.get('point_id', '').strip()
            wpid = row.get('wait_point_id', '').strip()
            eqtype = row.get('equipment_type', '').strip()
            if wpid:
                lookup[wpid] = {
                    "point_id": pid,
                    "equipment_type": eqtype
                }
        logging.info(f"成功載入 {len(lookup)} 筆設備交握點位資料。")
    except Exception as e:
        logging.error(f"讀取對照表失敗: {e}")
    return lookup

hs_lookup_table = load_lookup_table()

# 追蹤與管理正在進行的任務狀態
active_missions = {}

class WCSRequestHandler(http.server.BaseHTTPRequestHandler):
    """處理 HTTP 請求"""
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        logging.info(f"\n[HTTP Server] 接收到來自 RMS 的 POST 請求 - {self.path}")
        
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

        reply_payload = {
            "status": "success",
            "message": f"成功收到步驟 {action} 的結果"
        }
        self.send_json_response(200, reply_payload)
        
        # 放入結果佇列中供主迴圈處理設備交握與 ACK
        received_results_queue.put({
            "sequence": seq,
            "action": action,
            "space": payload.get("space", "UNKNOWN"),
            "result": payload.get("result", "UNKNOWN"),
            "reason": payload.get("reason", "NA"),
            "priority": priority,
            "protocol_version": protocol_version
        })

    def handle_online(self, payload):
        device = payload.get("device", "UNKNOWN")
        status = payload.get("status", "UNKNOWN")
        logging.info(f"收到 RMS 上線狀態報告 -> 設備: {device}, 狀態: {status}")
        self.send_json_response(200, {"status": "success", "message": "online status received"})

    def send_json_response(self, status_code, data):
        response_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def send_error_response(self, status_code, message):
        self.send_json_response(status_code, {"status": "error", "message": message})

def start_http_server(port):
    server_address = ('', port)
    httpd = http.server.ThreadingHTTPServer(server_address, WCSRequestHandler)
    logging.info(f"WCS 模擬伺服器已啟動，監聽 Port: {port} ...")
    try:
        httpd.serve_forever()
    except Exception as e:
        logging.error(f"WCS 伺服器異常終止: {e}")

# Web API 交握功能呼叫
def call_request_enter(equipment_type, wes_id, purpose_mode):
    url = f"{EAP_BASE_URL}/api/request-enter"
    payload = {
        "equipment_type": equipment_type,
        "wes_id": wes_id,
        "purpose_mode": purpose_mode
    }
    logging.info(f"[EAP 交握] 正在呼叫 request-enter -> 設備: {equipment_type}, ID: {wes_id}, 目的模式: {purpose_mode}...")
    success, res = send_post_request(url, payload)
    return success

def call_preparation_complete(equipment_type, wes_id, purpose_mode):
    url = f"{EAP_BASE_URL}/api/preparation-complete"
    payload = {
        "equipment_type": equipment_type,
        "wes_id": wes_id,
        "purpose_mode": purpose_mode
    }
    logging.info(f"[EAP 交握] 正在呼叫 preparation-complete -> 設備: {equipment_type}, ID: {wes_id}, 目的模式: {purpose_mode}...")
    success, res = send_post_request(url, payload)
    return success

def call_result_query_takeover(equipment_type, wes_id, purpose_mode):
    url = f"{EAP_BASE_URL}/api/result-query-takeover"
    payload = {
        "equipment_type": equipment_type,
        "wes_id": wes_id,
        "purpose_mode": purpose_mode
    }
    logging.info(f"[EAP 交握] 正在呼叫 result-query-takeover -> 設備: {equipment_type}, ID: {wes_id}, 目的模式: {purpose_mode}...")
    success, res = send_post_request(url, payload)
    return success

def send_ack_to_rms(seq, action, priority, protocol_version):
    ack_payload = {
        "protocol_version": protocol_version,
        "sequence": seq,
        "timestamp": get_timestamp(),
        "priority": priority,
        "action": action,
        "ack": "OK"
    }
    url = f"{RMS_BASE_URL}/awd/rms/set_mission_ack"
    logging.info(f"[WCS 發送 ACK] 任務: {seq}, action: {action}, 狀態: OK")
    send_post_request(url, ack_payload)

# 執行任務派發
def trigger_move_mission(sourcepoint, targetpoint):
    sequence = f"M_MOVE_{datetime.datetime.now().strftime('%y%m%d%H%M%S')}"
    
    # 1. 呼叫 generate_mission 產生任務資訊
    mission_data = generate_mission(sourcepoint, targetpoint, sequence=sequence)
    logging.info(f"\n[任務生成] 成功生成 MOVE 任務 (起點: {sourcepoint}, 終點: {targetpoint}, 序號: {sequence})")
    
    # 解析該任務的 waiting points
    # generate_mission 會讀取並對照 hs_lookup_table.csv
    # 我們也需要載入對照表以查出 sourcepoint_W 與 targetpoint_W 供交握判斷
    csv_lookup = {}
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AGV_mission", "hs_lookup_table.csv")
    if os.path.exists(csv_path):
        try:
            try:
                with open(csv_path, mode='r', encoding='utf-8-sig', errors='ignore') as f:
                    rows = list(csv.DictReader(f))
            except UnicodeDecodeError:
                with open(csv_path, mode='r', encoding='cp950', errors='ignore') as f:
                    rows = list(csv.DictReader(f))
            for row in rows:
                pid = row.get('point_id', '').strip()
                wpid = row.get('wait_point_id', '').strip()
                csv_lookup[pid] = wpid
        except Exception as e:
            logging.error(f"在任務發送時讀取對照表失敗: {e}")
                
    sourcepoint_W = csv_lookup.get(sourcepoint)
    targetpoint_W = csv_lookup.get(targetpoint)
    
    # 初始化 active_missions 記錄
    active_missions[sequence] = {
        "sourcepoint": sourcepoint,
        "targetpoint": targetpoint,
        "sourcepoint_W": sourcepoint_W,
        "targetpoint_W": targetpoint_W,
        "counters": {},
        "completed": False
    }
    
    logging.info(f"等待點解析成果 -> 起點等待點: {sourcepoint_W}, 終點等待點: {targetpoint_W}")
    logging.info(f"子任務步驟明細:")
    for idx, sub in enumerate(mission_data["sub_missions"]):
        logging.info(f"  步驟 {idx+1}: space='{sub['space']}', action='{sub['action']}'")
        
    # 發送任務給 RMS
    mission_data["protocol_version"] = "2.0"
    url = f"{RMS_BASE_URL}/awd/rms/set_mission_request"
    logging.info(f"[主動派工] 向 RMS 發送 MOVE 任務...")
    send_post_request(url, mission_data)
    return sequence

# 四種測試情境列表
TEST_SCENARIOS = [
    {
        "name": "情境 1: 起點有 WP (IPT_101) -> 終點有 WP (OPT_101)",
        "source": "IPT_101",
        "target": "OPT_101"
    },
    {
        "name": "情境 2: 起點有 WP (IPT_101) -> 終點無 WP (ARE_101)",
        "source": "IPT_101",
        "target": "ARE_101"
    },
    {
        "name": "情境 3: 起點無 WP (ARE_101) -> 終點有 WP (IPT_101)",
        "source": "ARE_101",
        "target": "IPT_101"
    },
    {
        "name": "情境 4: 起點無 WP (ARE_101) -> 終點無 WP (ARE_102)",
        "source": "ARE_101",
        "target": "ARE_102"
    }
]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WCS MOVE 任務與交握工具")
    parser.add_argument("sourcepoint", nargs="?", default=None, help="來源點位 (起點)")
    parser.add_argument("targetpoint", nargs="?", default=None, help="目標點位 (終點)")
    parser.add_argument("--rms-host", default="localhost", help="RMS 伺服器 Host (預設為 localhost)")
    args = parser.parse_args()

    # 動態設定 RMS Server URL
    RMS_BASE_URL = f"http://{args.rms_host}:{config.RMS_PORT}"

    # 啟動 WCS HTTP Server 接收 RMS 狀態上報
    server_thread = threading.Thread(target=start_http_server, args=(config.WCS_PORT,), daemon=True)
    server_thread.start()
    time.sleep(0.5)

    single_mode = args.sourcepoint is not None and args.targetpoint is not None

    print("\n" + "="*70)
    if single_mode:
        print(f" move.py 單次搬送任務啟動：{args.sourcepoint} -> {args.targetpoint}")
    else:
        print(" move.py 自動化測試控制台已啟動！")
        print(" 本測試將依序驗證 4 種有/無 Waiting Point 的搭配組合。")
    print(f" RMS 伺服器設定為：{RMS_BASE_URL}")
    print(" 請確保 RMS 模擬器 (rms_simulator.py) 與 EAP Web 服務已啟動。")
    print("="*70 + "\n")

    current_idx = 0
    current_seq = None

    if single_mode:
        current_seq = trigger_move_mission(args.sourcepoint, args.targetpoint)
    else:
        # 發送第一個情境
        scenario = TEST_SCENARIOS[current_idx]
        logging.info(f"\n>>>>>>> 開始測試 {scenario['name']} <<<<<<<")
        current_seq = trigger_move_mission(scenario["source"], scenario["target"])

    try:
        while True:
            try:
                # 阻塞獲取來自 RMS 的執行結果
                res = received_results_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            seq = res["sequence"]
            action = res["action"]
            space = res["space"]
            result = res["result"]

            logging.info(f"\n[重要節點] 接收任務執行結果 -> 序號={seq}, 動作={action}, 位置={space}, 結果={result}")

            # 只有在有註冊 active_missions 的任務才進行交握處理
            if seq in active_missions:
                mission_info = active_missions[seq]

                if action == "idle":
                    # 累計當前 space 的交握次數
                    counters = mission_info["counters"]
                    counters[space] = counters.get(space, 0) + 1
                    count = counters[space]

                    # 根據 space 決定 purpose_mode (起點 2，終點 1)
                    if space == mission_info["sourcepoint_W"]:
                        purpose_mode = 2
                    elif space == mission_info["targetpoint_W"]:
                        purpose_mode = 1
                    else:
                        purpose_mode = 1  # 預設模式

                    # 查詢對照表，獲取 equipment_type 與 wes_id
                    hs_info = hs_lookup_table.get(space)
                    if hs_info:
                        equipment_type = hs_info["equipment_type"]
                        wes_id = hs_info["point_id"]
                    else:
                        equipment_type = "Station"
                        wes_id = space

                    logging.info(f"[設備交握判定] 位置 '{space}' 的第 {count} 次交握. 目的模式: {purpose_mode}")
                    
                    try:
                        if count == 1:
                            # 進入申請
                            call_request_enter(equipment_type, wes_id, purpose_mode)
                        elif count == 2:
                            # 完工與釋放確認
                            call_preparation_complete(equipment_type, wes_id, purpose_mode)
                            call_result_query_takeover(equipment_type, wes_id, purpose_mode)
                    except Exception as ex:
                        logging.error(f"[設備交握異常] 呼叫 Web API 錯誤 (但將繼續發送 ACK 回應以維持測試流暢): {ex}")

                # 發送確認 ACK 給 RMS
                send_ack_to_rms(seq, action, res["priority"], res["protocol_version"])

                # 當任務執行至 end 時，表示該任務成功完成
                if action == "end":
                    active_missions[seq]["completed"] = True
                    
                    if single_mode:
                        logging.info(f"\n>>>>>>> 單次搬送任務 {args.sourcepoint} -> {args.targetpoint} 已順利完成！ <<<<<<<\n")
                        break
                    else:
                        logging.info(f"\n>>>>>>> 成功完成 {TEST_SCENARIOS[current_idx]['name']} 測試！ <<<<<<<\n")
                        # 延遲 3 秒後進行下一個情境
                        current_idx += 1
                        if current_idx < len(TEST_SCENARIOS):
                            time.sleep(3.0)
                            scenario = TEST_SCENARIOS[current_idx]
                            logging.info(f"\n>>>>>>> 開始測試 {scenario['name']} <<<<<<<")
                            current_seq = trigger_move_mission(scenario["source"], scenario["target"])
                        else:
                            logging.info("\n" + "="*70)
                            logging.info(" 恭喜！所有 4 種搬送交握情境已全部測試完成！")
                            logging.info("="*70 + "\n")
                            break

    except KeyboardInterrupt:
        logging.info("測試程式已手動終止。")

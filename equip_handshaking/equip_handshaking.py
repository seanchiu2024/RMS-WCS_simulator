import time
import logging

# ==============================================================================
# 配置 Logger (同時記錄到 handshaking.log 與 Console)
# ==============================================================================
logger = logging.getLogger("handshaking")
logger.setLevel(logging.INFO)

# 避免重複添加 handlers
if not logger.handlers:
    # 檔案 Handler (有時間戳記與日誌等級格式)
    fh = logging.FileHandler("handshaking.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

    # 控制台 Handler (保持原本乾淨的模擬輸出)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(ch)


def request_enter(equipment_type: str, wes_id: str, purpose_mode: int, **kwargs) -> str:
    """
    ［1］ 申請進入設備 (Request Enter)
    :param equipment_type: 設備類型 (Wrap, Check, Aligner, PalletSupply, ASRS_IPORT, ASRS_OPORT, LIFT, Station)
    :param wes_id: WES_ID
    :param purpose_mode: 申請目的模式
    :param kwargs: 機台特有引數，如 pallet_no (str), cargo_height (str), rack_in_place (bool), op_mode (int)
    :return: "OK" 或 "WAIT"
    """
    pallet_no = kwargs.get("pallet_no", "")
    cargo_height = kwargs.get("cargo_height", "")
    rack_in_place = kwargs.get("rack_in_place", False)
    op_mode = kwargs.get("op_mode", 1)

    logger.info(f"\n[RequestEnter] 申請進入設備 ({equipment_type}) ID: {wes_id}, 目的模式: {purpose_mode}...")
    if kwargs:
        logger.info(f"  -> 攜帶參數: pallet_no={pallet_no}, cargo_height={cargo_height}, rack_in_place={rack_in_place}, op_mode={op_mode}")

    match equipment_type:
        case "Wrap":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [Wrap] 包膜機 (1: Pre_Wrap 進入)，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case 2:
                    logger.info("  -> [Match-Case] [Wrap] 包膜機 (2: Full_Wrap 進入)，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case 3:
                    logger.info("  -> [Match-Case] [Wrap] 包膜機 (3: 完工取貨)，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case _:
                    logger.info(f"  -> [Match-Case] [Wrap] 未知模式 {purpose_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"

        case "Check":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [Check] 檢驗設備 (1: 檢測進出)，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case _:
                    logger.info(f"  -> [Match-Case] [Check] 未知模式 {purpose_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"

        case "Aligner":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [Aligner] 糾偏機 (1: 入料申請)，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case 2:
                    logger.info("  -> [Match-Case] [Aligner] 糾偏機 (2: 出料申請)，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case _:
                    logger.info(f"  -> [Match-Case] [Aligner] 未知模式 {purpose_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"

        case "PalletSupply":
            match purpose_mode:
                case 1:
                    logger.info(f"  -> [Match-Case] [PalletSupply] 棧板供收機 (1: 取單板)，驗證參數: op_mode={op_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case 2:
                    logger.info(f"  -> [Match-Case] [PalletSupply] 棧板供收機 (2: 收單板)，驗證參數: op_mode={op_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case 3:
                    logger.info(f"  -> [Match-Case] [PalletSupply] 棧板供收機 (3: 供滿版)，驗證參數: op_mode={op_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case 4:
                    logger.info(f"  -> [Match-Case] [PalletSupply] 棧板供收機 (4: 收滿版)，驗證參數: op_mode={op_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case _:
                    logger.info(f"  -> [Match-Case] [PalletSupply] 未知模式 {purpose_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"

        case "ASRS_IPORT":
            match purpose_mode:
                case 1:
                    logger.info(f"  -> [Match-Case] [ASRS_IPORT] 入口區 (1: 進入放貨-滿架)，驗證參數: PalletNo={pallet_no}, 貨物高度={cargo_height}, 空架到位={rack_in_place}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case 2:
                    logger.info("  -> [Match-Case] [ASRS_IPORT] 入口區 (2: 進入載空架離開)，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case _:
                    logger.info(f"  -> [Match-Case] [ASRS_IPORT] 未知模式 {purpose_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"

        case "ASRS_OPORT":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [ASRS_OPORT] 出口區 (1: 進入取貨-滿架)，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case 2:
                    logger.info(f"  -> [Match-Case] [ASRS_OPORT] 出口區 (2: 進入放空架)，驗證參數: 空架到位={rack_in_place}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case _:
                    logger.info(f"  -> [Match-Case] [ASRS_OPORT] 未知模式 {purpose_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"

        case "LIFT":
            match purpose_mode:
                case 1:
                    logger.info(f"  -> [Match-Case] [LIFT] 提升機 (1: 放貨)，驗證參數: PalletNo={pallet_no}, 貨物高度={cargo_height}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case 2:
                    logger.info("  -> [Match-Case] [LIFT] 提升機 (2: 取貨)，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case _:
                    logger.info(f"  -> [Match-Case] [LIFT] 未知模式 {purpose_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"

        case "Station":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [Station] 手臂棧板位 (1: 入料到位感測)，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case 2:
                    logger.info("  -> [Match-Case] [Station] 手臂棧板位 (2: 出料釋放資源)，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"
                case _:
                    logger.info(f"  -> [Match-Case] [Station] 未知模式 {purpose_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    return "OK"

        case _:
            logger.info(f"  -> [Match-Case] 未知設備類型 {equipment_type}，預設模擬等待 3 秒...")
            time.sleep(3)
            return "OK"


def preparation_complete(equipment_type: str, wes_id: str, purpose_mode: int) -> str:
    """
    ［2］ 準備完成通知 (Preparation Complete) - 同步式等待
    :param equipment_type: 設備類型 (Wrap, Check, Aligner, PalletSupply, ASRS_IPORT, ASRS_OPORT, LIFT, Station)
    :param wes_id: WES_ID
    :param purpose_mode: 申請目的模式
    :return: "OK" 或 "WAIT"
    """
    logger.info(f"\n[PreparationComplete] 設備 ({equipment_type}) ID: {wes_id}, 目的模式: {purpose_mode} 準備完成通知，等待確認...")
    match equipment_type:
        case "Wrap":
            match purpose_mode:
                case 1 | 2 | 3:
                    logger.info(f"  -> [Match-Case] [Wrap] 準備完成通知 (模式 {purpose_mode})，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"
                case _:
                    logger.info(f"  -> [Match-Case] [Wrap] 準備完成通知 (未知模式 {purpose_mode})，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"

        case "Check":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [Check] 準備完成通知 (模式 1)，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"
                case _:
                    logger.info("  -> [Match-Case] [Check] 未知模式，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"

        case "Aligner":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [Aligner] 準備完成通知 (模式 1: 入料準備完成)，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"
                case 2:
                    logger.info("  -> [Match-Case] [Aligner] 準備完成通知 (模式 2: 出料準備完成)，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"
                case _:
                    logger.info("  -> [Match-Case] [Aligner] 未知模式，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"

        case "PalletSupply":
            match purpose_mode:
                case 1 | 2 | 3 | 4:
                    logger.info(f"  -> [Match-Case] [PalletSupply] 準備完成通知 (模式 {purpose_mode})，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"
                case _:
                    logger.info("  -> [Match-Case] [PalletSupply] 未知模式，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"

        case "ASRS_IPORT":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [ASRS_IPORT] 準備完成通知 (模式 1: 放貨完成)，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"
                case 2:
                    logger.info("  -> [Match-Case] [ASRS_IPORT] 準備完成通知 (模式 2: 載空架離開完成)，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"
                case _:
                    logger.info("  -> [Match-Case] [ASRS_IPORT] 未知模式，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"

        case "ASRS_OPORT":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [ASRS_OPORT] 準備完成通知 (模式 1: 取貨完成)，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"
                case 2:
                    logger.info("  -> [Match-Case] [ASRS_OPORT] 準備完成通知 (模式 2: 放空架完成)，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"
                case _:
                    logger.info("  -> [Match-Case] [ASRS_OPORT] 未知模式，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"

        case "LIFT":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [LIFT] 準備完成通知 (模式 1: 放貨完成)，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"
                case 2:
                    logger.info("  -> [Match-Case] [LIFT] 準備完成通知 (模式 2: 取貨完成)，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"
                case _:
                    logger.info("  -> [Match-Case] [LIFT] 未知模式，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"

        case "Station":
            match purpose_mode:
                case 1 | 2:
                    logger.info(f"  -> [Match-Case] [Station] 準備完成通知 (模式 {purpose_mode})，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"
                case _:
                    logger.info(f"  -> [Match-Case] [Station] 準備完成通知 (未知模式 {purpose_mode})，模擬等待 0.5 秒...")
                    time.sleep(0.5)
                    return "OK"

        case _:
            logger.info(f"  -> [Match-Case] 未知設備 {equipment_type} 準備完成，預設模擬等待 0.5 秒...")
            time.sleep(0.5)
            return "OK"


def result_query_takeover(equipment_type: str, wes_id: str, purpose_mode: int) -> dict:
    """
    ［3］ 等待處理結果並接手 (ResultQuery_TakeOver) - 同步式等待
    :param equipment_type: 設備類型 (Wrap, Check, Aligner, PalletSupply, ASRS_IPORT, ASRS_OPORT, LIFT, Station)
    :param wes_id: WES_ID
    :param purpose_mode: 申請目的模式
    :return: 字典格式結果 (包含 status, palletNo, okNG, highLow, result 等)
    """
    logger.info(f"\n[ResultQuery_TakeOver] 設備 ({equipment_type}) ID: {wes_id}, 目的模式: {purpose_mode} 開始同步等待結果...")
    match equipment_type:
        case "Wrap":
            match purpose_mode:
                case 1 | 2 | 3:
                    logger.info(f"  -> [Match-Case] [Wrap] 開始同步等待結果，模式: {purpose_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    logger.info(f"  -> [Wrap] 作業完成，回報 WES (ID: {wes_id}) 並釋放設備資源。")
                    return {"status": "OK"}
                case _:
                    time.sleep(3)
                    return {"status": "OK"}

        case "Check":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [Check] 開始檢驗同步等待，模式: 1，模擬等待 3 秒...")
                    time.sleep(3)
                    result_data = {
                        "status": "OK",
                        "result": "Checked",
                        "okNG": "OK",
                        "highLow": "Normal",
                        "palletNo": f"PLT_CHECK_{wes_id}"
                    }
                    logger.info(f"  -> [Check] 檢驗作業完成，結果: {result_data}，回報 WES 並釋放資源。")
                    return result_data
                case _:
                    time.sleep(3)
                    return {"status": "OK"}

        case "Aligner":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [Aligner] 開始糾偏同步等待，模式: 1，模擬等待 3 秒...")
                    time.sleep(3)
                    result_data = {
                        "status": "OK",
                        "result": "Aligned",
                        "okNG": "OK",
                        "highLow": "Normal",
                        "palletNo": f"PLT_ALIGN_{wes_id}"
                    }
                    logger.info(f"  -> [Aligner] 糾偏作業完成，結果: {result_data}，回報 WES 並釋放資源。")
                    return result_data
                case 2:
                    logger.info("  -> [Match-Case] [Aligner] 出料同步等待，模式: 2，模擬等待 3 秒...")
                    time.sleep(3)
                    return {"status": "OK"}
                case _:
                    time.sleep(3)
                    return {"status": "OK"}

        case "PalletSupply":
            match purpose_mode:
                case 1 | 2 | 3 | 4:
                    logger.info(f"  -> [Match-Case] [PalletSupply] 開始棧板供收同步等待，模式: {purpose_mode}，模擬等待 3 秒...")
                    time.sleep(3)
                    result_data = {
                        "status": "OK",
                        "palletNo": f"PLT_SUPPLY_BOTTOM_{wes_id}"
                    }
                    logger.info(f"  -> [PalletSupply] 棧板作業完成，結果: {result_data}，回報 WES 並釋放資源。")
                    return result_data
                case _:
                    time.sleep(3)
                    return {"status": "OK"}

        case "ASRS_IPORT":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [ASRS_IPORT] 入庫放貨同步等待，模式: 1，模擬等待 3 秒...")
                    time.sleep(3)
                    logger.info("  -> [ASRS_IPORT] 入庫作業完成，回報 WES 並釋放資源。")
                    return {"status": "OK"}
                case 2:
                    logger.info("  -> [Match-Case] [ASRS_IPORT] 載空架離開同步等待，模式: 2，模擬等待 3 秒...")
                    time.sleep(3)
                    logger.info("  -> [ASRS_IPORT] 作業完成，回報 WES 並釋放資源。")
                    return {"status": "OK"}
                case _:
                    time.sleep(3)
                    return {"status": "OK"}

        case "ASRS_OPORT":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [ASRS_OPORT] 取貨同步等待，模式: 1，模擬等待 3 秒...")
                    time.sleep(3)
                    result_data = {
                        "status": "OK",
                        "palletNo": f"PLT_ASRS_OUT_{wes_id}"
                    }
                    logger.info(f"  -> [ASRS_OPORT] 取貨出庫完成，結果: {result_data}，回報 WES 並釋放出口工位資源。")
                    return result_data
                case 2:
                    logger.info("  -> [Match-Case] [ASRS_OPORT] 放空架同步等待，模式: 2，模擬等待 3 秒...")
                    time.sleep(3)
                    logger.info("  -> [ASRS_OPORT] 空架放置完成，回報 WES 並釋放工位資源。")
                    return {"status": "OK"}
                case _:
                    time.sleep(3)
                    return {"status": "OK"}

        case "LIFT":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [LIFT] 放貨同步等待，模式: 1，模擬等待 3 秒...")
                    time.sleep(3)
                    logger.info("  -> [LIFT] 貨物已送達目標樓層，回報 WES 並釋放提升機資源。")
                    return {"status": "OK"}
                case 2:
                    logger.info("  -> [Match-Case] [LIFT] 取貨同步等待，模式: 2，模擬等待 3 秒...")
                    time.sleep(3)
                    result_data = {
                        "status": "OK",
                        "palletNo": f"PLT_LIFT_OUT_{wes_id}"
                    }
                    logger.info(f"  -> [LIFT] 取貨交接完成，結果: {result_data}，回報 WES 並釋放資源。")
                    return result_data
                case _:
                    time.sleep(3)
                    return {"status": "OK"}

        case "Station":
            match purpose_mode:
                case 1:
                    logger.info("  -> [Match-Case] [Station] 入料到位感測同步等待結果，模擬等待 3 秒...")
                    time.sleep(3)
                    logger.info(f"  -> [Station] 入料到位作業完成，回報 WES (ID: {wes_id}) 並釋放設備資源。")
                    return {"status": "OK"}
                case 2:
                    logger.info("  -> [Match-Case] [Station] 出料釋放資源同步等待結果，模擬等待 3 秒...")
                    time.sleep(3)
                    logger.info(f"  -> [Station] 出料釋放作業完成，回報 WES (ID: {wes_id}) 並釋放設備資源。")
                    return {"status": "OK"}
                case _:
                    time.sleep(3)
                    return {"status": "OK"}

        case _:
            time.sleep(3)
            logger.info(f"  -> [Match-Case] 未知設備類型 {equipment_type}，回報 WES 並釋放資源。")
            return {"status": "OK"}


# ==============================================================================
# 模擬執行流程 (Simulation Workflow)
# ==============================================================================
def run_simulation():
    logger.info("==================================================")
    logger.info("      開始 EAP 設備交握流程模擬 (Mock Mode)       ")
    logger.info("==================================================")

    # 場景 1: Wrap 包膜機流程 (模式 1 (預包) -> 完成 -> 等待結果 -> 模式 3 (完工取貨) -> 完工準備完成)
    logger.info("\n>>> [場景 1] 模擬 AGV 至 Wrap 包膜機放貨並取貨...")
    wes_id_1 = "WES_WRAP_99"
    if request_enter(equipment_type="Wrap", wes_id=wes_id_1, purpose_mode=1) == "OK":
        logger.info("  >>> AGV 進入 Wrap 干涉區，執行放貨作業...")
        time.sleep(0.5)
        logger.info("  >>> AGV 完成放貨，退回安全區域。")

        if preparation_complete(equipment_type="Wrap", wes_id=wes_id_1, purpose_mode=1) == "OK":
            res = result_query_takeover(equipment_type="Wrap", wes_id=wes_id_1, purpose_mode=1)
            if res.get("status") == "OK":
                logger.info("  >>> 包膜作業完成且資源已釋放。AGV 準備重新進入取貨...")
                
                # 重新申請進入取貨 (mode 3)
                if request_enter(equipment_type="Wrap", wes_id=wes_id_1, purpose_mode=3) == "OK":
                    logger.info("  >>> AGV 重新進入 Wrap 執行取貨...")
                    time.sleep(0.5)
                    logger.info("  >>> AGV 完成取貨，攜帶貨物退出安全區域。")
                    preparation_complete(equipment_type="Wrap", wes_id=wes_id_1, purpose_mode=3)
                    logger.info("  >>> [場景 1] 成功結束。")

    # 場景 2: Check 檢驗站流程 (模式 1 (檢測進出))
    logger.info("\n>>> [場景 2] 模擬 AGV 至 Check 檢驗站進行檢驗...")
    wes_id_2 = "WES_CHECK_88"
    if request_enter(equipment_type="Check", wes_id=wes_id_2, purpose_mode=1) == "OK":
        logger.info("  >>> AGV 進入 Check 干涉區放貨並離開...")
        time.sleep(0.5)
        if preparation_complete(equipment_type="Check", wes_id=wes_id_2, purpose_mode=1) == "OK":
            res = result_query_takeover(equipment_type="Check", wes_id=wes_id_2, purpose_mode=1)
            logger.info(f"  >>> [場景 2] 成功結束，取得檢驗結果: {res}")

    # 場景 3: ASRS_IPORT 入庫流程 (模式 1)
    logger.info("\n>>> [場景 3] 模擬 AGV 前往 ASRS 入口區放貨...")
    wes_id_3 = "WES_ASRS_IN_77"
    # 傳入 extra arguments
    if request_enter(
        equipment_type="ASRS_IPORT",
        wes_id=wes_id_3,
        purpose_mode=1,
        pallet_no="PLT_ASRS_001",
        cargo_height="Low",
        rack_in_place=True
    ) == "OK":
        logger.info("  >>> AGV 進入 ASRS 入口區執行放貨...")
        time.sleep(0.5)
        if preparation_complete(equipment_type="ASRS_IPORT", wes_id=wes_id_3, purpose_mode=1) == "OK":
            res = result_query_takeover(equipment_type="ASRS_IPORT", wes_id=wes_id_3, purpose_mode=1)
            logger.info(f"  >>> [場景 3] 成功結束，結果: {res}")

    # 場景 4: Aligner 糾偏機流程
    logger.info("\n>>> [場景 4] 模擬 AGV 至 Aligner 糾偏機進行入料與出料...")
    wes_id_4 = "WES_ALIGN_55"
    # 1. 申請入料 (purpose_mode=1)
    if request_enter(equipment_type="Aligner", wes_id=wes_id_4, purpose_mode=1) == "OK":
        logger.info("  >>> AGV 進入 Aligner 干涉區，執行放貨作業...")
        time.sleep(0.5)
        logger.info("  >>> AGV 完成放貨，退回安全區域。")
        
        # 2. 入料準備完成
        if preparation_complete(equipment_type="Aligner", wes_id=wes_id_4, purpose_mode=1) == "OK":
            # 3. 入料同步等待結果 (回傳 OK)
            res1 = result_query_takeover(equipment_type="Aligner", wes_id=wes_id_4, purpose_mode=1)
            if res1.get("status") == "OK":
                logger.info("  >>> 入料作業完成，機台開始糾偏。AGV 準備申請出料取貨...")
                time.sleep(0.5)
                
                # 4. 申請出料 (purpose_mode=2)
                if request_enter(equipment_type="Aligner", wes_id=wes_id_4, purpose_mode=2) == "OK":
                    logger.info("  >>> AGV 重新進入 Aligner 執行取貨...")
                    time.sleep(0.5)
                    logger.info("  >>> AGV 完成取貨，退出安全區域。")
                    
                    # 5. 出料準備完成
                    if preparation_complete(equipment_type="Aligner", wes_id=wes_id_4, purpose_mode=2) == "OK":
                        # 6. 出料等待結果並接手
                        res2 = result_query_takeover(equipment_type="Aligner", wes_id=wes_id_4, purpose_mode=2)
                        logger.info(f"  >>> [場景 4] 成功結束，取得糾偏出料結果: {res2}")


if __name__ == "__main__":
    run_simulation()

import uvicorn
from fastapi import FastAPI, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

# 匯入原本的 Python 交握函式
from equip_handshaking import request_enter, preparation_complete, result_query_takeover

app = FastAPI(
    title="EAP 設備交握 API 服務",
    description="提供 AGV/AMR 與 EAP 設備之間的 HTTP RESTful API 交握介面",
    version="1.2.0"
)

# 定義 API 請求的資料格式 (Pydantic Model)
class HandshakeRequest(BaseModel):
    equipment_type: str = Field(
        ..., 
        description="設備類型 (Wrap, Check, Aligner, PalletSupply, ASRS_IPORT, ASRS_OPORT, LIFT, Station)", 
        json_schema_extra={"example": "Wrap"}
    )
    wes_id: str = Field(
        ..., 
        description="WES_ID 任務編號", 
        json_schema_extra={"example": "WES_ID01"}
    )
    purpose_mode: int = Field(
        ..., 
        description="申請目的模式", 
        json_schema_extra={"example": 1}
    )
    pallet_no: Optional[str] = Field(None, alias="PalletNo", description="機台特有參數 PalletNo")
    cargo_height: Optional[str] = Field(None, alias="CargoHeight", description="機台特有參數 CargoHeight")
    rack_in_place: Optional[bool] = Field(None, alias="RackInPlace", description="機台特有參數 RackInPlace")
    op_mode: Optional[int] = Field(None, alias="OpMode", description="機台特有參數 OpMode (1:單板作業, 2:上層/子板作業)")
    extra_args: dict = Field(
        default=None,
        description="機台特有額外引數 (如 pallet_no, cargo_height, rack_in_place, op_mode)",
        json_schema_extra={"example": {"pallet_no": "P001", "cargo_height": "Low", "rack_in_place": True, "op_mode": 1}}
    )


# 定義 API 回傳格式 (基本版)
class HandshakeResponse(BaseModel):
    status: str = Field(..., description="執行結果 ('OK' 或 'WAIT')")

@app.post("/api/request-enter", response_model=HandshakeResponse, summary="［1］ 申請進入設備")
def api_request_enter(payload: HandshakeRequest):
    try:
        # 呼叫原本的 Python 核心函式，傳入解包後的 extra_args 與別名欄位
        kwargs = payload.extra_args if payload.extra_args is not None else {}
        # 合併別名欄位至 kwargs
        if payload.pallet_no is not None:
            kwargs["pallet_no"] = payload.pallet_no
        if payload.cargo_height is not None:
            kwargs["cargo_height"] = payload.cargo_height
        if payload.rack_in_place is not None:
            kwargs["rack_in_place"] = payload.rack_in_place
        if payload.op_mode is not None:
            kwargs["op_mode"] = payload.op_mode
        result = request_enter(
            equipment_type=payload.equipment_type,
            wes_id=payload.wes_id,
            purpose_mode=payload.purpose_mode,
            **kwargs
        )
        return HandshakeResponse(status=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/preparation-complete", response_model=HandshakeResponse, summary="［2］ 準備完成通知")
def api_preparation_complete(payload: HandshakeRequest):
    try:
        result = preparation_complete(
            equipment_type=payload.equipment_type,
            wes_id=payload.wes_id,
            purpose_mode=payload.purpose_mode
        )
        return HandshakeResponse(status=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/result-query-takeover", summary="［3］ 等待處理結果並接手")
def api_result_query_takeover(payload: HandshakeRequest):
    try:
        # 此處回傳為 dict，以支援規格表的多欄位要求
        result = result_query_takeover(
            equipment_type=payload.equipment_type,
            wes_id=payload.wes_id,
            purpose_mode=payload.purpose_mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="EAP Handshaking API Service")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="監聽 Host")
    parser.add_argument("--port", type=int, default=8000, help="監聽 Port")
    args = parser.parse_args()
    
    # 啟動 Web Server
    uvicorn.run("app:app", host=args.host, port=args.port, reload=True)

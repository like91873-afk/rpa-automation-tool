"""
RPA自动化工具 - FastAPI后端服务

提供REST API接口用于流程管理和执行
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..engine import ExecutionEngine
from ..models.schemas import (
    ExecutionResult,
    Flow,
    FlowExecuteRequest,
    FlowSaveRequest,
    NodeDefinition,
)
from ..nodes import get_all_node_definitions
from ..utils import (
    create_sample_flow,
    generate_flow_id,
    load_flow_from_file,
    save_flow_to_file,
    validate_flow,
)

# 创建FastAPI应用
app = FastAPI(
    title="RPA自动化工具 API",
    description="轻量级RPA流程设计器和执行引擎",
    version="0.1.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局执行引擎
engine = ExecutionEngine()

# 流程存储目录
FLOWS_DIR = Path("./flows")
FLOWS_DIR.mkdir(exist_ok=True)

# 静态文件目录
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# 前端页面
@app.get("/")
async def index():
    """前端设计器页面"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "RPA自动化工具 API", "docs": "/docs"}


# API响应模型
class ApiResponse(BaseModel):
    """通用API响应"""
    success: bool
    message: str
    data: Optional[Any] = None


class FlowListResponse(BaseModel):
    """流程列表响应"""
    flows: List[Dict[str, Any]]
    total: int


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# 获取节点类型列表
@app.get("/api/nodes", response_model=List[NodeDefinition])
async def list_nodes():
    """获取所有可用的节点类型"""
    return get_all_node_definitions()


# 流程管理API
@app.get("/api/flows", response_model=FlowListResponse)
async def list_flows():
    """获取所有流程列表"""
    flows = []
    for flow_file in FLOWS_DIR.glob("*.json"):
        try:
            flow = load_flow_from_file(str(flow_file))
            flows.append({
                "id": flow.id,
                "name": flow.name,
                "description": flow.description,
                "version": flow.version,
                "node_count": len(flow.nodes),
                "created_at": flow.created_at.isoformat(),
                "updated_at": flow.updated_at.isoformat(),
            })
        except Exception as e:
            print(f"加载流程文件失败 {flow_file}: {e}")

    return FlowListResponse(flows=flows, total=len(flows))


@app.post("/api/flows", response_model=ApiResponse)
async def create_flow(request: FlowSaveRequest):
    """创建新流程"""
    flow = request.flow

    # 生成ID（如果没有）
    if not flow.id:
        flow.id = generate_flow_id()

    # 验证流程
    errors = validate_flow(flow)
    if errors:
        raise HTTPException(status_code=400, detail=f"流程验证失败: {', '.join(errors)}")

    # 保存流程
    flow_file = FLOWS_DIR / f"{flow.id}.json"
    if flow_file.exists() and not request.overwrite:
        raise HTTPException(status_code=409, detail=f"流程已存在: {flow.id}")

    save_flow_to_file(flow, str(flow_file))

    return ApiResponse(
        success=True,
        message=f"流程创建成功: {flow.id}",
        data={"flow_id": flow.id}
    )


@app.get("/api/flows/{flow_id}")
async def get_flow(flow_id: str):
    """获取流程详情"""
    flow_file = FLOWS_DIR / f"{flow_id}.json"
    if not flow_file.exists():
        raise HTTPException(status_code=404, detail=f"流程不存在: {flow_id}")

    flow = load_flow_from_file(str(flow_file))
    return flow.model_dump()


@app.put("/api/flows/{flow_id}", response_model=ApiResponse)
async def update_flow(flow_id: str, request: FlowSaveRequest):
    """更新流程"""
    flow = request.flow
    flow.id = flow_id

    # 验证流程
    errors = validate_flow(flow)
    if errors:
        raise HTTPException(status_code=400, detail=f"流程验证失败: {', '.join(errors)}")

    # 保存流程
    flow_file = FLOWS_DIR / f"{flow_id}.json"
    save_flow_to_file(flow, str(flow_file))

    return ApiResponse(
        success=True,
        message=f"流程更新成功: {flow_id}",
        data={"flow_id": flow_id}
    )


@app.delete("/api/flows/{flow_id}", response_model=ApiResponse)
async def delete_flow(flow_id: str):
    """删除流程"""
    flow_file = FLOWS_DIR / f"{flow_id}.json"
    if not flow_file.exists():
        raise HTTPException(status_code=404, detail=f"流程不存在: {flow_id}")

    flow_file.unlink()

    return ApiResponse(
        success=True,
        message=f"流程删除成功: {flow_id}"
    )


# 流程执行API
@app.post("/api/flows/{flow_id}/execute", response_model=ApiResponse)
async def execute_flow(flow_id: str, request: FlowExecuteRequest):
    """执行流程"""
    flow_file = FLOWS_DIR / f"{flow_id}.json"
    if not flow_file.exists():
        raise HTTPException(status_code=404, detail=f"流程不存在: {flow_id}")

    # 加载流程
    flow = load_flow_from_file(str(flow_file))

    # 验证流程
    errors = validate_flow(flow)
    if errors:
        raise HTTPException(status_code=400, detail=f"流程验证失败: {', '.join(errors)}")

    # 执行流程
    try:
        result = engine.execute_flow(
            flow=flow,
            initial_variables=request.variables,
            timeout=request.timeout,
            debug=request.debug
        )

        return ApiResponse(
            success=True,
            message="流程执行完成",
            data=result.model_dump()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流程执行失败: {str(e)}")


# 获取示例流程
@app.get("/api/flows/sample")
async def get_sample_flow():
    """获取示例流程"""
    flow = create_sample_flow()
    return flow.model_dump()


# 获取执行引擎状态
@app.get("/api/engine/status")
async def get_engine_status():
    """获取执行引擎状态"""
    return {
        "status": "running",
        "version": "0.1.0",
        "flows_dir": str(FLOWS_DIR.absolute()),
        "flow_count": len(list(FLOWS_DIR.glob("*.json")))
    }


# 启动服务器的函数
def start_server(host: str = "0.0.0.0", port: int = 8000):
    """启动API服务器"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()

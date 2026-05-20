"""
RPA自动化工具 - FastAPI后端服务

提供REST API接口用于流程管理、执行和调度
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..engine import ExecutionEngine
from ..models.schemas import (
    ExecutionHistory,
    FlowExecuteRequest,
    FlowSaveRequest,
    NodeDefinition,
    Schedule,
    ScheduleCreateRequest,
    ScheduleStatus,
    ScheduleUpdateRequest,
    TriggerType,
)
from ..nodes import get_all_node_definitions
from ..scheduler.scheduler import FlowScheduler
from ..scheduler.events import EventManager
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
    description="轻量级RPA流程设计器和执行引擎，支持定时调度和事件触发",
    version="0.2.0"
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


# ============= 调度系统初始化 =============

def _flow_executor(flow_id: str, variables: Dict[str, Any] = None):
    """流程执行器函数，供调度器调用"""
    flow_file = FLOWS_DIR / f"{flow_id}.json"
    if not flow_file.exists():
        raise FileNotFoundError(f"流程不存在: {flow_id}")
    flow = load_flow_from_file(str(flow_file))
    return engine.execute_flow(flow=flow, initial_variables=variables or {})


scheduler = FlowScheduler(flow_executor=_flow_executor)
event_manager = EventManager(scheduler=scheduler)

# 注册调度器事件回调
def _on_schedule_added(schedule: Schedule):
    """调度任务添加时，如果是文件监控类型则启动监控"""
    if schedule.trigger_type == TriggerType.FILE_WATCH and schedule.status == ScheduleStatus.ACTIVE:
        event_manager.start_file_watch(schedule)

scheduler.on("schedule_added", _on_schedule_added)


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
    return {
        "status": "ok",
        "version": "0.2.0",
        "timestamp": datetime.now().isoformat(),
        "scheduler_running": scheduler.is_running(),
    }


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

    if not flow.id:
        flow.id = generate_flow_id()

    errors = validate_flow(flow)
    if errors:
        raise HTTPException(status_code=400, detail=f"流程验证失败: {', '.join(errors)}")

    flow_file = FLOWS_DIR / f"{flow.id}.json"
    if flow_file.exists() and not request.overwrite:
        raise HTTPException(status_code=409, detail=f"流程已存在: {flow.id}")

    save_flow_to_file(flow, str(flow_file))

    return ApiResponse(
        success=True,
        message=f"流程创建成功: {flow.id}",
        data={"flow_id": flow.id}
    )


@app.get("/api/flows/sample")
async def get_sample_flow():
    """获取示例流程"""
    flow = create_sample_flow()
    return flow.model_dump()


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

    errors = validate_flow(flow)
    if errors:
        raise HTTPException(status_code=400, detail=f"流程验证失败: {', '.join(errors)}")

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

    flow = load_flow_from_file(str(flow_file))

    errors = validate_flow(flow)
    if errors:
        raise HTTPException(status_code=400, detail=f"流程验证失败: {', '.join(errors)}")

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


# ============= 调度管理API =============

@app.post("/api/schedules", response_model=ApiResponse)
async def create_schedule(request: ScheduleCreateRequest):
    """创建调度任务"""
    schedule = Schedule(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        flow_id=request.flow_id,
        trigger_type=request.trigger_type,
        cron_expression=request.cron_expression,
        timezone=request.timezone,
        interval_seconds=request.interval_seconds,
        run_at=request.run_at,
        webhook_token=request.webhook_token or str(uuid.uuid4()),
        webhook_secret=request.webhook_secret,
        watch_path=request.watch_path,
        watch_events=request.watch_events,
        watch_pattern=request.watch_pattern,
        watch_recursive=request.watch_recursive,
        initial_variables=request.initial_variables,
        max_retries=request.max_retries,
        retry_delay_seconds=request.retry_delay_seconds,
        timeout=request.timeout,
    )

    # 验证流程是否存在
    flow_file = FLOWS_DIR / f"{request.flow_id}.json"
    if not flow_file.exists():
        raise HTTPException(status_code=404, detail=f"关联流程不存在: {request.flow_id}")

    try:
        scheduler.add_schedule(schedule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse(
        success=True,
        message=f"调度任务创建成功: {schedule.id}",
        data={
            "schedule_id": schedule.id,
            "webhook_url": f"/api/webhooks/{schedule.webhook_token}" if schedule.trigger_type == TriggerType.WEBHOOK else None,
        }
    )


@app.get("/api/schedules")
async def list_schedules(status: Optional[str] = None):
    """获取调度任务列表"""
    status_filter = ScheduleStatus(status) if status else None
    schedules = scheduler.list_schedules(status_filter)
    return {
        "schedules": [s.model_dump() for s in schedules],
        "total": len(schedules),
    }


@app.get("/api/schedules/{schedule_id}")
async def get_schedule(schedule_id: str):
    """获取调度任务详情"""
    schedule = scheduler.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail=f"调度任务不存在: {schedule_id}")
    return schedule.model_dump()


@app.put("/api/schedules/{schedule_id}", response_model=ApiResponse)
async def update_schedule(schedule_id: str, request: ScheduleUpdateRequest):
    """更新调度任务"""
    try:
        updates = request.model_dump(exclude_none=True)
        schedule = scheduler.update_schedule(schedule_id, updates)
        return ApiResponse(
            success=True,
            message=f"调度任务更新成功: {schedule_id}",
            data=schedule.model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/schedules/{schedule_id}", response_model=ApiResponse)
async def delete_schedule(schedule_id: str):
    """删除调度任务"""
    event_manager.stop_file_watch(schedule_id)
    if scheduler.remove_schedule(schedule_id):
        return ApiResponse(success=True, message=f"调度任务删除成功: {schedule_id}")
    raise HTTPException(status_code=404, detail=f"调度任务不存在: {schedule_id}")


@app.post("/api/schedules/{schedule_id}/pause", response_model=ApiResponse)
async def pause_schedule(schedule_id: str):
    """暂停调度任务"""
    try:
        schedule = scheduler.pause_schedule(schedule_id)
        event_manager.stop_file_watch(schedule_id)
        return ApiResponse(success=True, message=f"调度任务已暂停: {schedule_id}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/schedules/{schedule_id}/resume", response_model=ApiResponse)
async def resume_schedule(schedule_id: str):
    """恢复调度任务"""
    try:
        schedule = scheduler.resume_schedule(schedule_id)
        if schedule.trigger_type == TriggerType.FILE_WATCH:
            event_manager.start_file_watch(schedule)
        return ApiResponse(success=True, message=f"调度任务已恢复: {schedule_id}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/schedules/{schedule_id}/trigger", response_model=ApiResponse)
async def trigger_schedule(schedule_id: str, variables: Dict[str, Any] = None):
    """手动触发调度任务"""
    try:
        history = scheduler.trigger_schedule(schedule_id, variables)
        return ApiResponse(
            success=True,
            message="调度任务已触发",
            data=history.model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= Webhook API =============

@app.post("/api/webhooks/{token}")
async def webhook_trigger(token: str, request: Request):
    """Webhook触发端点"""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    # 从header获取密钥
    secret = request.headers.get("X-Webhook-Secret")

    try:
        history = scheduler.trigger_webhook(token, payload, secret)
        return {
            "success": True,
            "message": "Webhook触发成功",
            "execution_id": history.id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= 执行历史API =============

@app.get("/api/history")
async def get_execution_history(schedule_id: Optional[str] = None, limit: int = 100):
    """获取执行历史"""
    history = scheduler.get_history(schedule_id, limit)
    return {
        "history": [h.model_dump() for h in history],
        "total": len(history),
    }


@app.delete("/api/history", response_model=ApiResponse)
async def clear_execution_history(schedule_id: Optional[str] = None):
    """清空执行历史"""
    scheduler.clear_history(schedule_id)
    return ApiResponse(success=True, message="执行历史已清空")


# ============= 调度器状态API =============

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """获取调度器状态"""
    return scheduler.get_statistics()


@app.post("/api/scheduler/start", response_model=ApiResponse)
async def start_scheduler():
    """启动调度器"""
    scheduler.start()
    return ApiResponse(success=True, message="调度器已启动")


@app.post("/api/scheduler/stop", response_model=ApiResponse)
async def stop_scheduler():
    """停止调度器"""
    scheduler.stop()
    event_manager.stop_all()
    return ApiResponse(success=True, message="调度器已停止")


# ============= 文件监控API =============

@app.get("/api/watchers")
async def list_watchers():
    """获取活跃的文件监控器列表"""
    return event_manager.get_active_watchers()


@app.get("/api/events")
async def get_event_log(limit: int = 100):
    """获取事件日志"""
    return event_manager.get_event_log(limit)


# 获取执行引擎状态
@app.get("/api/engine/status")
async def get_engine_status():
    """获取执行引擎状态"""
    return {
        "status": "running",
        "version": "0.2.0",
        "flows_dir": str(FLOWS_DIR.absolute()),
        "flow_count": len(list(FLOWS_DIR.glob("*.json"))),
        "scheduler_running": scheduler.is_running(),
    }


# 启动服务器的函数
def start_server(host: str = "0.0.0.0", port: int = 8000, enable_scheduler: bool = True):
    """启动API服务器"""
    import uvicorn

    if enable_scheduler:
        scheduler.start(check_interval=10.0)
        print("[调度器] 已启动")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()

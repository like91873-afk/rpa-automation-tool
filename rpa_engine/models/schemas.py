"""
RPA自动化工具 - 核心数据模型

定义流程、节点、连接等核心数据结构
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """节点类型枚举"""
    PYTHON_EXEC = "python_exec"           # Python代码执行
    PYTHON_SCRIPT = "python_script"       # Python脚本文件执行
    FILE_OPEN = "file_open"               # 打开文件
    FILE_READ = "file_read"               # 读取文件
    FILE_WRITE = "file_write"             # 写入文件
    SYSTEM_CMD = "system_cmd"             # 系统命令执行
    CONDITION = "condition"               # 条件判断
    LOOP = "loop"                         # 循环
    SFTP_CONNECT = "sftp_connect"         # SFTP连接
    SFTP_UPLOAD = "sftp_upload"           # SFTP上传
    SFTP_DOWNLOAD = "sftp_download"       # SFTP下载
    MATH_OPERATION = "math_operation"     # 数值运算
    STRING_OPERATION = "string_operation" # 字符串操作


class InputType(str, Enum):
    """输入参数类型"""
    TEXT = "text"              # 普通文本
    VARIABLE = "variable"      # 变量引用
    DROPDOWN = "dropdown"      # 下拉选择
    NUMBER = "number"          # 数字
    BOOLEAN = "boolean"        # 布尔值
    CODE = "code"              # 代码编辑器
    FILE_PATH = "file_path"    # 文件路径


class NodeInput(BaseModel):
    """节点输入参数定义"""
    name: str = Field(..., description="参数名称")
    label: str = Field(..., description="参数显示标签")
    type: InputType = Field(default=InputType.TEXT, description="参数类型")
    required: bool = Field(default=True, description="是否必填")
    default: Optional[Any] = Field(default=None, description="默认值")
    options: Optional[List[str]] = Field(default=None, description="下拉框选项")
    description: Optional[str] = Field(default=None, description="参数描述")


class NodeOutput(BaseModel):
    """节点输出定义"""
    key: str = Field(..., description="输出键名")
    label: str = Field(..., description="输出显示标签")
    description: str = Field(..., description="输出描述")


class NodeDefinition(BaseModel):
    """节点类型定义"""
    type: NodeType = Field(..., description="节点类型")
    name: str = Field(..., description="节点名称")
    description: str = Field(default="", description="节点描述")
    category: str = Field(default="通用", description="节点分类")
    icon: Optional[str] = Field(default=None, description="节点图标")
    inputs: List[NodeInput] = Field(default_factory=list, description="输入参数列表")
    outputs: List[NodeOutput] = Field(default_factory=list, description="输出定义列表")


class NodeInstance(BaseModel):
    """流程中的节点实例"""
    id: str = Field(..., description="节点实例ID")
    type: NodeType = Field(..., description="节点类型")
    name: str = Field(default="", description="节点显示名称")
    alias: Optional[str] = Field(default=None, description="节点别名")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="输入参数值")
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0}, description="画布位置")
    disabled: bool = Field(default=False, description="是否禁用")


class Connection(BaseModel):
    """节点连接"""
    id: str = Field(..., description="连接ID")
    source_node_id: str = Field(..., description="源节点ID")
    source_port: str = Field(default="output", description="源端口")
    target_node_id: str = Field(..., description="目标节点ID")
    target_port: str = Field(default="input", description="目标端口")


class FlowVariable(BaseModel):
    """流程变量"""
    name: str = Field(..., description="变量名")
    value: Any = Field(default=None, description="变量值")
    type: str = Field(default="any", description="变量类型")
    description: Optional[str] = Field(default=None, description="变量描述")


class Flow(BaseModel):
    """完整流程定义"""
    id: str = Field(..., description="流程ID")
    name: str = Field(..., description="流程名称")
    description: Optional[str] = Field(default=None, description="流程描述")
    version: str = Field(default="1.0.0", description="流程版本")
    nodes: List[NodeInstance] = Field(default_factory=list, description="节点列表")
    connections: List[Connection] = Field(default_factory=list, description="连接列表")
    variables: Dict[str, Any] = Field(default_factory=dict, description="全局变量")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "RUNNING"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class NodeExecutionLog(BaseModel):
    """节点执行日志"""
    node_id: str = Field(..., description="节点ID")
    node_name: str = Field(default="", description="节点名称")
    node_type: NodeType = Field(..., description="节点类型")
    status: ExecutionStatus = Field(..., description="执行状态")
    start_time: datetime = Field(default_factory=datetime.now, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    duration_ms: Optional[int] = Field(default=None, description="执行时长(毫秒)")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="输入参数")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="输出结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    logs: List[str] = Field(default_factory=list, description="执行日志")


class ExecutionResult(BaseModel):
    """流程执行结果"""
    flow_id: str = Field(..., description="流程ID")
    flow_name: str = Field(default="", description="流程名称")
    execution_id: str = Field(..., description="执行ID")
    status: ExecutionStatus = Field(..., description="执行状态")
    start_time: datetime = Field(default_factory=datetime.now, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    duration_ms: Optional[int] = Field(default=None, description="执行时长(毫秒)")
    variables: Dict[str, Any] = Field(default_factory=dict, description="最终变量值")
    node_logs: List[NodeExecutionLog] = Field(default_factory=list, description="节点执行日志")
    error: Optional[str] = Field(default=None, description="错误信息")


class FlowExecuteRequest(BaseModel):
    """流程执行请求"""
    flow_id: str = Field(..., description="流程ID")
    variables: Dict[str, Any] = Field(default_factory=dict, description="初始变量")
    timeout: int = Field(default=3600, description="超时时间(秒)")
    debug: bool = Field(default=False, description="调试模式")


class FlowSaveRequest(BaseModel):
    """流程保存请求"""
    flow: Flow = Field(..., description="流程定义")
    overwrite: bool = Field(default=True, description="是否覆盖")

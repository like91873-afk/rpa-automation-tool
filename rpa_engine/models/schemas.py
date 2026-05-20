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
    DIRECTORY_LIST = "directory_list"      # 列出目录
    PATH_EXISTS = "path_exists"           # 路径存在检查
    SYSTEM_CMD = "system_cmd"             # 系统命令执行
    POWERSHELL = "powershell"             # PowerShell命令
    COMPUTER_INFO = "computer_info"       # 获取电脑信息
    CONDITION = "condition"               # 条件判断
    LOOP = "loop"                         # 循环
    SFTP_CONNECT = "sftp_connect"         # SFTP连接
    SFTP_UPLOAD = "sftp_upload"           # SFTP上传
    SFTP_DOWNLOAD = "sftp_download"       # SFTP下载
    SFTP_NEW_FILE = "sftp_new_file"       # SFTP新建文件
    SFTP_WRITE_FILE = "sftp_write_file"   # SFTP写入文件
    FTP_CONNECT = "ftp_connect"           # FTP连接
    FTP_LIST_DIR = "ftp_list_dir"         # FTP查看目录
    XML_SAVE = "xml_save"                 # 数据保存为XML
    MATH_OPERATION = "math_operation"     # 数值运算
    STRING_OPERATION = "string_operation" # 字符串操作
    # 数据库操作
    DB_CONNECT = "db_connect"             # 数据库连接
    DB_QUERY = "db_query"                 # 数据库查询
    DB_EXECUTE = "db_execute"             # 数据库执行SQL
    # Excel操作
    EXCEL_READ = "excel_read"             # 读取Excel
    EXCEL_WRITE = "excel_write"           # 写入Excel
    EXCEL_CREATE = "excel_create"         # 创建Excel
    # Web操作
    HTTP_REQUEST = "http_request"         # HTTP请求
    WEB_SCRAPE = "web_scrape"             # 网页抓取
    # 延迟/等待
    DELAY = "delay"                       # 延迟执行
    WAIT_FOR = "wait_for"                 # 等待条件
    # Phase 5 新增节点
    FORMULA = "formula"                   # 公式计算
    EMAIL_CONNECT = "email_connect"       # 邮箱连接
    EMAIL_FETCH = "email_fetch"           # 邮件获取
    EMAIL_SEND = "email_send"             # 邮件发送
    TIME_GET = "time_get"                 # 时间获取
    TIME_PROCESS = "time_process"         # 时间处理
    FILE_COMPRESS = "file_compress"       # 文件压缩
    FILE_DECOMPRESS = "file_decompress"   # 文件解压
    PDF_PARSE = "pdf_parse"               # PDF解析
    FTP_DELETE = "ftp_delete"             # FTP删除
    SFTP_CREATE_DIR = "sftp_create_dir"   # SFTP创建目录


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
    RUNNING = "running"
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


# ============= 调度系统模型 =============

class TriggerType(str, Enum):
    """触发器类型"""
    CRON = "cron"                # Cron表达式触发
    INTERVAL = "interval"        # 固定间隔触发
    ONCE = "once"               # 单次定时执行
    WEBHOOK = "webhook"         # Webhook触发
    FILE_WATCH = "file_watch"   # 文件监控触发
    MANUAL = "manual"           # 手动触发


class ScheduleStatus(str, Enum):
    """调度任务状态"""
    ACTIVE = "active"       # 活跃
    PAUSED = "paused"       # 暂停
    COMPLETED = "completed" # 已完成（一次性任务）
    FAILED = "failed"       # 失败


class FileWatchEvent(str, Enum):
    """文件监控事件类型"""
    CREATED = "created"     # 文件创建
    MODIFIED = "modified"   # 文件修改
    DELETED = "deleted"     # 文件删除
    MOVED = "moved"         # 文件移动


class Schedule(BaseModel):
    """调度任务定义"""
    id: str = Field(..., description="调度任务ID")
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(default=None, description="任务描述")
    flow_id: str = Field(..., description="关联流程ID")
    trigger_type: TriggerType = Field(..., description="触发器类型")
    # Cron触发配置
    cron_expression: Optional[str] = Field(default=None, description="Cron表达式 (分 时 日 月 周)")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    # 间隔触发配置
    interval_seconds: Optional[int] = Field(default=None, description="间隔秒数")
    # 单次触发配置
    run_at: Optional[datetime] = Field(default=None, description="执行时间")
    # Webhook配置
    webhook_token: Optional[str] = Field(default=None, description="Webhook访问令牌")
    webhook_secret: Optional[str] = Field(default=None, description="Webhook验证密钥")
    # 文件监控配置
    watch_path: Optional[str] = Field(default=None, description="监控路径")
    watch_events: List[FileWatchEvent] = Field(default_factory=lambda: [FileWatchEvent.CREATED], description="监控事件类型")
    watch_pattern: str = Field(default="*", description="文件匹配模式 (*.txt)")
    watch_recursive: bool = Field(default=False, description="是否递归监控子目录")
    # 通用配置
    initial_variables: Dict[str, Any] = Field(default_factory=dict, description="初始变量")
    max_retries: int = Field(default=0, description="最大重试次数")
    retry_delay_seconds: int = Field(default=60, description="重试间隔(秒)")
    timeout: int = Field(default=3600, description="执行超时(秒)")
    status: ScheduleStatus = Field(default=ScheduleStatus.ACTIVE, description="任务状态")
    # 运行统计
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    last_run_at: Optional[datetime] = Field(default=None, description="上次执行时间")
    next_run_at: Optional[datetime] = Field(default=None, description="下次执行时间")
    run_count: int = Field(default=0, description="执行次数")
    success_count: int = Field(default=0, description="成功次数")
    fail_count: int = Field(default=0, description="失败次数")


class ScheduleCreateRequest(BaseModel):
    """创建调度任务请求"""
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(default=None, description="任务描述")
    flow_id: str = Field(..., description="关联流程ID")
    trigger_type: TriggerType = Field(..., description="触发器类型")
    cron_expression: Optional[str] = Field(default=None, description="Cron表达式")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    interval_seconds: Optional[int] = Field(default=None, description="间隔秒数")
    run_at: Optional[datetime] = Field(default=None, description="执行时间")
    webhook_token: Optional[str] = Field(default=None, description="Webhook令牌")
    webhook_secret: Optional[str] = Field(default=None, description="Webhook密钥")
    watch_path: Optional[str] = Field(default=None, description="监控路径")
    watch_events: List[FileWatchEvent] = Field(default_factory=lambda: [FileWatchEvent.CREATED])
    watch_pattern: str = Field(default="*")
    watch_recursive: bool = Field(default=False)
    initial_variables: Dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=0)
    retry_delay_seconds: int = Field(default=60)
    timeout: int = Field(default=3600)


class ScheduleUpdateRequest(BaseModel):
    """更新调度任务请求"""
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    cron_expression: Optional[str] = Field(default=None)
    interval_seconds: Optional[int] = Field(default=None)
    run_at: Optional[datetime] = Field(default=None)
    initial_variables: Optional[Dict[str, Any]] = Field(default=None)
    max_retries: Optional[int] = Field(default=None)
    timeout: Optional[int] = Field(default=None)
    status: Optional[ScheduleStatus] = Field(default=None)


class ExecutionHistory(BaseModel):
    """执行历史记录"""
    id: str = Field(..., description="记录ID")
    schedule_id: str = Field(..., description="调度任务ID")
    flow_id: str = Field(..., description="流程ID")
    execution_id: Optional[str] = Field(default=None, description="流程执行ID")
    trigger_type: TriggerType = Field(..., description="触发类型")
    status: ExecutionStatus = Field(..., description="执行状态")
    started_at: datetime = Field(default_factory=datetime.now, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    duration_ms: Optional[int] = Field(default=None, description="执行时长(ms)")
    error: Optional[str] = Field(default=None, description="错误信息")
    trigger_info: Optional[str] = Field(default=None, description="触发信息")
    retry_count: int = Field(default=0, description="重试次数")

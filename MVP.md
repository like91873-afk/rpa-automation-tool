# RPA自动化工具 MVP文档

## 1. 项目概述

### 1.1 目标
构建一个轻量级、可扩展的RPA（机器人流程自动化）设计器和执行引擎，支持可视化流程编排和Python脚本执行。

### 1.2 MVP核心功能
- 流程设计器（可视化编排）
- 基础节点库（文件操作、Python执行、系统命令）
- 流程执行引擎
- 变量管理系统
- REST API接口

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    RPA 设计器前端                          │
│  ┌─────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ 画布区域 │  │ 节点面板    │  │ 属性配置面板         │  │
│  └─────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                   后端服务 (FastAPI)                       │
│  ┌─────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │流程管理  │  │ 节点注册    │  │ 执行引擎            │  │
│  └─────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                   执行层 (Python)                          │
│  ┌─────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │变量管理  │  │ 节点执行器  │  │ 异常处理            │  │
│  └─────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 核心数据模型

### 3.1 流程定义 (Flow)
```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Flow(BaseModel):
    """完整流程定义"""
    id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    nodes: List[NodeInstance]
    connections: List[Connection]
    variables: Dict[str, Any] = {}
```

### 3.2 节点实例 (NodeInstance)
```python
class NodeInstance(BaseModel):
    """流程中的节点实例"""
    id: str
    type: NodeType  # python_exec, file_open, system_cmd等
    name: str
    alias: Optional[str] = None
    inputs: Dict[str, Any]
    position: Dict[str, float] = {"x": 0, "y": 0}
    disabled: bool = False
```

### 3.3 执行上下文 (ExecutionContext)
```python
class ExecutionContext:
    """流程执行上下文"""
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.execution_log: List[Dict] = []
        self.current_node_id: Optional[str] = None
        self.status: str = "pending"
        self.error: Optional[str] = None
    
    def set_variable(self, key: str, value: Any):
        """设置变量"""
        self.variables[key] = value
    
    def get_variable(self, key: str) -> Any:
        """获取变量值"""
        if key not in self.variables:
            raise KeyError(f"变量 {key} 不存在")
        return self.variables[key]
    
    def resolve_variables(self, text: str) -> str:
        """解析文本中的变量引用 ${var_name}"""
        import re
        pattern = r'\$\{(\w+)\}'
        
        def replace_var(match):
            var_name = match.group(1)
            return str(self.get_variable(var_name))
        
        return re.sub(pattern, replace_var, text)
```

---

## 4. 节点实现

### 4.1 Python代码执行节点
```python
class PythonExecNode(BaseNode):
    """
    Python代码执行节点
    
    参数说明:
    - python_code: Python代码，可使用已有全局变量
    - timeout: 执行超时时间（秒），默认1800秒
    """
    
    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        code = self.get_required_input(inputs, "python_code")
        timeout = self.get_input_value(inputs, "timeout", 1800)
        
        # 准备执行环境
        exec_globals = {"__builtins__": __builtins__}
        exec_globals.update(context.variables)
        
        # 执行代码
        exec(code, exec_globals, exec_locals)
        
        # 保存新变量到上下文
        for key, value in exec_locals.items():
            if not key.startswith("_"):
                context.set_variable(key, value)
        
        return {"python_code_result": {"success": True, "variables": exec_locals}}
```

### 4.2 文件打开节点
```python
class FileOpenNode(BaseNode):
    """
    打开文件节点
    
    参数说明:
    - file_path: 要打开的文件路径
    - open_mode: 打开方式（默认程序/应用程序）
    - app_path: 应用程序路径（open_mode为"application"时必填）
    """
    
    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        file_path = self.get_required_input(inputs, "file_path")
        open_mode = self.get_input_value(inputs, "open_mode", "default")
        
        # 验证文件存在
        if not os.path.exists(file_path):
            return {"file_open_result": {"success": False, "error": f"文件不存在: {file_path}"}}
        
        # 使用系统默认程序打开
        if open_mode == "default":
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", file_path])
            else:
                subprocess.run(["xdg-open", file_path])
        
        return {"file_open_result": {"success": True, "file_path": file_path}}
```

### 4.3 系统命令执行节点
```python
class SystemCmdNode(BaseNode):
    """
    命令行执行节点
    
    支持Windows CMD、PowerShell、Unix Bash等
    
    参数说明:
    - command: 要执行的命令
    - shell_type: 命令行类型（auto/cmd/powershell/bash/sh）
    - working_dir: 工作目录
    - timeout: 超时时间（秒）
    """
    
    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        command = self.get_required_input(inputs, "command")
        shell_type = self.get_input_value(inputs, "shell_type", "auto")
        
        # 获取shell命令
        cmd = self._get_shell_command(shell_type, command)
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        return {
            "cmd_result": {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        }
```

---

## 5. 执行引擎

```python
class ExecutionEngine:
    """流程执行引擎"""
    
    def execute_flow(self, flow: Flow, initial_variables: Dict[str, Any] = None) -> ExecutionResult:
        """执行完整流程"""
        context = ExecutionContext(initial_variables)
        
        # 初始化全局变量
        if flow.variables:
            for key, value in flow.variables.items():
                context.set_variable(key, value)
        
        # 获取执行顺序（拓扑排序）
        execution_order = self._get_execution_order(flow)
        
        # 按顺序执行节点
        for node_id in execution_order:
            node = self._find_node(flow, node_id)
            
            # 获取节点执行器
            node_class = get_node_class(node.type)
            executor = node_class()
            
            # 解析输入参数
            resolved_inputs = {}
            for key, value in node.inputs.items():
                resolved_inputs[key] = context.resolve_input_value(value)
            
            # 执行节点
            outputs = executor.execute(resolved_inputs, context)
            
            # 保存输出到上下文
            for key, value in outputs.items():
                context.set_variable(key, value)
        
        return ExecutionResult(
            flow_id=flow.id,
            status=context.status,
            variables=context.variables,
            node_logs=context.execution_log
        )
    
    def _get_execution_order(self, flow: Flow) -> List[str]:
        """拓扑排序获取执行顺序"""
        # 使用Kahn算法
        in_degree = {node.id: 0 for node in flow.nodes}
        
        for conn in flow.connections:
            in_degree[conn.target_node_id] += 1
        
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        order = []
        
        while queue:
            node_id = queue.pop(0)
            order.append(node_id)
            
            for conn in flow.connections:
                if conn.source_node_id == node_id:
                    in_degree[conn.target_node_id] -= 1
                    if in_degree[conn.target_node_id] == 0:
                        queue.append(conn.target_node_id)
        
        return order
```

---

## 6. API接口设计

### 6.1 健康检查
```
GET /health
```

### 6.2 节点管理
```
GET /api/nodes - 获取所有可用节点类型
```

### 6.3 流程管理
```
GET    /api/flows - 获取所有流程列表
POST   /api/flows - 创建新流程
GET    /api/flows/{flow_id} - 获取流程详情
PUT    /api/flows/{flow_id} - 更新流程
DELETE /api/flows/{flow_id} - 删除流程
```

### 6.4 流程执行
```
POST /api/flows/{flow_id}/execute - 执行流程
```

### 6.5 执行请求格式
```json
{
  "flow_id": "flow-001",
  "variables": {
    "input_var": "value"
  },
  "timeout": 3600,
  "debug": false
}
```

### 6.6 执行响应格式
```json
{
  "success": true,
  "message": "流程执行完成",
  "data": {
    "flow_id": "flow-001",
    "execution_id": "exec-uuid",
    "status": "completed",
    "variables": {
      "result": "computed_value"
    },
    "node_logs": [...]
  }
}
```

---

## 7. MVP开发计划

| 阶段 | 功能 | 状态 | 预计时间 |
|------|------|------|----------|
| Phase 1 | 核心数据模型 + 执行引擎 + REST API | ✅ 已完成 | 1 周 |
| Phase 2 | Python执行节点 + 文件操作 + 系统命令 + SFTP + 逻辑控制 + 数据处理 | ✅ 已完成 | 1 周 |
| Phase 3 | FTP操作 + SFTP写入 + XML保存 + 路径检查 | ✅ 已完成 | 1 周 |
| Phase 4 | 数据库 + Excel + Web + 延迟节点 + Web前端设计器 | ✅ 已完成 | 1 周 |
| Phase 5 | 公式计算 + 邮件操作 + 时间处理 + 文件压缩/PDF + FTP删除 + SFTP目录 | ✅ 已完成 | 1 周 |

### Phase 2 新增功能

#### 逻辑控制节点
- **条件判断** (`condition`) - 支持三种条件类型:
  - `expression`: Python布尔表达式
  - `compare`: 比较运算（==, !=, >, >=, <, <=）
  - `variable_check`: 变量存在性和真值检查
- **循环** (`loop`) - 支持三种循环类型:
  - `foreach`: 遍历列表/集合
  - `range`: 数字范围循环
  - `count`: 计数循环

#### 数据处理节点
- **数值运算** (`math_operation`) - 支持运算:
  - 基本运算: add, subtract, multiply, divide, mod, power
  - 数学函数: sqrt, abs, round, floor, ceil, min, max
- **字符串操作** (`string_operation`) - 支持操作:
  - 操作: concat, split, replace, upper, lower, trim, strip
  - 检查: contains, startswith, endswith
  - 处理: format, length, substring, reverse

#### Bug修复
- 修复 `ExecutionStatus.RUNNING` 枚举值大小写不一致问题
- 修复 `NodeExecutionLog` 中 `node_type` 类型不匹配问题
- 修复 `DirectoryListNode` 使用错误的 `NodeType` 问题
- 修复 `PowerShellNode` 和 `GetComputerInfoNode` 共享 `SYSTEM_CMD` 类型问题
- 修复 `pyproject.toml` 中错误的 `build-backend` 配置
- 添加缺失的 `.gitignore` 文件

### Phase 3 新增功能

#### 路径检查节点
- **路径存在检查** (`path_exists`) - 检查文件/目录是否存在，返回详细信息:
  - 路径、是否存在、类型（file/directory）、所在目录、文件名
  - 文件大小、创建时间、修改时间

#### FTP操作节点
- **FTP连接** (`ftp_connect`) - 创建FTP连接对象:
  - 参数: host, port, username, password, passive
  - 输出: ftp_connection 连接对象
- **FTP查看目录** (`ftp_list_dir`) - 查看FTP目录文件列表:
  - 参数: ftp_connection, ftp_dir, recursive
  - 输出: ftp_dir_list 文件信息列表（包含type, permissions, size, ctime, name, abspath）

#### SFTP增强
- **SFTP写入文件** (`sftp_write_file`) - 向SFTP文件写入内容:
  - 写入模式: 追加(append)/覆盖(overwrite)
  - 结束方式: 添加换行(add_newline)/不添加换行(no_newline)
  - 文件不存在处理: 新建(create)/报错(error)

#### XML操作节点
- **XML保存** (`xml_save`) - 将数据保存为XML文件:
  - 支持编码: UTF-8, GBK, GB2312, ASCII
  - 存在处理: 忽略(ignore)/报错(error)/备份(backup)/删除(delete)
  - 自动将字典/列表数据转换为XML结构

### Phase 4 新增功能

#### 数据库操作节点
- **数据库连接** (`db_connect`) - 创建SQLite数据库连接
  - 参数: db_path(数据库路径), db_type(数据库类型)
  - 输出: db_connection(连接对象), db_connect_result(连接结果)
- **数据库查询** (`db_query`) - 执行SELECT查询语句
  - 参数: db_connection, sql, params
  - 输出: query_result(查询结果，包含rows和row_count)
- **数据库执行** (`db_execute`) - 执行INSERT/UPDATE/DELETE语句
  - 参数: db_connection, sql, params, commit
  - 输出: execute_result(执行结果，包含affected_rows)

#### Excel操作节点
- **读取Excel** (`excel_read`) - 读取Excel文件数据
  - 参数: file_path, sheet_name, range, has_header
  - 输出: excel_data(数据列表，支持字典格式)
- **写入Excel** (`excel_write`) - 向Excel写入数据
  - 参数: file_path, sheet_name, data, start_cell, append
  - 输出: write_result(写入结果)
- **创建Excel** (`excel_create`) - 创建新的Excel文件
  - 参数: file_path, sheet_names, headers, data
  - 输出: create_result(创建结果)

#### Web操作节点
- **HTTP请求** (`http_request`) - 发送HTTP请求
  - 支持GET/POST/PUT/DELETE/PATCH方法
  - 参数: url, method, headers, body, timeout
  - 输出: response(响应结果，包含status_code, body, json)
- **网页抓取** (`web_scrape`) - 抓取网页内容
  - 参数: url, extract(text/html), encoding, timeout
  - 输出: scrape_result(抓取结果，包含content, title)

#### 控制流节点
- **延迟执行** (`delay`) - 暂停流程指定时间
  - 参数: seconds(延迟秒数), message(提示信息)
  - 输出: delay_result(延迟结果)
- **等待条件** (`wait_for`) - 等待条件满足
  - 支持: variable_exists/variable_true/python_expression/time
  - 参数: condition_type, variable_name, expression, timeout, poll_interval
  - 输出: wait_result(等待结果)

#### Web前端设计器
- 可视化流程编排界面
- 拖拽式节点添加
- 节点连线和属性配置
- 流程保存/加载/执行
- 执行结果展示

### Phase 5 新增功能

#### 公式计算节点
- **公式计算** (`formula`) - 支持数学表达式计算
  - 参数: formula(数学表达式，支持${var}变量引用), variables(变量映射JSON)
  - 输出: result(计算结果)

#### 邮件操作节点
- **邮箱连接** (`email_connect`) - 创建IMAP邮箱连接
  - 参数: host, port, username, password, use_ssl
  - 输出: connection(连接对象), success(是否成功)
- **邮件获取** (`email_fetch`) - 从邮箱获取邮件列表
  - 参数: connection, folder(INBOX), limit(10), search_criteria(ALL)
  - 输出: emails(邮件列表), count(数量)
- **邮件发送** (`email_send`) - 通过SMTP发送邮件
  - 参数: smtp_host, smtp_port, username, password, to, subject, body, use_tls
  - 输出: success, error

#### 时间处理节点
- **时间获取** (`time_get`) - 获取当前时间和时间戳
  - 参数: format(时间格式), timezone(时区)
  - 输出: datetime, timestamp, year, month, day, hour, minute, second
- **时间处理** (`time_process`) - 时间加减和格式转换
  - 参数: datetime_str, input_format, output_format, days, hours, minutes
  - 输出: result(处理后时间), timestamp

#### 文件压缩/解压节点
- **文件压缩** (`file_compress`) - 压缩文件/目录为zip
  - 参数: source_path, output_path, compression_level(0-9)
  - 输出: success, output_path, file_size
- **文件解压** (`file_decompress`) - 解压zip文件
  - 参数: zip_path, output_dir, overwrite
  - 输出: success, extracted_files, file_count

#### PDF解析节点
- **PDF解析** (`pdf_parse`) - 提取PDF文本内容
  - 参数: pdf_path, page_range(all)
  - 输出: text(文本), page_count(总页数), extracted_pages(提取页数)

#### FTP/SFTP增强
- **FTP删除** (`ftp_delete`) - 删除FTP服务器文件
  - 参数: connection, remote_path
  - 输出: success, error
- **SFTP创建目录** (`sftp_create_dir`) - 在SFTP服务器创建目录
  - 参数: connection, remote_path, recursive(True)
  - 输出: success, error

---

## 8. 技术栈

- **后端**: Python 3.10+, FastAPI, Pydantic
- **前端**: React/Vue + 流程图库（如ReactFlow, X6）
- **存储**: SQLite (MVP) / PostgreSQL (生产)
- **部署**: Docker, Docker Compose

---

## 9. 使用示例

### 9.1 启动API服务器
```bash
python -m rpa_engine serve --host 0.0.0.0 --port 8000
```

### 9.2 创建示例流程
```bash
python -m rpa_engine sample --output sample.json
```

### 9.3 执行流程
```bash
python -m rpa_engine run sample.json --debug
```

### 9.4 Python API调用
```python
from rpa_engine import ExecutionEngine, Flow, NodeInstance

flow = Flow(
    id="my-flow",
    name="我的流程",
    nodes=[
        NodeInstance(
            id="node-1",
            type="python_exec",
            name="执行计算",
            inputs={
                "python_code": "result = 1 + 2\nprint(f'结果: {result}')",
                "timeout": 1800
            }
        )
    ],
    connections=[]
)

engine = ExecutionEngine()
result = engine.execute_flow(flow)
print(f"状态: {result.status}")
```

---

## 10. Phase 6: 调度系统 ✅ 已完成

### 10.1 调度触发器类型

| 触发器 | 说明 | 配置参数 |
|--------|------|----------|
| `cron` | Cron表达式定时 | `cron_expression` (分 时 日 月 周) |
| `interval` | 固定间隔执行 | `interval_seconds` |
| `once` | 单次定时执行 | `run_at` (ISO时间) |
| `webhook` | HTTP请求触发 | `webhook_token`, `webhook_secret` |
| `file_watch` | 文件变化触发 | `watch_path`, `watch_pattern`, `watch_events` |
| `manual` | 手动触发 | 无 |

### 10.2 调度器核心功能

- **Cron表达式解析**: 支持通配符、步长、范围、列表等语法
- **重试机制**: 可配置最大重试次数和重试间隔
- **执行历史**: 记录每次执行的状态、耗时、错误信息
- **Webhook安全**: 支持令牌认证和密钥验证
- **文件监控**: 基于轮询的文件变化检测，支持递归监控

### 10.3 新增API端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/schedules` | 创建调度任务 |
| GET | `/api/schedules` | 获取调度列表 |
| GET | `/api/schedules/{id}` | 获取调度详情 |
| PUT | `/api/schedules/{id}` | 更新调度任务 |
| DELETE | `/api/schedules/{id}` | 删除调度任务 |
| POST | `/api/schedules/{id}/pause` | 暂停调度 |
| POST | `/api/schedules/{id}/resume` | 恢复调度 |
| POST | `/api/schedules/{id}/trigger` | 手动触发 |
| POST | `/api/webhooks/{token}` | Webhook触发 |
| GET | `/api/history` | 执行历史 |
| GET | `/api/scheduler/status` | 调度器状态 |
| POST | `/api/scheduler/start` | 启动调度器 |
| POST | `/api/scheduler/stop` | 停止调度器 |

### 10.4 前端调度管理

- 调度任务列表（卡片式展示）
- 新建调度弹窗（支持所有触发器类型配置）
- Cron表达式常用预设（每分钟、每小时、每天等）
- 调度任务操作（暂停、恢复、手动执行、删除）
- 执行历史查看（支持按任务过滤）
- 调度器启停控制

---

## 11. 后续扩展方向

1. **录制回放**: 录制用户操作自动生成流程
2. **AI增强**: 自然语言描述转流程、智能异常处理
3. **权限管理**: 用户认证、流程权限控制
4. **监控告警**: 执行监控、失败告警通知（邮件/钉钉/企微）
5. **集群调度**: 多节点分布式调度
6. **流程市场**: 社区共享流程模板

---

## 11. 文件结构

```
rpa-automation-tool/
├── rpa_engine/              # 核心引擎
│   ├── __init__.py
│   ├── __main__.py
│   ├── engine.py
│   ├── models/              # 数据模型
│   │   ├── schemas.py       # 流程、节点、调度等模型
│   │   └── context.py       # 执行上下文
│   ├── nodes/               # 节点实现 (43个)
│   │   ├── python_nodes.py
│   │   ├── file_nodes.py
│   │   ├── system_nodes.py
│   │   ├── logic_nodes.py
│   │   ├── sftp_nodes.py
│   │   ├── ftp_nodes.py
│   │   ├── xml_nodes.py
│   │   ├── math_nodes.py
│   │   ├── database_nodes.py
│   │   ├── excel_nodes.py
│   │   ├── web_nodes.py
│   │   ├── delay_nodes.py
│   │   └── phase5_nodes.py
│   ├── scheduler/           # 调度系统
│   │   ├── scheduler.py     # 调度引擎 (Cron、间隔、单次)
│   │   └── events.py        # 事件管理 (文件监控)
│   ├── api/                 # REST API
│   │   └── server.py        # FastAPI服务 (含调度API)
│   ├── static/              # 前端静态文件
│   │   ├── index.html       # 流程设计器+调度管理
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── utils/
├── tests/                   # 199个测试
│   ├── test_core_engine.py
│   ├── test_phase2_nodes.py
│   ├── test_phase3_nodes.py
│   ├── test_phase4_nodes.py
│   ├── test_phase5_nodes.py
│   └── test_phase6_scheduler.py
├── examples/
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

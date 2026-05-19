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
| Phase 3 | 前端设计器原型 (React/Vue + ReactFlow) | 📋 待开始 | 1 周 |
| Phase 4 | 测试完善 + 文档 + 生产部署 | 📋 待开始 | 1 周 |

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

## 10. 后续扩展方向

1. **更多节点类型**: Web操作、数据库操作、邮件发送、Excel处理
2. **调度系统**: 定时执行、触发器执行
3. **录制回放**: 录制用户操作自动生成流程
4. **AI增强**: 自然语言描述转流程、智能异常处理
5. **前端设计器**: 可视化流程编排界面
6. **权限管理**: 用户认证、流程权限控制
7. **监控告警**: 执行监控、失败告警

---

## 11. 文件结构

```
rpa-automation-tool/
├── rpa_engine/              # 核心引擎
│   ├── __init__.py
│   ├── __main__.py
│   ├── engine.py
│   ├── models/
│   ├── nodes/
│   ├── api/
│   └── utils/
├── tests/
├── examples/
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── README.md
└── MVP.md
```

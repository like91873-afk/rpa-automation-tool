# RPA自动化工具

轻量级RPA（机器人流程自动化）设计器和执行引擎，支持可视化流程编排和Python脚本执行。

## 功能特性

### 核心功能
- **流程设计器** - 可视化流程编排
- **执行引擎** - 流程调度和执行
- **变量管理** - 全局变量和节点间数据传递
- **REST API** - 完整的后端API接口

### 支持的节点类型

#### Python相关
- **Python代码执行** - 执行Python代码，支持变量传递
- **Python脚本执行** - 执行外部Python脚本文件

#### 文件操作
- **打开文件** - 使用默认程序或指定应用打开文件
- **读取文件** - 读取文件内容
- **写入文件** - 写入或追加内容到文件
- **列出目录** - 列出目录下的文件和子目录

#### 系统操作
- **执行命令行** - 支持CMD、PowerShell、Bash等
- **执行PowerShell** - 专门的PowerShell命令执行
- **获取电脑信息** - 获取环境变量、系统信息等

#### 网络操作
- **SFTP连接** - 创建SFTP连接
- **SFTP上传** - 上传文件到SFTP服务器
- **SFTP下载** - 从SFTP服务器下载文件
- **新建SFTP文件** - 在SFTP服务器上创建文件

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/like91873-afk/rpa-automation-tool.git
cd rpa-automation-tool

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 使用示例

#### 1. 启动API服务器

```bash
python -m rpa_engine serve --host 0.0.0.0 --port 8000
```

服务器启动后，可以访问 http://localhost:8000/docs 查看API文档。

#### 2. 创建示例流程

```bash
python -m rpa_engine sample --output sample.json
```

#### 3. 执行流程

```bash
python -m rpa_engine run sample.json --debug
```

#### 4. 验证流程

```bash
python -m rpa_engine validate sample.json
```

### Python API使用

```python
from rpa_engine import ExecutionEngine, Flow, NodeInstance

# 创建流程
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

# 执行流程
engine = ExecutionEngine()
result = engine.execute_flow(flow)

print(f"状态: {result.status}")
print(f"变量: {result.variables}")
```

### REST API使用

```bash
# 获取所有节点类型
curl http://localhost:8000/api/nodes

# 获取所有流程
curl http://localhost:8000/api/flows

# 创建流程
curl -X POST http://localhost:8000/api/flows \
  -H "Content-Type: application/json" \
  -d @sample.json

# 执行流程
curl -X POST http://localhost:8000/api/flows/sample-flow-001/execute \
  -H "Content-Type: application/json" \
  -d '{"variables": {}, "debug": true}'
```

## 项目结构

```
rpa-automation-tool/
├── rpa_engine/              # 核心引擎
│   ├── __init__.py         # 模块初始化
│   ├── __main__.py         # 命令行入口
│   ├── engine.py           # 执行引擎
│   ├── models/             # 数据模型
│   │   ├── __init__.py
│   │   ├── schemas.py      # Pydantic模型
│   │   └── context.py      # 执行上下文
│   ├── nodes/              # 节点实现
│   │   ├── __init__.py
│   │   ├── base.py         # 节点基类
│   │   ├── python_nodes.py # Python节点
│   │   ├── file_nodes.py   # 文件操作节点
│   │   ├── system_nodes.py # 系统操作节点
│   │   └── sftp_nodes.py   # SFTP节点
│   ├── api/                # REST API
│   │   ├── __init__.py
│   │   └── server.py       # FastAPI服务器
│   └── utils/              # 工具函数
│       └── __init__.py
├── tests/                  # 测试文件
│   └── test_engine.py
├── examples/               # 示例流程
│   ├── python_exec_example.json
│   └── file_operations_example.json
├── pyproject.toml          # 项目配置
├── requirements.txt        # 依赖列表
├── .gitignore             # Git忽略文件
└── README.md              # 项目文档
```

## 流程文件格式

流程使用JSON格式定义：

```json
{
  "id": "flow-id",
  "name": "流程名称",
  "description": "流程描述",
  "version": "1.0.0",
  "nodes": [
    {
      "id": "node-1",
      "type": "python_exec",
      "name": "节点名称",
      "inputs": {
        "python_code": "print('Hello')",
        "timeout": 1800
      },
      "position": {"x": 100, "y": 100}
    }
  ],
  "connections": [
    {
      "id": "conn-1",
      "source_node_id": "node-1",
      "target_node_id": "node-2"
    }
  ],
  "variables": {
    "global_var": "value"
  }
}
```

## 变量引用

在节点参数中可以使用变量引用：

```json
{
  "python_code": "print('${message}')",
  "file_path": "${output_dir}/result.txt"
}
```

## 开发指南

### 添加新节点

1. 在 `rpa_engine/nodes/` 目录下创建新的节点文件
2. 继承 `BaseNode` 类
3. 实现 `_create_definition()` 和 `execute()` 方法
4. 在 `rpa_engine/nodes/__init__.py` 中注册新节点

示例：

```python
from .base import BaseNode
from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType

class MyCustomNode(BaseNode):
    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.CUSTOM,
            name="自定义节点",
            description="我的自定义节点",
            inputs=[
                NodeInput(
                    name="input_param",
                    label="输入参数",
                    required=True
                )
            ],
            outputs=[
                NodeOutput(
                    key="output_result",
                    label="输出结果",
                    description="节点输出"
                )
            ]
        )

    def execute(self, inputs, context):
        input_param = self.get_required_input(inputs, "input_param")
        # 实现节点逻辑
        return {"output_result": f"处理结果: {input_param}"}
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_engine.py

# 带覆盖率运行
pytest --cov=rpa_engine
```

## 部署

### Docker部署

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "rpa_engine", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

构建并运行：

```bash
docker build -t rpa-automation-tool .
docker run -p 8000:8000 rpa-automation-tool
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

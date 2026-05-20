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
- **Python代码执行** (`python_exec`) - 执行Python代码，支持变量传递
- **Python脚本执行** (`python_script`) - 执行外部Python脚本文件

#### 文件操作
- **打开文件** (`file_open`) - 使用默认程序或指定应用打开文件
- **读取文件** (`file_read`) - 读取文件内容
- **写入文件** (`file_write`) - 写入或追加内容到文件
- **列出目录** (`directory_list`) - 列出目录下的文件和子目录
- **路径存在检查** (`path_exists`) - 检查路径是否存在并返回详细信息

#### 系统操作
- **执行命令行** (`system_cmd`) - 支持CMD、PowerShell、Bash等
- **执行PowerShell** (`powershell`) - 专门的PowerShell命令执行
- **获取电脑信息** (`computer_info`) - 获取环境变量、系统信息等

#### 逻辑控制 (Phase 2)
- **条件判断** (`condition`) - 支持表达式、比较运算、变量检查三种条件类型
- **循环** (`loop`) - 支持范围循环、遍历集合、计数循环

#### 数据处理 (Phase 2)
- **数值运算** (`math_operation`) - 支持加减乘除、取模、幂运算、平方根、绝对值、取整等
- **字符串操作** (`string_operation`) - 支持拼接、分割、替换、大小写转换、包含检查、格式化等

#### 网络操作
- **SFTP连接** (`sftp_connect`) - 创建SFTP连接
- **SFTP上传** (`sftp_upload`) - 上传文件到SFTP服务器
- **SFTP下载** (`sftp_download`) - 从SFTP服务器下载文件
- **新建SFTP文件** (`sftp_new_file`) - 在SFTP服务器上创建文件
- **SFTP写入文件** (`sftp_write_file`) - 向SFTP文件写入内容，支持追加/覆盖模式

#### FTP操作 (Phase 3)
- **FTP连接** (`ftp_connect`) - 创建FTP连接对象
- **FTP查看目录** (`ftp_list_dir`) - 查看FTP服务器目录下的文件列表

#### 数据处理
- **XML保存** (`xml_save`) - 将数据保存为XML文件，支持多种编码和存在处理方式

#### 数据库操作 (Phase 4)
- **数据库连接** (`db_connect`) - 创建SQLite数据库连接
- **数据库查询** (`db_query`) - 执行SELECT查询语句，返回结果列表
- **数据库执行** (`db_execute`) - 执行INSERT/UPDATE/DELETE等SQL语句

#### Excel操作 (Phase 4)
- **读取Excel** (`excel_read`) - 读取Excel文件数据，支持表头和范围选择
- **写入Excel** (`excel_write`) - 向Excel文件写入数据，支持追加模式
- **创建Excel** (`excel_create`) - 创建新的Excel文件，支持多工作表

#### Web操作 (Phase 4)
- **HTTP请求** (`http_request`) - 发送HTTP请求，支持GET/POST/PUT/DELETE等
- **网页抓取** (`web_scrape`) - 抓取网页内容，提取文本或HTML

#### 控制流 (Phase 4)
- **延迟执行** (`delay`) - 暂停流程执行指定时间
- **等待条件** (`wait_for`) - 等待变量存在/为真/表达式成立

#### 邮件操作 (Phase 5)
- **邮箱连接** (`email_connect`) - 创建IMAP邮箱连接，支持SSL加密
- **邮件获取** (`email_fetch`) - 从邮箱获取邮件列表，支持搜索条件
- **邮件发送** (`email_send`) - 通过SMTP发送邮件，支持TLS加密

#### 时间处理 (Phase 5)
- **时间获取** (`time_get`) - 获取当前时间、时间戳、年月日时分秒，支持时区
- **时间处理** (`time_process`) - 时间加减运算和格式转换

#### 文件压缩 (Phase 5)
- **文件压缩** (`file_compress`) - 将文件/目录压缩为zip格式，支持压缩级别
- **文件解压** (`file_decompress`) - 解压zip文件，支持覆盖控制

#### PDF解析 (Phase 5)
- **PDF解析** (`pdf_parse`) - 提取PDF文件文本内容，支持页码范围

#### FTP/SFTP增强 (Phase 5)
- **FTP删除** (`ftp_delete`) - 删除FTP服务器上的文件
- **SFTP创建目录** (`sftp_create_dir`) - 在SFTP服务器上创建目录，支持递归创建

#### 数据处理 (Phase 5)
- **公式计算** (`formula`) - 数学表达式计算，支持${var}变量引用语法

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

#### 基础流程

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

#### 条件判断示例

```python
from rpa_engine import Flow, NodeInstance, Connection, ExecutionEngine

flow = Flow(
    id="condition-flow",
    name="条件判断流程",
    nodes=[
        NodeInstance(
            id="node-calc",
            type="math_operation",
            name="计算",
            inputs={
                "operation": "multiply",
                "operand_a": 10,
                "operand_b": 5
            }
        ),
        NodeInstance(
            id="node-check",
            type="condition",
            name="判断大小",
            inputs={
                "condition_type": "expression",
                "expression": "result > 30"
            }
        )
    ],
    connections=[
        Connection(id="conn-1", source_node_id="node-calc", target_node_id="node-check")
    ]
)

engine = ExecutionEngine()
result = engine.execute_flow(flow)
print(f"条件结果: {result.variables.get('result')}")  # True
```

#### 字符串处理示例

```python
from rpa_engine import Flow, NodeInstance, ExecutionEngine

flow = Flow(
    id="string-flow",
    name="字符串处理流程",
    nodes=[
        NodeInstance(
            id="node-1",
            type="string_operation",
            name="分割字符串",
            inputs={
                "operation": "split",
                "input_string": "apple,banana,cherry",
                "param1": ","
            }
        ),
        NodeInstance(
            id="node-2",
            type="math_operation",
            name="计算长度",
            inputs={
                "operation": "multiply",
                "operand_a": "${count}",
                "operand_b": 2
            }
        )
    ],
    connections=[
        Connection(id="conn-1", source_node_id="node-1", target_node_id="node-2")
    ]
)

engine = ExecutionEngine()
result = engine.execute_flow(flow)
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
│   │   ├── sftp_nodes.py   # SFTP节点
│   │   ├── ftp_nodes.py    # FTP节点
│   │   ├── xml_nodes.py    # XML操作节点
│   │   ├── logic_nodes.py  # 逻辑控制节点（条件/循环）
│   │   ├── math_nodes.py   # 数学运算节点
│   │   ├── string_nodes.py # 字符串操作节点
│   │   ├── database_nodes.py # 数据库操作节点 (Phase 4)
│   │   ├── excel_nodes.py  # Excel操作节点 (Phase 4)
│   │   ├── web_nodes.py    # Web操作节点 (Phase 4)
│   │   ├── delay_nodes.py  # 延迟/等待节点 (Phase 4)
│   │   └── phase5_nodes.py # Phase 5节点（公式/邮件/时间/压缩/PDF）
│   ├── api/                # REST API
│   │   ├── __init__.py
│   │   └── server.py       # FastAPI服务器
│   ├── static/             # 前端静态文件 (Phase 4)
│   │   ├── index.html      # 前端设计器页面
│   │   ├── css/style.css   # 样式表
│   │   └── js/app.js       # 前端应用
│   └── utils/              # 工具函数
│       └── __init__.py
├── tests/                  # 测试文件
│   ├── test_engine.py      # 核心引擎测试
│   ├── test_phase2_nodes.py # Phase 2节点测试
│   ├── test_phase3_nodes.py # Phase 3节点测试
│   ├── test_phase4_nodes.py # Phase 4节点测试
│   └── test_phase5_nodes.py # Phase 5节点测试
├── examples/               # 示例流程
├── pyproject.toml          # 项目配置
├── .gitignore             # Git忽略文件
├── README.md              # 项目文档
└── MVP.md                 # MVP设计文档
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
      "type": "math_operation",
      "name": "计算",
      "inputs": {
        "operation": "add",
        "operand_a": 10,
        "operand_b": 20
      },
      "position": {"x": 100, "y": 100}
    },
    {
      "id": "node-2",
      "type": "condition",
      "name": "判断",
      "inputs": {
        "condition_type": "expression",
        "expression": "result > 25"
      },
      "position": {"x": 300, "y": 100}
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
  "file_path": "${output_dir}/result.txt",
  "operand_a": "${previous_result}"
}
```

## 节点详细说明

### 条件判断节点 (`condition`)

支持三种条件类型：

| 条件类型 | 说明 | 必需参数 |
|---------|------|---------|
| `expression` | Python布尔表达式 | `expression` |
| `compare` | 两个值的比较 | `left_value`, `operator`, `right_value` |
| `variable_check` | 检查变量是否存在且为真 | `variable_name` |

比较运算符：`==`, `!=`, `>`, `>=`, `<`, `<=`

### 循环节点 (`loop`)

支持三种循环类型：

| 循环类型 | 说明 | 必需参数 |
|---------|------|---------|
| `range` | 范围循环 | `start_num`, `end_num`, `step` |
| `foreach` | 遍历集合 | `collection` |
| `count` | 计数循环 | `count` |

### 数学运算节点 (`math_operation`)

支持的运算类型：

| 运算 | 说明 | 需要操作数B |
|-----|------|-----------|
| `add` | 加法 | ✓ |
| `subtract` | 减法 | ✓ |
| `multiply` | 乘法 | ✓ |
| `divide` | 除法 | ✓ |
| `mod` | 取模 | ✓ |
| `power` | 幂运算 | ✓ |
| `sqrt` | 平方根 | ✗ |
| `abs` | 绝对值 | ✗ |
| `round` | 四舍五入 | ✗ |
| `floor` | 向下取整 | ✗ |
| `ceil` | 向上取整 | ✗ |
| `min` | 最小值 | ✓ |
| `max` | 最大值 | ✓ |

### 字符串操作节点 (`string_operation`)

支持的操作类型：

| 操作 | 说明 | 参数1 | 参数2 |
|-----|------|-------|-------|
| `concat` | 拼接 | 拼接字符串 | - |
| `split` | 分割 | 分隔符 | - |
| `replace` | 替换 | 查找 | 替换为 |
| `upper` | 转大写 | - | - |
| `lower` | 转小写 | - | - |
| `trim` | 去除空白 | - | - |
| `contains` | 包含检查 | 子串 | - |
| `startswith` | 前缀检查 | 前缀 | - |
| `endswith` | 后缀检查 | 后缀 | - |
| `format` | 格式化 | 参数 | - |
| `length` | 长度 | - | - |
| `substring` | 截取 | 起始 | 结束 |
| `reverse` | 反转 | - | - |

## 开发指南

### 添加新节点

1. 在 `rpa_engine/nodes/` 目录下创建新的节点文件
2. 继承 `BaseNode` 类
3. 实现 `_create_definition()` 和 `execute()` 方法
4. 在 `rpa_engine/nodes/__init__.py` 中注册新节点
5. 在 `rpa_engine/models/schemas.py` 的 `NodeType` 枚举中添加类型

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

## Web前端设计器

项目包含一个可视化流程设计器，通过浏览器访问即可使用：

```bash
# 启动API服务器
python -m rpa_engine serve --host 0.0.0.0 --port 8000

# 浏览器访问
# http://localhost:8000
```

### 功能特性
- 🎨 可视化流程编排
- 🖱️ 拖拽式节点添加
- 🔗 节点连线
- ⚙️ 属性配置面板
- 💾 流程保存/加载
- ▶️ 一键执行流程
- 📊 执行结果展示

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

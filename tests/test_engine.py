"""
RPA引擎 - 核心功能测试
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa_engine import (
    ExecutionEngine,
    Flow,
    NodeInstance,
    Connection,
    create_sample_flow,
    validate_flow,
)


@pytest.fixture
def engine():
    """创建执行引擎实例"""
    return ExecutionEngine()


@pytest.fixture
def sample_flow():
    """创建示例流程"""
    return create_sample_flow()


class TestExecutionEngine:
    """执行引擎测试"""

    def test_create_engine(self, engine):
        """测试创建执行引擎"""
        assert engine is not None

    def test_execute_simple_flow(self, engine):
        """测试执行简单流程"""
        flow = Flow(
            id="test-flow-1",
            name="测试流程",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="python_exec",
                    name="测试Python执行",
                    inputs={
                        "python_code": "result = 1 + 1\nprint(f'结果: {result}')",
                        "timeout": 1800
                    }
                )
            ],
            connections=[]
        )

        result = engine.execute_flow(flow)
        assert result.status == "completed"
        assert result.error is None

    def test_execute_with_variables(self, engine):
        """测试带变量的流程执行"""
        flow = Flow(
            id="test-flow-2",
            name="变量测试流程",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="python_exec",
                    name="变量测试",
                    inputs={
                        "python_code": "print(f'变量值: {test_var}')\nresult = test_var * 2",
                        "timeout": 1800
                    }
                )
            ],
            connections=[]
        )

        result = engine.execute_flow(
            flow=flow,
            initial_variables={"test_var": "hello"}
        )

        assert result.status == "completed"
        assert "hellohello" in str(result.variables.get("result", ""))

    def test_execute_multiple_nodes(self, engine):
        """测试多节点流程执行"""
        flow = Flow(
            id="test-flow-3",
            name="多节点测试",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="python_exec",
                    name="第一个节点",
                    inputs={
                        "python_code": "x = 10\nprint(f'节点1: x = {x}')",
                        "timeout": 1800
                    }
                ),
                NodeInstance(
                    id="node-2",
                    type="python_exec",
                    name="第二个节点",
                    inputs={
                        "python_code": "y = x * 2\nprint(f'节点2: y = {y}')",
                        "timeout": 1800
                    }
                )
            ],
            connections=[
                Connection(
                    id="conn-1",
                    source_node_id="node-1",
                    target_node_id="node-2"
                )
            ]
        )

        result = engine.execute_flow(flow)
        assert result.status == "completed"
        assert len(result.node_logs) == 2

    def test_execute_with_file_operations(self, engine):
        """测试文件操作流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "test_output.txt")

            flow = Flow(
                id="test-flow-4",
                name="文件操作测试",
                nodes=[
                    NodeInstance(
                        id="node-1",
                        type="file_write",
                        name="写入文件",
                        inputs={
                            "file_path": output_file,
                            "content": "Hello, RPA!",
                            "mode": "overwrite"
                        }
                    )
                ],
                connections=[]
            )

            result = engine.execute_flow(flow)
            assert result.status == "completed"
            assert os.path.exists(output_file)

            with open(output_file, "r") as f:
                content = f.read()
            assert content == "Hello, RPA!"

    def test_flow_validation(self):
        """测试流程验证"""
        # 有效流程
        valid_flow = create_sample_flow()
        errors = validate_flow(valid_flow)
        assert len(errors) == 0

        # 无效流程（重复节点ID）
        invalid_flow = Flow(
            id="invalid-flow",
            name="无效流程",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="python_exec",
                    name="节点1",
                    inputs={"python_code": "print('test')"}
                ),
                NodeInstance(
                    id="node-1",  # 重复ID
                    type="python_exec",
                    name="节点2",
                    inputs={"python_code": "print('test')"}
                )
            ],
            connections=[]
        )

        errors = validate_flow(invalid_flow)
        assert len(errors) > 0
        assert any("重复" in error for error in errors)

    def test_sample_flow_creation(self):
        """测试示例流程创建"""
        flow = create_sample_flow()
        assert flow.id == "sample-flow-001"
        assert flow.name == "示例流程"
        assert len(flow.nodes) > 0


class TestPythonExecution:
    """Python代码执行测试"""

    def test_basic_python_execution(self, engine):
        """测试基础Python执行"""
        flow = Flow(
            id="python-test-1",
            name="Python基础测试",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="python_exec",
                    name="基础计算",
                    inputs={
                        "python_code": "result = 2 + 3\nprint(f'2 + 3 = {result}')",
                        "timeout": 1800
                    }
                )
            ],
            connections=[]
        )

        result = engine.execute_flow(flow)
        assert result.status == "completed"
        assert result.variables.get("result") == 5

    def test_python_with_imports(self, engine):
        """测试Python导入模块"""
        flow = Flow(
            id="python-test-2",
            name="Python导入测试",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="python_exec",
                    name="导入测试",
                    inputs={
                        "python_code": "import json\nimport datetime\n\nnow = datetime.datetime.now()\ndata = {\"time\": now.isoformat()}\nresult = json.dumps(data)\nprint(result)",
                        "timeout": 1800
                    }
                )
            ],
            connections=[]
        )

        result = engine.execute_flow(flow)
        assert result.status == "completed"
        assert result.variables.get("result") is not None

    def test_python_error_handling(self, engine):
        """测试Python错误处理"""
        flow = Flow(
            id="python-test-3",
            name="Python错误测试",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="python_exec",
                    name="错误测试",
                    inputs={
                        "python_code": "raise ValueError('测试错误')",
                        "timeout": 1800
                    }
                )
            ],
            connections=[]
        )

        result = engine.execute_flow(flow)
        assert result.status == "failed"
        assert result.error is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

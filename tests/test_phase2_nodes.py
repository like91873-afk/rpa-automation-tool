"""
RPA引擎 - Phase 2节点测试

测试条件节点、循环节点、数学运算节点、字符串操作节点
"""

import pytest
from rpa_engine import (
    ExecutionEngine,
    Flow,
    NodeInstance,
    Connection,
    NodeType,
)
from rpa_engine.nodes.logic_nodes import ConditionNode, LoopNode
from rpa_engine.nodes.math_nodes import MathOperationNode
from rpa_engine.nodes.string_nodes import StringOperationNode
from rpa_engine.models.context import ExecutionContext


@pytest.fixture
def engine():
    """创建执行引擎实例"""
    return ExecutionEngine()


@pytest.fixture
def context():
    """创建执行上下文实例"""
    return ExecutionContext()


class TestConditionNode:
    """条件节点测试"""

    def test_condition_node_definition(self):
        """测试条件节点定义"""
        node = ConditionNode()
        defn = node.definition
        assert defn.type == NodeType.CONDITION
        assert defn.name == "条件判断"
        assert len(defn.inputs) > 0
        assert len(defn.outputs) > 0

    def test_expression_condition_true(self, context):
        """测试表达式条件为真"""
        node = ConditionNode()
        result = node.execute({
            "condition_type": "expression",
            "expression": "1 + 1 == 2"
        }, context)
        assert result["result"] is True
        assert result["true_path"] is True
        assert result["false_path"] is False

    def test_expression_condition_false(self, context):
        """测试表达式条件为假"""
        node = ConditionNode()
        result = node.execute({
            "condition_type": "expression",
            "expression": "1 + 1 == 3"
        }, context)
        assert result["result"] is False
        assert result["true_path"] is False
        assert result["false_path"] is True

    def test_expression_with_variables(self, context):
        """测试带变量的条件表达式"""
        context.set_variable("status", "active")
        context.set_variable("count", 5)
        node = ConditionNode()
        result = node.execute({
            "condition_type": "expression",
            "expression": "status == 'active' and count > 3"
        }, context)
        assert result["result"] is True

    def test_compare_condition(self, context):
        """测试比较条件"""
        node = ConditionNode()
        result = node.execute({
            "condition_type": "compare",
            "left_value": "10",
            "operator": ">",
            "right_value": "5"
        }, context)
        assert result["result"] is True

    def test_compare_condition_equal(self, context):
        """测试相等比较"""
        node = ConditionNode()
        result = node.execute({
            "condition_type": "compare",
            "left_value": "hello",
            "operator": "==",
            "right_value": "hello"
        }, context)
        assert result["result"] is True

    def test_variable_check_exists(self, context):
        """测试变量存在检查"""
        context.set_variable("my_var", "value")
        node = ConditionNode()
        result = node.execute({
            "condition_type": "variable_check",
            "variable_name": "my_var"
        }, context)
        assert result["result"] is True

    def test_variable_check_not_exists(self, context):
        """测试变量不存在检查"""
        node = ConditionNode()
        result = node.execute({
            "condition_type": "variable_check",
            "variable_name": "nonexistent_var"
        }, context)
        assert result["result"] is False

    def test_condition_in_flow(self, engine):
        """测试条件节点在流程中的执行"""
        flow = Flow(
            id="condition-test",
            name="条件测试流程",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="condition",
                    name="判断条件",
                    inputs={
                        "condition_type": "expression",
                        "expression": "True"
                    }
                )
            ],
            connections=[]
        )
        result = engine.execute_flow(flow)
        assert result.status.value == "completed"
        assert result.variables.get("result") is True


class TestLoopNode:
    """循环节点测试"""

    def test_loop_node_definition(self):
        """测试循环节点定义"""
        node = LoopNode()
        defn = node.definition
        assert defn.type == NodeType.LOOP
        assert defn.name == "循环"

    def test_range_loop(self, context):
        """测试范围循环"""
        node = LoopNode()
        result = node.execute({
            "loop_type": "range",
            "start_num": 0,
            "end_num": 5,
            "step": 1
        }, context)
        assert result["items"] == [0, 1, 2, 3, 4]
        assert result["count"] == 5
        assert result["current_item"] == 4
        assert result["current_index"] == 4
        assert result["is_done"] is True

    def test_range_loop_with_step(self, context):
        """测试带步长的范围循环"""
        node = LoopNode()
        result = node.execute({
            "loop_type": "range",
            "start_num": 0,
            "end_num": 10,
            "step": 2
        }, context)
        assert result["items"] == [0, 2, 4, 6, 8]
        assert result["count"] == 5

    def test_foreach_loop(self, context):
        """测试遍历循环"""
        node = LoopNode()
        result = node.execute({
            "loop_type": "foreach",
            "collection": [1, "two", 3, "four"]
        }, context)
        assert result["items"] == [1, "two", 3, "four"]
        assert result["count"] == 4
        assert result["current_item"] == "four"

    def test_count_loop(self, context):
        """测试计数循环"""
        node = LoopNode()
        result = node.execute({
            "loop_type": "count",
            "count": 3
        }, context)
        assert result["items"] == [0, 1, 2]
        assert result["count"] == 3

    def test_loop_zero_step_error(self, context):
        """测试步长为零的错误"""
        node = LoopNode()
        with pytest.raises(ValueError, match="步长不能为0"):
            node.execute({
                "loop_type": "range",
                "start_num": 0,
                "end_num": 10,
                "step": 0
            }, context)

    def test_loop_max_iterations_exceeded(self, context):
        """测试超过最大循环次数"""
        node = LoopNode()
        with pytest.raises(ValueError, match="超过最大限制"):
            node.execute({
                "loop_type": "range",
                "start_num": 0,
                "end_num": 10000,
                "step": 1,
                "max_iterations": 100
            }, context)

    def test_loop_in_flow(self, engine):
        """测试循环节点在流程中的执行"""
        flow = Flow(
            id="loop-test",
            name="循环测试流程",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="loop",
                    name="范围循环",
                    inputs={
                        "loop_type": "range",
                        "start_num": 0,
                        "end_num": 3,
                        "step": 1
                    }
                )
            ],
            connections=[]
        )
        result = engine.execute_flow(flow)
        assert result.status.value == "completed"
        assert result.variables.get("count") == 3


class TestMathOperationNode:
    """数学运算节点测试"""

    def test_math_node_definition(self):
        """测试数学节点定义"""
        node = MathOperationNode()
        defn = node.definition
        assert defn.type == NodeType.MATH_OPERATION
        assert defn.name == "数值运算"

    def test_add(self, context):
        """测试加法"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "add",
            "operand_a": 10,
            "operand_b": 5
        }, context)
        assert result["result"] == 15

    def test_subtract(self, context):
        """测试减法"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "subtract",
            "operand_a": 10,
            "operand_b": 3
        }, context)
        assert result["result"] == 7

    def test_multiply(self, context):
        """测试乘法"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "multiply",
            "operand_a": 4,
            "operand_b": 5
        }, context)
        assert result["result"] == 20

    def test_divide(self, context):
        """测试除法"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "divide",
            "operand_a": 10,
            "operand_b": 3
        }, context)
        assert abs(result["result"] - 3.3333333333333335) < 1e-10

    def test_divide_integer(self, context):
        """测试整除"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "divide",
            "operand_a": 10,
            "operand_b": 2
        }, context)
        assert result["result"] == 5.0

    def test_divide_by_zero(self, context):
        """测试除零错误"""
        node = MathOperationNode()
        with pytest.raises(ValueError, match="除数不能为零"):
            node.execute({
                "operation": "divide",
                "operand_a": 10,
                "operand_b": 0
            }, context)

    def test_mod(self, context):
        """测试取模"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "mod",
            "operand_a": 10,
            "operand_b": 3
        }, context)
        assert result["result"] == 1

    def test_power(self, context):
        """测试幂运算"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "power",
            "operand_a": 2,
            "operand_b": 10
        }, context)
        assert result["result"] == 1024

    def test_sqrt(self, context):
        """测试平方根"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "sqrt",
            "operand_a": 16
        }, context)
        assert result["result"] == 4.0

    def test_abs(self, context):
        """测试绝对值"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "abs",
            "operand_a": -42
        }, context)
        assert result["result"] == 42

    def test_round(self, context):
        """测试四舍五入"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "round",
            "operand_a": 3.14159,
            "precision": 2
        }, context)
        assert result["result"] == 3.14

    def test_floor(self, context):
        """测试向下取整"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "floor",
            "operand_a": 3.7
        }, context)
        assert result["result"] == 3

    def test_ceil(self, context):
        """测试向上取整"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "ceil",
            "operand_a": 3.2
        }, context)
        assert result["result"] == 4

    def test_min(self, context):
        """测试最小值"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "min",
            "operand_a": 10,
            "operand_b": 5
        }, context)
        assert result["result"] == 5

    def test_max(self, context):
        """测试最大值"""
        node = MathOperationNode()
        result = node.execute({
            "operation": "max",
            "operand_a": 10,
            "operand_b": 5
        }, context)
        assert result["result"] == 10

    def test_math_in_flow(self, engine):
        """测试数学运算在流程中执行"""
        flow = Flow(
            id="math-test",
            name="数学运算测试",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="math_operation",
                    name="加法",
                    inputs={
                        "operation": "add",
                        "operand_a": 100,
                        "operand_b": 200
                    }
                )
            ],
            connections=[]
        )
        result = engine.execute_flow(flow)
        assert result.status.value == "completed"
        assert result.variables.get("result") == 300


class TestStringOperationNode:
    """字符串操作节点测试"""

    def test_string_node_definition(self):
        """测试字符串节点定义"""
        node = StringOperationNode()
        defn = node.definition
        assert defn.type == NodeType.STRING_OPERATION
        assert defn.name == "字符串操作"

    def test_concat(self, context):
        """测试字符串拼接"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "concat",
            "input_string": "Hello",
            "param1": "World",
            "separator": " "
        }, context)
        assert result["result"] == "Hello World"

    def test_split(self, context):
        """测试字符串分割"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "split",
            "input_string": "a,b,c,d",
            "param1": ","
        }, context)
        assert result["result"] == ["a", "b", "c", "d"]

    def test_replace(self, context):
        """测试字符串替换"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "replace",
            "input_string": "Hello World",
            "param1": "World",
            "param2": "Python"
        }, context)
        assert result["result"] == "Hello Python"

    def test_upper(self, context):
        """测试转大写"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "upper",
            "input_string": "hello world"
        }, context)
        assert result["result"] == "HELLO WORLD"

    def test_lower(self, context):
        """测试转小写"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "lower",
            "input_string": "HELLO WORLD"
        }, context)
        assert result["result"] == "hello world"

    def test_trim(self, context):
        """测试去除空白"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "trim",
            "input_string": "  hello  "
        }, context)
        assert result["result"] == "hello"

    def test_contains_true(self, context):
        """测试包含检查（真）"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "contains",
            "input_string": "Hello World",
            "param1": "World"
        }, context)
        assert result["result"] is True

    def test_contains_false(self, context):
        """测试包含检查（假）"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "contains",
            "input_string": "Hello World",
            "param1": "Python"
        }, context)
        assert result["result"] is False

    def test_startswith(self, context):
        """测试前缀检查"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "startswith",
            "input_string": "Hello World",
            "param1": "Hello"
        }, context)
        assert result["result"] is True

    def test_endswith(self, context):
        """测试后缀检查"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "endswith",
            "input_string": "Hello World",
            "param1": "World"
        }, context)
        assert result["result"] is True

    def test_length(self, context):
        """测试长度"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "length",
            "input_string": "Hello"
        }, context)
        assert result["result"] == 5

    def test_substring(self, context):
        """测试子串截取"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "substring",
            "input_string": "Hello World",
            "param1": "0",
            "param2": "5"
        }, context)
        assert result["result"] == "Hello"

    def test_reverse(self, context):
        """测试字符串反转"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "reverse",
            "input_string": "Hello"
        }, context)
        assert result["result"] == "olleH"

    def test_format_positional(self, context):
        """测试位置格式化"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "format",
            "input_string": "Hello {}, you are {} years old",
            "param1": '["Alice", 25]'
        }, context)
        assert result["result"] == "Hello Alice, you are 25 years old"

    def test_format_keyword(self, context):
        """测试关键字格式化"""
        node = StringOperationNode()
        result = node.execute({
            "operation": "format",
            "input_string": "Hello {name}, welcome to {place}",
            "param1": '{"name": "Alice", "place": "Wonderland"}'
        }, context)
        assert result["result"] == "Hello Alice, welcome to Wonderland"

    def test_string_in_flow(self, engine):
        """测试字符串操作在流程中执行"""
        flow = Flow(
            id="string-test",
            name="字符串测试",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="string_operation",
                    name="拼接",
                    inputs={
                        "operation": "upper",
                        "input_string": "hello rpa"
                    }
                )
            ],
            connections=[]
        )
        result = engine.execute_flow(flow)
        assert result.status.value == "completed"
        assert result.variables.get("result") == "HELLO RPA"


class TestPhase2Integration:
    """Phase 2功能集成测试"""

    def test_math_then_condition_flow(self, engine):
        """测试数学运算+条件判断流程"""
        flow = Flow(
            id="integration-test-1",
            name="数学+条件集成测试",
            nodes=[
                NodeInstance(
                    id="node-math",
                    type="math_operation",
                    name="计算",
                    inputs={
                        "operation": "add",
                        "operand_a": 10,
                        "operand_b": 20
                    }
                ),
                NodeInstance(
                    id="node-condition",
                    type="condition",
                    name="判断",
                    inputs={
                        "condition_type": "expression",
                        "expression": "result > 20"
                    }
                )
            ],
            connections=[
                Connection(
                    id="conn-1",
                    source_node_id="node-math",
                    target_node_id="node-condition"
                )
            ]
        )
        result = engine.execute_flow(flow)
        assert result.status.value == "completed"
        assert result.variables.get("result") is True

    def test_string_and_loop_flow(self, engine):
        """测试字符串+循环流程"""
        flow = Flow(
            id="integration-test-2",
            name="字符串+循环集成测试",
            nodes=[
                NodeInstance(
                    id="node-string",
                    type="string_operation",
                    name="分割字符串",
                    inputs={
                        "operation": "split",
                        "input_string": "apple,banana,cherry",
                        "param1": ","
                    }
                ),
                NodeInstance(
                    id="node-loop",
                    type="loop",
                    name="遍历列表",
                    inputs={
                        "loop_type": "foreach",
                        "collection": "${result}"
                    }
                )
            ],
            connections=[
                Connection(
                    id="conn-1",
                    source_node_id="node-string",
                    target_node_id="node-loop"
                )
            ]
        )
        result = engine.execute_flow(flow)
        assert result.status.value == "completed"
        assert result.variables.get("count") == 3

    def test_node_registry_completeness(self):
        """测试节点注册表完整性"""
        from rpa_engine.nodes import NODE_REGISTRY, get_all_node_definitions

        expected_nodes = [
            "python_exec", "python_script",
            "file_open", "file_read", "file_write", "directory_list", "path_exists",
            "system_cmd", "powershell", "computer_info",
            "condition", "loop",
            "sftp_connect", "sftp_upload", "sftp_download", "sftp_new_file", "sftp_write_file",
            "ftp_connect", "ftp_list_dir",
            "xml_save", "math_operation", "string_operation",
        ]

        for node_type in expected_nodes:
            assert node_type in NODE_REGISTRY, f"节点类型 {node_type} 未注册"

        definitions = get_all_node_definitions()
        assert len(definitions) == len(expected_nodes)

    def test_node_type_enum_completeness(self):
        """测试NodeType枚举完整性"""
        expected_types = [
            "python_exec", "python_script",
            "file_open", "file_read", "file_write", "directory_list", "path_exists",
            "system_cmd", "powershell", "computer_info",
            "condition", "loop",
            "sftp_connect", "sftp_upload", "sftp_download", "sftp_new_file", "sftp_write_file",
            "ftp_connect", "ftp_list_dir",
            "xml_save", "math_operation", "string_operation",
        ]

        for type_value in expected_types:
            assert hasattr(NodeType, type_value.upper()) or \
                   any(e.value == type_value for e in NodeType), \
                   f"NodeType枚举缺少: {type_value}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

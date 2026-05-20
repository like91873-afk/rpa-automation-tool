"""
逻辑控制节点

提供条件判断和循环控制功能
"""

import operator
from typing import Any, Dict

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


# 支持的比较运算符
COMPARISON_OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}


class ConditionNode(BaseNode):
    """
    条件判断节点

    根据条件表达式返回布尔结果，支持多种条件类型

    参数说明:
    - condition_type: 条件类型（expression/compare/variable_check）
    - expression: Python布尔表达式（condition_type为expression时使用）
    - left_value: 左侧比较值
    - operator: 比较运算符（==, !=, >, >=, <, <=）
    - right_value: 右侧比较值
    - variable_name: 变量名（condition_type为variable_check时使用）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.CONDITION,
            name="条件判断",
            description="根据条件表达式判断并返回布尔结果",
            category="逻辑控制",
            inputs=[
                NodeInput(
                    name="condition_type",
                    label="条件类型",
                    type=InputType.DROPDOWN,
                    required=True,
                    default="expression",
                    options=["expression", "compare", "variable_check"],
                    description="条件判断类型"
                ),
                NodeInput(
                    name="expression",
                    label="布尔表达式",
                    type=InputType.CODE,
                    required=False,
                    description="Python布尔表达式，如: len(items) > 0 and status == 'active'"
                ),
                NodeInput(
                    name="left_value",
                    label="左侧值",
                    type=InputType.TEXT,
                    required=False,
                    description="比较运算的左侧值"
                ),
                NodeInput(
                    name="operator",
                    label="比较运算符",
                    type=InputType.DROPDOWN,
                    required=False,
                    default="==",
                    options=["==", "!=", ">", ">=", "<", "<="],
                    description="比较运算符"
                ),
                NodeInput(
                    name="right_value",
                    label="右侧值",
                    type=InputType.TEXT,
                    required=False,
                    description="比较运算的右侧值"
                ),
                NodeInput(
                    name="variable_name",
                    label="变量名",
                    type=InputType.TEXT,
                    required=False,
                    description="要检查的变量名（variable_check类型时使用）"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="result",
                    label="判断结果",
                    description="条件判断的布尔结果（True/False）"
                ),
                NodeOutput(
                    key="true_path",
                    label="为真时的值",
                    description="条件为True时的输出"
                ),
                NodeOutput(
                    key="false_path",
                    label="为假时的值",
                    description="条件为False时的输出"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """执行条件判断"""
        condition_type = self.get_input_value(inputs, "condition_type", "expression")

        result = False

        if condition_type == "expression":
            expression = self.get_required_input(inputs, "expression")
            expression = context.resolve_variables(expression)
            # 安全地执行布尔表达式
            result = self._eval_expression(expression, context)

        elif condition_type == "compare":
            left_value = self.get_input_value(inputs, "left_value", "")
            op = self.get_input_value(inputs, "operator", "==")
            right_value = self.get_input_value(inputs, "right_value", "")

            left_value = context.resolve_variables(str(left_value))
            right_value = context.resolve_variables(str(right_value))

            # 尝试类型转换
            left_value = self._try_convert_type(left_value)
            right_value = self._try_convert_type(right_value)

            if op not in COMPARISON_OPERATORS:
                raise ValueError(f"不支持的比较运算符: {op}")

            result = COMPARISON_OPERATORS[op](left_value, right_value)

        elif condition_type == "variable_check":
            var_name = self.get_required_input(inputs, "variable_name")
            var_name = context.resolve_variables(var_name)
            # 检查变量是否存在且为真值
            result = context.has_variable(var_name) and bool(context.get_variable(var_name))

        else:
            raise ValueError(f"不支持的条件类型: {condition_type}")

        return self.create_output(
            result=result,
            true_path=result,
            false_path=not result
        )

    def _eval_expression(self, expression: str, context: ExecutionContext) -> bool:
        """安全地评估布尔表达式"""
        # 构建安全的执行环境
        safe_globals = {
            "__builtins__": {
                "len": len,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
                "abs": abs,
                "min": min,
                "max": max,
                "sum": sum,
                "any": any,
                "all": all,
                "True": True,
                "False": False,
                "None": None,
            }
        }
        safe_globals.update(context.variables)

        try:
            result = eval(expression, safe_globals, {})
            return bool(result)
        except Exception as e:
            raise ValueError(f"条件表达式执行失败: {str(e)}")

    def _try_convert_type(self, value: str) -> Any:
        """尝试将字符串值转换为合适的类型"""
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        if value.lower() == "none":
            return None

        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            pass

        return value


class LoopNode(BaseNode):
    """
    循环节点

    支持遍历列表、范围计数等循环操作

    参数说明:
    - loop_type: 循环类型（foreach/range/count）
    - collection: 遍历的列表或集合（foreach类型）
    - start_num: 起始数字（range类型）
    - end_num: 结束数字（range类型）
    - step: 步长（range类型）
    - count: 循环次数（count类型）
    - max_iterations: 最大循环次数限制（防止无限循环）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.LOOP,
            name="循环",
            description="循环遍历列表、范围或指定次数",
            category="逻辑控制",
            inputs=[
                NodeInput(
                    name="loop_type",
                    label="循环类型",
                    type=InputType.DROPDOWN,
                    required=True,
                    default="range",
                    options=["foreach", "range", "count"],
                    description="循环类型"
                ),
                NodeInput(
                    name="collection",
                    label="遍历集合",
                    type=InputType.VARIABLE,
                    required=False,
                    description="要遍历的列表或集合变量（foreach类型使用）"
                ),
                NodeInput(
                    name="start_num",
                    label="起始数字",
                    type=InputType.NUMBER,
                    required=False,
                    default=0,
                    description="范围循环的起始数字（range类型使用）"
                ),
                NodeInput(
                    name="end_num",
                    label="结束数字",
                    type=InputType.NUMBER,
                    required=False,
                    default=10,
                    description="范围循环的结束数字（range类型使用）"
                ),
                NodeInput(
                    name="step",
                    label="步长",
                    type=InputType.NUMBER,
                    required=False,
                    default=1,
                    description="范围循环的步长（range类型使用）"
                ),
                NodeInput(
                    name="count",
                    label="循环次数",
                    type=InputType.NUMBER,
                    required=False,
                    default=1,
                    description="循环执行次数（count类型使用）"
                ),
                NodeInput(
                    name="max_iterations",
                    label="最大循环次数",
                    type=InputType.NUMBER,
                    required=False,
                    default=1000,
                    description="防止无限循环的最大迭代次数限制"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="items",
                    label="循环项目列表",
                    description="循环遍历的所有项目"
                ),
                NodeOutput(
                    key="count",
                    label="项目总数",
                    description="循环项目的总数量"
                ),
                NodeOutput(
                    key="current_item",
                    label="当前项目",
                    description="当前循环到的项目（最后一个）"
                ),
                NodeOutput(
                    key="current_index",
                    label="当前索引",
                    description="当前循环的索引（最后一个）"
                ),
                NodeOutput(
                    key="is_done",
                    label="是否完成",
                    description="循环是否已完成"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """执行循环"""
        loop_type = self.get_input_value(inputs, "loop_type", "range")
        max_iterations = int(self.get_input_value(inputs, "max_iterations", 1000))

        items = []
        current_item = None
        current_index = 0

        if loop_type == "foreach":
            collection = self.get_required_input(inputs, "collection")

            # 解析变量
            if isinstance(collection, str):
                collection = context.resolve_variables(collection)
                # 尝试解析为列表
                try:
                    collection = eval(collection, {"__builtins__": {}}, {})
                except Exception:
                    pass

            if not hasattr(collection, '__iter__'):
                raise ValueError("foreach类型的collection必须是可迭代对象")

            items = list(collection)

        elif loop_type == "range":
            start_num = int(self.get_input_value(inputs, "start_num", 0))
            end_num = int(self.get_input_value(inputs, "end_num", 10))
            step = int(self.get_input_value(inputs, "step", 1))

            if step == 0:
                raise ValueError("步长不能为0")

            items = list(range(start_num, end_num, step))

        elif loop_type == "count":
            count = int(self.get_input_value(inputs, "count", 1))
            if count < 0:
                raise ValueError("循环次数不能为负数")
            items = list(range(count))

        else:
            raise ValueError(f"不支持的循环类型: {loop_type}")

        # 限制最大循环次数
        if len(items) > max_iterations:
            raise ValueError(f"循环项目数({len(items)})超过最大限制({max_iterations})")

        # 获取最后一个项目的信息
        if items:
            current_index = len(items) - 1
            current_item = items[current_index]

        return self.create_output(
            items=items,
            count=len(items),
            current_item=current_item,
            current_index=current_index,
            is_done=True
        )

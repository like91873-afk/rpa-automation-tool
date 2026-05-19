"""
数值运算节点

提供各种数学运算功能
"""

import math
from typing import Any, Dict

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


class MathOperationNode(BaseNode):
    """
    数值运算节点

    支持基本算术运算和常用数学函数

    参数说明:
    - operation: 运算类型（add/subtract/multiply/divide/mod/power/sqrt/abs/round/min/max）
    - operand_a: 第一个操作数
    - operand_b: 第二个操作数（部分运算不需要）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.MATH_OPERATION,
            name="数值运算",
            description="执行各种数学运算",
            category="数据处理",
            inputs=[
                NodeInput(
                    name="operation",
                    label="运算类型",
                    type=InputType.DROPDOWN,
                    required=True,
                    default="add",
                    options=[
                        "add", "subtract", "multiply", "divide", "mod", "power",
                        "sqrt", "abs", "round", "floor", "ceil", "min", "max"
                    ],
                    description="数学运算类型"
                ),
                NodeInput(
                    name="operand_a",
                    label="操作数A",
                    type=InputType.NUMBER,
                    required=True,
                    description="第一个操作数"
                ),
                NodeInput(
                    name="operand_b",
                    label="操作数B",
                    type=InputType.NUMBER,
                    required=False,
                    description="第二个操作数（sqrt/abs/round等单操作数运算不需要）"
                ),
                NodeInput(
                    name="precision",
                    label="精度（小数位数）",
                    type=InputType.NUMBER,
                    required=False,
                    default=2,
                    description="round运算时的小数位数"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="result",
                    label="运算结果",
                    description="数学运算的结果"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """执行数值运算"""
        operation = self.get_input_value(inputs, "operation", "add")
        operand_a = self.get_input_value(inputs, "operand_a", 0)
        operand_b = self.get_input_value(inputs, "operand_b", 0)
        precision = int(self.get_input_value(inputs, "precision", 2))

        # 解析变量
        if isinstance(operand_a, str):
            operand_a = context.resolve_variables(operand_a)
        if isinstance(operand_b, str):
            operand_b = context.resolve_variables(operand_b)

        # 转换为数字
        try:
            operand_a = float(operand_a)
            # 如果是整数则转换回int
            if operand_a == int(operand_a) and operation not in ["divide"]:
                operand_a = int(operand_a)
        except (ValueError, TypeError):
            raise ValueError(f"操作数A不是有效数字: {operand_a}")

        # 需要两个操作数的运算
        two_operand_ops = ["add", "subtract", "multiply", "divide", "mod", "power", "min", "max"]

        if operation in two_operand_ops:
            try:
                operand_b = float(operand_b)
                if operand_b == int(operand_b) and operation not in ["divide"]:
                    operand_b = int(operand_b)
            except (ValueError, TypeError):
                raise ValueError(f"操作数B不是有效数字: {operand_b}")

        result = None

        if operation == "add":
            result = operand_a + operand_b
        elif operation == "subtract":
            result = operand_a - operand_b
        elif operation == "multiply":
            result = operand_a * operand_b
        elif operation == "divide":
            if operand_b == 0:
                raise ValueError("除数不能为零")
            result = operand_a / operand_b
        elif operation == "mod":
            if operand_b == 0:
                raise ValueError("除数不能为零")
            result = operand_a % operand_b
        elif operation == "power":
            result = operand_a ** operand_b
        elif operation == "sqrt":
            if operand_a < 0:
                raise ValueError("不能对负数求平方根")
            result = math.sqrt(operand_a)
        elif operation == "abs":
            result = abs(operand_a)
        elif operation == "round":
            result = round(operand_a, precision)
        elif operation == "floor":
            result = math.floor(operand_a)
        elif operation == "ceil":
            result = math.ceil(operand_a)
        elif operation == "min":
            result = min(operand_a, operand_b)
        elif operation == "max":
            result = max(operand_a, operand_b)
        else:
            raise ValueError(f"不支持的运算类型: {operation}")

        # 整数结果优化
        if isinstance(result, float) and result == int(result) and not math.isinf(result):
            result = int(result)

        return self.create_output(result=result)

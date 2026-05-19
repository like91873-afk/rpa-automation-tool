"""
字符串操作节点

提供各种字符串处理功能
"""

import json
import re
from typing import Any, Dict

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


class StringOperationNode(BaseNode):
    """
    字符串操作节点

    支持字符串的拼接、分割、替换、大小写转换等操作

    参数说明:
    - operation: 操作类型
    - input_string: 输入字符串
    - param1: 第一个参数（根据不同操作含义不同）
    - param2: 第二个参数（根据不同操作含义不同）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.STRING_OPERATION,
            name="字符串操作",
            description="执行各种字符串处理操作",
            category="数据处理",
            inputs=[
                NodeInput(
                    name="operation",
                    label="操作类型",
                    type=InputType.DROPDOWN,
                    required=True,
                    default="concat",
                    options=[
                        "concat", "split", "replace", "upper", "lower", "trim",
                        "contains", "startswith", "endswith", "format",
                        "length", "substring", "reverse", "strip"
                    ],
                    description="字符串操作类型"
                ),
                NodeInput(
                    name="input_string",
                    label="输入字符串",
                    type=InputType.TEXT,
                    required=True,
                    description="要处理的字符串"
                ),
                NodeInput(
                    name="param1",
                    label="参数1",
                    type=InputType.TEXT,
                    required=False,
                    description="第一个参数（split:分隔符, replace:查找, concat:拼接字符串, format:格式化参数）"
                ),
                NodeInput(
                    name="param2",
                    label="参数2",
                    type=InputType.TEXT,
                    required=False,
                    description="第二个参数（replace:替换为, substring:结束索引）"
                ),
                NodeInput(
                    name="separator",
                    label="连接分隔符",
                    type=InputType.TEXT,
                    required=False,
                    default="",
                    description="concat操作时多个字符串的连接分隔符"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="result",
                    label="操作结果",
                    description="字符串操作的结果（可能是字符串、列表或数字）"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """执行字符串操作"""
        operation = self.get_input_value(inputs, "operation", "concat")
        input_string = self.get_required_input(inputs, "input_string")
        param1 = self.get_input_value(inputs, "param1", "")
        param2 = self.get_input_value(inputs, "param2", "")
        separator = self.get_input_value(inputs, "separator", "")

        # 解析变量
        input_string = context.resolve_variables(str(input_string))
        param1 = context.resolve_variables(str(param1))
        param2 = context.resolve_variables(str(param2))
        separator = context.resolve_variables(str(separator))

        result = None

        if operation == "concat":
            # 拼接字符串
            if param1:
                result = input_string + separator + param1
            else:
                result = input_string

        elif operation == "split":
            # 分割字符串
            delimiter = param1 if param1 else ","
            result = input_string.split(delimiter)

        elif operation == "replace":
            # 替换字符串
            if not param1:
                raise ValueError("replace操作需要指定查找字符串（param1）")
            replacement = param2 if param2 else ""
            result = input_string.replace(param1, replacement)

        elif operation == "upper":
            # 转大写
            result = input_string.upper()

        elif operation == "lower":
            # 转小写
            result = input_string.lower()

        elif operation == "trim":
            # 去除首尾空白
            result = input_string.strip()

        elif operation == "strip":
            # 去除指定字符
            chars = param1 if param1 else None
            result = input_string.strip(chars)

        elif operation == "contains":
            # 检查是否包含子串
            if not param1:
                raise ValueError("contains操作需要指定查找字符串（param1）")
            result = param1 in input_string

        elif operation == "startswith":
            # 检查是否以指定字符串开头
            if not param1:
                raise ValueError("startswith操作需要指定前缀字符串（param1）")
            result = input_string.startswith(param1)

        elif operation == "endswith":
            # 检查是否以指定字符串结尾
            if not param1:
                raise ValueError("endswith操作需要指定后缀字符串（param1）")
            result = input_string.endswith(param1)

        elif operation == "format":
            # 字符串格式化
            try:
                # 尝试解析参数为列表或字典
                if param1.startswith("["):
                    args = json.loads(param1)
                    result = input_string.format(*args)
                elif param1.startswith("{"):
                    kwargs = json.loads(param1)
                    result = input_string.format(**kwargs)
                else:
                    result = input_string.format(param1)
            except json.JSONDecodeError:
                result = input_string.format(param1)
            except (IndexError, KeyError) as e:
                raise ValueError(f"格式化参数错误: {str(e)}")

        elif operation == "length":
            # 获取字符串长度
            result = len(input_string)

        elif operation == "substring":
            # 截取子串
            start = int(param1) if param1 else 0
            end = int(param2) if param2 else None
            if end is not None:
                result = input_string[start:end]
            else:
                result = input_string[start:]

        elif operation == "reverse":
            # 反转字符串
            result = input_string[::-1]

        else:
            raise ValueError(f"不支持的字符串操作: {operation}")

        return self.create_output(result=result)

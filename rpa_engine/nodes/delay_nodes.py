"""
延迟/等待节点

支持延迟执行和等待条件满足
"""

import time
from typing import Any, Dict

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


class DelayNode(BaseNode):
    """
    延迟执行节点

    暂停流程执行指定的时间。

    参数说明:
    - seconds: 延迟秒数
    - message: 延迟提示信息（可选）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.DELAY,
            name="延迟执行",
            description="暂停流程执行指定的时间",
            category="控制流",
            inputs=[
                NodeInput(
                    name="seconds",
                    label="延迟秒数",
                    type=InputType.NUMBER,
                    required=True,
                    description="延迟的秒数，如: 5 表示延迟5秒"
                ),
                NodeInput(
                    name="message",
                    label="提示信息",
                    type=InputType.TEXT,
                    required=False,
                    default="",
                    description="延迟时的提示信息（用于日志）"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="delay_result",
                    label="延迟结果",
                    description="延迟执行结果"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        seconds = float(self.get_required_input(inputs, "seconds"))
        message = self.get_input_value(inputs, "message", "")

        if seconds < 0:
            raise ValueError(f"延迟时间不能为负数: {seconds}")

        if seconds > 3600:
            raise ValueError(f"延迟时间不能超过3600秒（1小时）: {seconds}")

        start_time = time.time()

        if message:
            print(f"[延迟] {message} - 等待 {seconds} 秒...")

        time.sleep(seconds)

        actual_duration = time.time() - start_time

        return {
            "delay_result": {
                "success": True,
                "requested_seconds": seconds,
                "actual_seconds": round(actual_duration, 3),
                "message": message or f"延迟 {seconds} 秒完成"
            }
        }


class WaitForNode(BaseNode):
    """
    等待条件节点

    等待某个条件变为True，支持轮询检查。

    参数说明:
    - condition_type: 条件类型（variable_exists/variable_true/python_expression/time）
    - variable_name: 变量名（variable_exists/variable_true时使用）
    - expression: Python表达式（python_expression时使用）
    - timeout: 超时时间（秒，默认60）
    - poll_interval: 轮询间隔（秒，默认1）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.WAIT_FOR,
            name="等待条件",
            description="等待某个条件变为True，支持超时",
            category="控制流",
            inputs=[
                NodeInput(
                    name="condition_type",
                    label="条件类型",
                    type=InputType.DROPDOWN,
                    required=True,
                    options=["variable_exists", "variable_true", "python_expression", "time"],
                    description="等待的条件类型"
                ),
                NodeInput(
                    name="variable_name",
                    label="变量名",
                    type=InputType.TEXT,
                    required=False,
                    default="",
                    description="要检查的变量名（variable_exists/variable_true时使用）"
                ),
                NodeInput(
                    name="expression",
                    label="条件表达式",
                    type=InputType.TEXT,
                    required=False,
                    default="",
                    description="Python布尔表达式（python_expression时使用），如: len(data) > 0"
                ),
                NodeInput(
                    name="timeout",
                    label="超时时间(秒)",
                    type=InputType.NUMBER,
                    required=False,
                    default=60,
                    description="最大等待时间（秒）"
                ),
                NodeInput(
                    name="poll_interval",
                    label="轮询间隔(秒)",
                    type=InputType.NUMBER,
                    required=False,
                    default=1,
                    description="检查条件的间隔时间（秒）"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="wait_result",
                    label="等待结果",
                    description="等待结果，包含是否超时等信息"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        condition_type = self.get_required_input(inputs, "condition_type")
        variable_name = self.get_input_value(inputs, "variable_name", "")
        expression = self.get_input_value(inputs, "expression", "")
        timeout = float(self.get_input_value(inputs, "timeout", 60))
        poll_interval = float(self.get_input_value(inputs, "poll_interval", 1))

        if poll_interval <= 0:
            raise ValueError(f"轮询间隔必须大于0: {poll_interval}")

        start_time = time.time()
        check_count = 0

        while True:
            elapsed = time.time() - start_time
            check_count += 1

            # 检查是否超时
            if elapsed >= timeout:
                return {
                    "wait_result": {
                        "success": False,
                        "timeout": True,
                        "elapsed_seconds": round(elapsed, 3),
                        "check_count": check_count,
                        "message": f"等待超时 ({timeout}秒)"
                    }
                }

            # 检查条件
            condition_met = False

            if condition_type == "variable_exists":
                if not variable_name:
                    raise ValueError("variable_exists类型需要指定variable_name")
                condition_met = context.has_variable(variable_name)

            elif condition_type == "variable_true":
                if not variable_name:
                    raise ValueError("variable_true类型需要指定variable_name")
                if context.has_variable(variable_name):
                    value = context.get_variable(variable_name)
                    condition_met = bool(value)

            elif condition_type == "python_expression":
                if not expression:
                    raise ValueError("python_expression类型需要指定expression")
                try:
                    # 准备执行环境
                    eval_globals = {"__builtins__": {}}
                    eval_globals.update(context.variables)
                    condition_met = bool(eval(expression, eval_globals))
                except Exception:
                    condition_met = False

            elif condition_type == "time":
                # 等待指定时间后返回
                wait_seconds = float(self.get_input_value(inputs, "timeout", 60))
                time.sleep(wait_seconds)
                return {
                    "wait_result": {
                        "success": True,
                        "elapsed_seconds": round(wait_seconds, 3),
                        "check_count": 1,
                        "message": f"等待 {wait_seconds} 秒完成"
                    }
                }

            if condition_met:
                return {
                    "wait_result": {
                        "success": True,
                        "timeout": False,
                        "elapsed_seconds": round(elapsed, 3),
                        "check_count": check_count,
                        "message": f"条件满足，耗时 {round(elapsed, 1)} 秒"
                    }
                }

            # 等待下一次检查
            time.sleep(poll_interval)

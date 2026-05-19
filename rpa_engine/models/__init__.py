"""
RPA引擎 - 数据模型
"""

from .schemas import (
    Connection,
    ExecutionResult,
    ExecutionStatus,
    Flow,
    FlowExecuteRequest,
    FlowSaveRequest,
    FlowVariable,
    InputType,
    NodeDefinition,
    NodeExecutionLog,
    NodeInput,
    NodeInstance,
    NodeOutput,
    NodeType,
)
from .context import ExecutionContext

__all__ = [
    "Connection",
    "ExecutionContext",
    "ExecutionResult",
    "ExecutionStatus",
    "Flow",
    "FlowExecuteRequest",
    "FlowSaveRequest",
    "FlowVariable",
    "InputType",
    "NodeDefinition",
    "NodeExecutionLog",
    "NodeInput",
    "NodeInstance",
    "NodeOutput",
    "NodeType",
]

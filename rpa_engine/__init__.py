"""
RPA自动化工具引擎

轻量级RPA流程设计器和执行引擎
"""

__version__ = "0.1.0"
__author__ = "RPA Team"

from .engine import ExecutionEngine, engine
from .models import (
    Connection,
    ExecutionContext,
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
from .nodes import (
    BaseNode,
    NODE_REGISTRY,
    get_node_class,
    get_all_node_definitions,
)
from .utils import (
    create_sample_flow,
    generate_connection_id,
    generate_flow_id,
    generate_node_id,
    load_flow_from_file,
    save_flow_to_file,
    validate_flow,
)

__all__ = [
    # Core
    "ExecutionEngine",
    "engine",
    # Models
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
    # Nodes
    "BaseNode",
    "NODE_REGISTRY",
    "get_node_class",
    "get_all_node_definitions",
    # Utils
    "create_sample_flow",
    "generate_connection_id",
    "generate_flow_id",
    "generate_node_id",
    "load_flow_from_file",
    "save_flow_to_file",
    "validate_flow",
]

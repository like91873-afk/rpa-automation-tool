"""
RPA引擎 - 工具函数
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..models.schemas import Flow


def load_flow_from_file(file_path: str) -> Flow:
    """从文件加载流程定义"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"流程文件不存在: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return Flow(**data)


def save_flow_to_file(flow: Flow, file_path: str) -> None:
    """保存流程定义到文件"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(flow.model_dump(), f, ensure_ascii=False, indent=2, default=str)


def create_sample_flow() -> Flow:
    """创建示例流程"""
    return Flow(
        id="sample-flow-001",
        name="示例流程",
        description="一个简单的示例流程，演示Python代码执行",
        nodes=[
            {
                "id": "node-1",
                "type": "python_exec",
                "name": "执行Python代码",
                "inputs": {
                    "python_code": "result = 1 + 2\nprint(f'计算结果: {result}')",
                    "timeout": 1800
                },
                "position": {"x": 100, "y": 100}
            },
            {
                "id": "node-2",
                "type": "file_write",
                "name": "写入结果文件",
                "inputs": {
                    "file_path": "output/result.txt",
                    "content": "执行完成",
                    "mode": "overwrite"
                },
                "position": {"x": 300, "y": 100}
            }
        ],
        connections=[
            {
                "id": "conn-1",
                "source_node_id": "node-1",
                "target_node_id": "node-2"
            }
        ],
        variables={}
    )


def generate_flow_id() -> str:
    """生成流程ID"""
    import uuid
    return f"flow-{uuid.uuid4().hex[:8]}"


def generate_node_id() -> str:
    """生成节点ID"""
    import uuid
    return f"node-{uuid.uuid4().hex[:8]}"


def generate_connection_id() -> str:
    """生成连接ID"""
    import uuid
    return f"conn-{uuid.uuid4().hex[:8]}"


def validate_flow(flow: Flow) -> list:
    """验证流程定义"""
    errors = []

    # 检查节点ID唯一性
    node_ids = [node.id for node in flow.nodes]
    if len(node_ids) != len(set(node_ids)):
        errors.append("存在重复的节点ID")

    # 检查连接的有效性
    for conn in flow.connections:
        if conn.source_node_id not in node_ids:
            errors.append(f"连接的源节点不存在: {conn.source_node_id}")
        if conn.target_node_id not in node_ids:
            errors.append(f"连接的目标节点不存在: {conn.target_node_id}")

    # 检查节点类型
    from ..nodes import NODE_REGISTRY
    for node in flow.nodes:
        node_type = node.type if isinstance(node.type, str) else node.type.value
        if node_type not in NODE_REGISTRY:
            errors.append(f"未知的节点类型: {node_type}")

    return errors

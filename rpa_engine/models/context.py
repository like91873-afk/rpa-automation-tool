"""
执行上下文 - 管理流程执行过程中的状态和变量
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .schemas import ExecutionStatus, NodeExecutionLog


class ExecutionContext:
    """流程执行上下文"""

    def __init__(self, initial_variables: Optional[Dict[str, Any]] = None):
        self.variables: Dict[str, Any] = initial_variables or {}
        self.execution_log: List[NodeExecutionLog] = []
        self.current_node_id: Optional[str] = None
        self.status: ExecutionStatus = ExecutionStatus.PENDING
        self.error: Optional[str] = None
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None
        self._node_outputs: Dict[str, Dict[str, Any]] = {}

    def set_variable(self, key: str, value: Any) -> None:
        """设置变量"""
        self.variables[key] = value

    def get_variable(self, key: str) -> Any:
        """获取变量值"""
        if key not in self.variables:
            raise KeyError(f"变量 '{key}' 不存在")
        return self.variables[key]

    def has_variable(self, key: str) -> bool:
        """检查变量是否存在"""
        return key in self.variables

    def resolve_variables(self, text: str) -> str:
        """解析文本中的变量引用 ${var_name}"""
        if not isinstance(text, str):
            return str(text)

        pattern = r'\$\{(\w+)\}'

        def replace_var(match):
            var_name = match.group(1)
            try:
                value = self.get_variable(var_name)
                return str(value)
            except KeyError:
                return match.group(0)  # 保留原始引用

        return re.sub(pattern, replace_var, text)

    def resolve_input_value(self, value: Any) -> Any:
        """解析输入值，处理变量引用"""
        if isinstance(value, str):
            # 检查是否是纯变量引用 ${var_name}
            var_match = re.match(r'^\$\{(\w+)\}$', value)
            if var_match:
                var_name = var_match.group(1)
                return self.get_variable(var_name)
            # 否则解析字符串中的变量
            return self.resolve_variables(value)
        elif isinstance(value, dict):
            return {k: self.resolve_input_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve_input_value(item) for item in value]
        return value

    def set_node_outputs(self, node_id: str, outputs: Dict[str, Any]) -> None:
        """保存节点输出"""
        self._node_outputs[node_id] = outputs

    def get_node_outputs(self, node_id: str) -> Dict[str, Any]:
        """获取节点输出"""
        return self._node_outputs.get(node_id, {})

    def add_execution_log(self, log: NodeExecutionLog) -> None:
        """添加执行日志"""
        self.execution_log.append(log)

    def start_node_execution(self, node_id: str, node_name: str, node_type: str) -> None:
        """开始节点执行"""
        self.current_node_id = node_id
        self.status = ExecutionStatus.RUNNING

    def complete_node_execution(
        self,
        node_id: str,
        node_name: str,
        node_type: str,
        outputs: Dict[str, Any],
        logs: Optional[List[str]] = None
    ) -> None:
        """完成节点执行"""
        log = NodeExecutionLog(
            node_id=node_id,
            node_name=node_name,
            node_type=node_type,
            status=ExecutionStatus.COMPLETED,
            end_time=datetime.now(),
            outputs=outputs,
            logs=logs or []
        )
        self.add_execution_log(log)
        self.set_node_outputs(node_id, outputs)

    def fail_node_execution(
        self,
        node_id: str,
        node_name: str,
        node_type: str,
        error: str,
        logs: Optional[List[str]] = None
    ) -> None:
        """节点执行失败"""
        log = NodeExecutionLog(
            node_id=node_id,
            node_name=node_name,
            node_type=node_type,
            status=ExecutionStatus.FAILED,
            end_time=datetime.now(),
            error=error,
            logs=logs or []
        )
        self.add_execution_log(log)

    def complete_execution(self, status: ExecutionStatus = ExecutionStatus.COMPLETED) -> None:
        """完成流程执行"""
        self.status = status
        self.end_time = datetime.now()

    def fail_execution(self, error: str) -> None:
        """流程执行失败"""
        self.status = ExecutionStatus.FAILED
        self.error = error
        self.end_time = datetime.now()

    def get_duration_ms(self) -> Optional[int]:
        """获取执行时长(毫秒)"""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "variables": self.variables,
            "error": self.error,
            "duration_ms": self.get_duration_ms(),
            "node_count": len(self.execution_log)
        }

"""
节点基类 - 所有RPA节点的基础类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType
from ..models.context import ExecutionContext


class BaseNode(ABC):
    """节点基类"""

    def __init__(self):
        self._definition: Optional[NodeDefinition] = None

    @property
    def definition(self) -> NodeDefinition:
        """获取节点定义"""
        if self._definition is None:
            self._definition = self._create_definition()
        return self._definition

    @abstractmethod
    def _create_definition(self) -> NodeDefinition:
        """创建节点定义"""
        pass

    @abstractmethod
    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """
        执行节点逻辑

        Args:
            inputs: 解析后的输入参数
            context: 执行上下文

        Returns:
            输出结果字典
        """
        pass

    def validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """
        验证输入参数

        Args:
            inputs: 输入参数

        Returns:
            错误消息列表，空表示验证通过
        """
        errors = []
        for param in self.definition.inputs:
            if param.required and param.name not in inputs:
                errors.append(f"缺少必填参数: {param.label} ({param.name})")
        return errors

    def get_input_value(self, inputs: Dict[str, Any], param_name: str, default: Any = None) -> Any:
        """获取输入参数值"""
        return inputs.get(param_name, default)

    def get_required_input(self, inputs: Dict[str, Any], param_name: str) -> Any:
        """获取必填输入参数，不存在则抛出异常"""
        if param_name not in inputs:
            raise ValueError(f"缺少必填参数: {param_name}")
        return inputs[param_name]

    def create_output(self, **kwargs) -> Dict[str, Any]:
        """创建输出字典"""
        return kwargs

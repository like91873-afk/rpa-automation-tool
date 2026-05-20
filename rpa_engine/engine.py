"""
RPA执行引擎

负责流程的执行调度和状态管理
"""

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models.schemas import (
    ExecutionResult,
    ExecutionStatus,
    Flow,
    NodeInstance,
    NodeType,
)
from .models.context import ExecutionContext
from .nodes import get_node_class


class ExecutionEngine:
    """流程执行引擎"""

    def __init__(self):
        self._running_executions: Dict[str, ExecutionContext] = {}

    def execute_flow(
        self,
        flow: Flow,
        initial_variables: Optional[Dict[str, Any]] = None,
        timeout: int = 3600,
        debug: bool = False
    ) -> ExecutionResult:
        """
        执行完整流程

        Args:
            flow: 流程定义
            initial_variables: 初始变量
            timeout: 超时时间（秒）
            debug: 调试模式

        Returns:
            执行结果
        """
        execution_id = str(uuid.uuid4())
        context = ExecutionContext(initial_variables)

        # 初始化全局变量
        if flow.variables:
            for key, value in flow.variables.items():
                context.set_variable(key, value)

        # 记录开始执行
        result = ExecutionResult(
            flow_id=flow.id,
            flow_name=flow.name,
            execution_id=execution_id,
            status=ExecutionStatus.RUNNING,
            start_time=datetime.now()
        )

        self._running_executions[execution_id] = context

        try:
            # 获取执行顺序
            execution_order = self._get_execution_order(flow)

            if debug:
                print(f"[DEBUG] 执行顺序: {execution_order}")

            # 按顺序执行节点
            for node_id in execution_order:
                node = self._find_node(flow, node_id)
                if not node:
                    raise ValueError(f"节点不存在: {node_id}")

                if node.disabled:
                    if debug:
                        print(f"[DEBUG] 跳过禁用节点: {node.name or node.type}")
                    continue

                # 执行节点
                self._execute_node(node, context, debug)

            # 执行完成
            context.complete_execution(ExecutionStatus.COMPLETED)

        except Exception as e:
            context.fail_execution(str(e))
            if debug:
                import traceback
                traceback.print_exc()

        finally:
            # 构建结果
            result.status = context.status
            result.end_time = context.end_time
            result.duration_ms = context.get_duration_ms()
            result.variables = context.variables
            result.node_logs = context.execution_log
            result.error = context.error

            # 清理
            self._running_executions.pop(execution_id, None)

        return result

    def _execute_node(self, node: NodeInstance, context: ExecutionContext, debug: bool = False) -> None:
        """执行单个节点"""
        # 统一使用NodeType枚举
        node_type = node.type if isinstance(node.type, NodeType) else NodeType(node.type)
        node_name = node.name or node_type.value

        if debug:
            print(f"[DEBUG] 执行节点: {node_name} ({node.id})")

        # 开始执行
        context.start_node_execution(node.id, node_name, node_type)

        # 获取节点类
        node_class = get_node_class(node_type.value)
        if not node_class:
            raise ValueError(f"未知节点类型: {node_type}")

        # 创建节点实例
        executor = node_class()

        # 解析输入参数
        resolved_inputs = {}
        for key, value in node.inputs.items():
            resolved_inputs[key] = context.resolve_input_value(value)

        # 验证输入
        errors = executor.validate_inputs(resolved_inputs)
        if errors:
            raise ValueError(f"节点 {node_name} 输入验证失败: {', '.join(errors)}")

        # 执行节点
        try:
            outputs = executor.execute(resolved_inputs, context)

            # 保存输出到上下文
            for key, value in outputs.items():
                context.set_variable(key, value)

            # 记录执行成功
            context.complete_node_execution(
                node_id=node.id,
                node_name=node_name,
                node_type=node_type,
                outputs=outputs
            )

            if debug:
                print(f"[DEBUG] 节点 {node_name} 执行成功")

        except Exception as e:
            # 记录执行失败
            context.fail_node_execution(
                node_id=node.id,
                node_name=node_name,
                node_type=node_type,
                error=str(e)
            )
            raise

    def _get_execution_order(self, flow: Flow) -> List[str]:
        """
        获取节点执行顺序（拓扑排序）

        使用Kahn算法进行拓扑排序
        """
        # 构建邻接表和入度表
        adjacency = defaultdict(list)
        in_degree = defaultdict(int)

        # 初始化所有节点
        for node in flow.nodes:
            in_degree[node.id] = 0

        # 构建图
        for conn in flow.connections:
            adjacency[conn.source_node_id].append(conn.target_node_id)
            in_degree[conn.target_node_id] += 1

        # 找到所有入度为0的节点
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # 按节点在列表中的顺序排序
            queue.sort(key=lambda x: next(
                (i for i, n in enumerate(flow.nodes) if n.id == x), len(flow.nodes)
            ))

            node_id = queue.pop(0)
            result.append(node_id)

            # 更新相邻节点的入度
            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # 检查是否有循环
        if len(result) != len(flow.nodes):
            raise ValueError("流程存在循环依赖，无法执行")

        return result

    def _find_node(self, flow: Flow, node_id: str) -> Optional[NodeInstance]:
        """查找节点"""
        for node in flow.nodes:
            if node.id == node_id:
                return node
        return None

    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行"""
        if execution_id in self._running_executions:
            context = self._running_executions[execution_id]
            context.complete_execution(ExecutionStatus.CANCELLED)
            return True
        return False

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态"""
        context = self._running_executions.get(execution_id)
        if context:
            return context.to_dict()
        return None


# 全局执行引擎实例
engine = ExecutionEngine()

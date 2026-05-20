"""
数据库操作节点

支持SQLite数据库连接、查询和执行SQL语句
"""

import sqlite3
from typing import Any, Dict, List, Optional

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


class DBConnectNode(BaseNode):
    """
    数据库连接节点

    创建SQLite数据库连接对象，供后续数据库操作节点使用。

    参数说明:
    - db_path: 数据库文件路径（SQLite）
    - db_type: 数据库类型（目前支持sqlite）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.DB_CONNECT,
            name="数据库连接",
            description="创建数据库连接对象，供后续数据库操作使用",
            category="数据库",
            inputs=[
                NodeInput(
                    name="db_path",
                    label="数据库路径",
                    type=InputType.TEXT,
                    required=True,
                    description="SQLite数据库文件路径，如: data.db 或 /path/to/data.db"
                ),
                NodeInput(
                    name="db_type",
                    label="数据库类型",
                    type=InputType.DROPDOWN,
                    required=False,
                    default="sqlite",
                    options=["sqlite"],
                    description="数据库类型（目前支持sqlite）"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="db_connection",
                    label="数据库连接",
                    description="数据库连接对象，传递给查询/执行节点使用"
                ),
                NodeOutput(
                    key="db_connect_result",
                    label="连接结果",
                    description="连接状态信息"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        db_path = self.get_required_input(inputs, "db_path")
        db_type = self.get_input_value(inputs, "db_type", "sqlite")

        if db_type != "sqlite":
            raise ValueError(f"不支持的数据库类型: {db_type}，目前仅支持sqlite")

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # 返回字典形式的结果

            return {
                "db_connection": conn,
                "db_connect_result": {
                    "success": True,
                    "db_type": db_type,
                    "db_path": db_path,
                    "message": f"成功连接到数据库: {db_path}"
                }
            }
        except Exception as e:
            return {
                "db_connection": None,
                "db_connect_result": {
                    "success": False,
                    "error": str(e)
                }
            }


class DBQueryNode(BaseNode):
    """
    数据库查询节点

    执行SELECT查询语句，返回查询结果。

    参数说明:
    - db_connection: 数据库连接对象（从db_connect节点获取）
    - sql: SQL查询语句
    - params: SQL参数（可选，用于参数化查询）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.DB_QUERY,
            name="数据库查询",
            description="执行SQL查询语句，返回查询结果列表",
            category="数据库",
            inputs=[
                NodeInput(
                    name="db_connection",
                    label="数据库连接",
                    type=InputType.VARIABLE,
                    required=True,
                    description="数据库连接对象，从db_connect节点获取"
                ),
                NodeInput(
                    name="sql",
                    label="SQL查询语句",
                    type=InputType.CODE,
                    required=True,
                    description="SELECT查询语句，如: SELECT * FROM users WHERE age > ?"
                ),
                NodeInput(
                    name="params",
                    label="查询参数",
                    type=InputType.TEXT,
                    required=False,
                    default="[]",
                    description="SQL参数列表（JSON数组格式），如: [18]"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="query_result",
                    label="查询结果",
                    description="查询结果字典，包含rows(结果列表)和row_count(行数)"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        import json

        conn = self.get_required_input(inputs, "db_connection")
        sql = self.get_required_input(inputs, "sql")
        params_str = self.get_input_value(inputs, "params", "[]")

        if conn is None:
            raise ValueError("数据库连接为空，请先执行db_connect节点")

        # 解析参数
        try:
            params = json.loads(params_str) if isinstance(params_str, str) else params_str
        except json.JSONDecodeError:
            params = []

        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)

            # 获取列名
            columns = [description[0] for description in cursor.description] if cursor.description else []

            # 获取所有行
            rows = cursor.fetchall()
            result_rows = []
            for row in rows:
                result_rows.append(dict(zip(columns, row)))

            return {
                "query_result": {
                    "success": True,
                    "columns": columns,
                    "rows": result_rows,
                    "row_count": len(result_rows)
                }
            }
        except Exception as e:
            return {
                "query_result": {
                    "success": False,
                    "error": str(e),
                    "rows": [],
                    "row_count": 0
                }
            }


class DBExecuteNode(BaseNode):
    """
    数据库执行节点

    执行INSERT/UPDATE/DELETE等非查询SQL语句。

    参数说明:
    - db_connection: 数据库连接对象
    - sql: SQL执行语句
    - params: SQL参数（可选）
    - commit: 是否自动提交（默认true）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.DB_EXECUTE,
            name="数据库执行",
            description="执行INSERT/UPDATE/DELETE等SQL语句",
            category="数据库",
            inputs=[
                NodeInput(
                    name="db_connection",
                    label="数据库连接",
                    type=InputType.VARIABLE,
                    required=True,
                    description="数据库连接对象，从db_connect节点获取"
                ),
                NodeInput(
                    name="sql",
                    label="SQL语句",
                    type=InputType.CODE,
                    required=True,
                    description="INSERT/UPDATE/DELETE语句，如: INSERT INTO users (name, age) VALUES (?, ?)"
                ),
                NodeInput(
                    name="params",
                    label="SQL参数",
                    type=InputType.TEXT,
                    required=False,
                    default="[]",
                    description="SQL参数列表（JSON数组格式），如: ['Alice', 25]"
                ),
                NodeInput(
                    name="commit",
                    label="自动提交",
                    type=InputType.BOOLEAN,
                    required=False,
                    default=True,
                    description="是否自动提交事务"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="execute_result",
                    label="执行结果",
                    description="执行结果字典，包含affected_rows(影响行数)和last_row_id(最后插入ID)"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        import json

        conn = self.get_required_input(inputs, "db_connection")
        sql = self.get_required_input(inputs, "sql")
        params_str = self.get_input_value(inputs, "params", "[]")
        commit = self.get_input_value(inputs, "commit", True)

        if conn is None:
            raise ValueError("数据库连接为空，请先执行db_connect节点")

        # 解析参数
        try:
            params = json.loads(params_str) if isinstance(params_str, str) else params_str
        except json.JSONDecodeError:
            params = []

        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)

            if commit:
                conn.commit()

            return {
                "execute_result": {
                    "success": True,
                    "affected_rows": cursor.rowcount,
                    "last_row_id": cursor.lastrowid,
                    "message": f"SQL执行成功，影响 {cursor.rowcount} 行"
                }
            }
        except Exception as e:
            if commit:
                conn.rollback()
            return {
                "execute_result": {
                    "success": False,
                    "error": str(e),
                    "affected_rows": 0
                }
            }

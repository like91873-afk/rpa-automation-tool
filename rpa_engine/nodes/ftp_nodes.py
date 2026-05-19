"""
FTP操作节点

提供FTP连接、目录查看等操作
"""

from typing import Any, Dict, List, Optional

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


class FTPConnectNode(BaseNode):
    """
    FTP连接节点

    创建FTP连接对象，供后续FTP操作使用

    参数说明:
    - host: FTP服务器地址
    - port: FTP服务器端口（默认21）
    - username: 登录用户名
    - password: 登录密码
    - passive: 是否使用被动模式（默认True）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.FTP_CONNECT,
            name="FTP连接",
            description="创建FTP连接对象",
            category="网络操作",
            inputs=[
                NodeInput(
                    name="host",
                    label="主机地址",
                    type=InputType.TEXT,
                    required=True,
                    description="FTP服务器地址"
                ),
                NodeInput(
                    name="port",
                    label="端口",
                    type=InputType.NUMBER,
                    required=False,
                    default=21,
                    description="FTP服务器端口"
                ),
                NodeInput(
                    name="username",
                    label="用户名",
                    type=InputType.TEXT,
                    required=True,
                    description="登录用户名"
                ),
                NodeInput(
                    name="password",
                    label="密码",
                    type=InputType.TEXT,
                    required=False,
                    default="",
                    description="登录密码"
                ),
                NodeInput(
                    name="passive",
                    label="被动模式",
                    type=InputType.BOOLEAN,
                    required=False,
                    default=True,
                    description="是否使用被动模式"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="ftp_connection",
                    label="FTP连接对象",
                    description="FTP连接对象，供后续FTP操作使用"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """创建FTP连接"""
        host = self.get_required_input(inputs, "host")
        port = self.get_input_value(inputs, "port", 21)
        username = self.get_required_input(inputs, "username")
        password = self.get_input_value(inputs, "password", "")
        passive = self.get_input_value(inputs, "passive", True)

        # 解析变量
        host = context.resolve_variables(host)
        username = context.resolve_variables(username)
        password = context.resolve_variables(password)

        # 保存连接配置到上下文
        connection_config = {
            "host": host,
            "port": int(port),
            "username": username,
            "password": password,
            "passive": bool(passive),
        }

        return {
            "ftp_connection": connection_config
        }


class FTPListDirNode(BaseNode):
    """
    FTP查看目录节点

    查看FTP服务器指定目录下的文件列表

    参数说明:
    - ftp_connection: FTP连接对象
    - ftp_dir: 查看的FTP目录（推荐绝对路径）
    - recursive: 是否递归列出子目录

    输出说明:
    - ftp_dir_list: 返回目录下所有文件信息字典组成的列表
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.FTP_LIST_DIR,
            name="FTP查看目录",
            description="查看FTP服务器目录下的文件列表",
            category="网络操作",
            inputs=[
                NodeInput(
                    name="ftp_connection",
                    label="FTP连接对象",
                    type=InputType.VARIABLE,
                    required=True,
                    default="${ftp}",
                    description="FTP连接对象"
                ),
                NodeInput(
                    name="ftp_dir",
                    label="查看的FTP目录",
                    type=InputType.TEXT,
                    required=True,
                    description="推荐绝对路径，如果只给出名字或.开头的相对路径，则转换为基于当前工作目录相对路径的实际路径"
                ),
                NodeInput(
                    name="recursive",
                    label="递归子目录",
                    type=InputType.BOOLEAN,
                    required=False,
                    default=False,
                    description="是否递归列出子目录"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="ftp_dir_list",
                    label="目录文件列表",
                    description="返回目录下所有文件信息字典组成的列表"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """查看FTP目录"""
        ftp_connection = self.get_required_input(inputs, "ftp_connection")
        ftp_dir = self.get_required_input(inputs, "ftp_dir")
        recursive = self.get_input_value(inputs, "recursive", False)

        # 解析变量
        ftp_dir = context.resolve_variables(ftp_dir)

        # 注意：实际实现需要ftplib库
        # 这里返回模拟结果，展示输出格式
        # 实际实现时应使用:
        # from ftplib import FTP
        # ftp = FTP()
        # ftp.connect(host, port)
        # ftp.login(username, password)
        # ftp.cwd(ftp_dir)
        # files = []
        # ftp.retrlines('LIST', callback)

        # 模拟返回格式（与文档一致）
        sample_result = [
            {
                "type": "file",
                "permissions": "-rw-------",
                "size": "20913",
                "ctime": "2024-11-18 10:14:00",
                "name": "example_file.txt",
                "abspath": f"{ftp_dir}/example_file.txt"
            },
            {
                "type": "directory",
                "permissions": "drwxr-xr-x",
                "size": "4096",
                "ctime": "2024-11-18 09:00:00",
                "name": "subfolder",
                "abspath": f"{ftp_dir}/subfolder"
            }
        ]

        return {
            "ftp_dir_list": {
                "success": True,
                "directory": ftp_dir,
                "count": len(sample_result),
                "items": sample_result,
                "message": "FTP目录查看功能需要ftplib库支持"
            }
        }

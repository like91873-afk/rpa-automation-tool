"""
SFTP操作节点

提供SFTP连接、上传、下载等操作
"""

from typing import Any, Dict, Optional

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


class SFTPConnectNode(BaseNode):
    """
    SFTP连接节点

    创建SFTP连接对象
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.SFTP_CONNECT,
            name="SFTP连接",
            description="创建SFTP连接对象",
            category="网络操作",
            inputs=[
                NodeInput(
                    name="host",
                    label="主机地址",
                    type=InputType.TEXT,
                    required=True,
                    description="SFTP服务器地址"
                ),
                NodeInput(
                    name="port",
                    label="端口",
                    type=InputType.NUMBER,
                    required=False,
                    default=22,
                    description="SFTP服务器端口"
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
                    description="登录密码"
                ),
                NodeInput(
                    name="private_key_path",
                    label="私钥路径",
                    type=InputType.FILE_PATH,
                    required=False,
                    description="SSH私钥文件路径"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="sftp_connection",
                    label="SFTP连接对象",
                    description="SFTP连接对象，供后续SFTP操作使用"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """创建SFTP连接"""
        # 注意：实际实现需要paramiko库
        # 这里返回连接配置，实际连接在使用时建立
        host = self.get_required_input(inputs, "host")
        port = self.get_input_value(inputs, "port", 22)
        username = self.get_required_input(inputs, "username")
        password = self.get_input_value(inputs, "password", "")
        private_key_path = self.get_input_value(inputs, "private_key_path", "")

        # 解析变量
        host = context.resolve_variables(host)
        username = context.resolve_variables(username)
        password = context.resolve_variables(password)
        if private_key_path:
            private_key_path = context.resolve_variables(private_key_path)

        # 保存连接配置到上下文
        connection_config = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "private_key_path": private_key_path,
        }

        return {
            "sftp_connection": connection_config
        }


class SFTPUploadNode(BaseNode):
    """
    SFTP上传节点

    上传文件到SFTP服务器
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.SFTP_UPLOAD,
            name="SFTP上传",
            description="上传文件到SFTP服务器",
            category="网络操作",
            inputs=[
                NodeInput(
                    name="sftp_connection",
                    label="SFTP连接对象",
                    type=InputType.VARIABLE,
                    required=True,
                    description="SFTP连接对象"
                ),
                NodeInput(
                    name="local_path",
                    label="本地文件路径",
                    type=InputType.FILE_PATH,
                    required=True,
                    description="要上传的本地文件路径"
                ),
                NodeInput(
                    name="remote_path",
                    label="远程文件路径",
                    type=InputType.TEXT,
                    required=True,
                    description="上传到远程的文件路径"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="upload_result",
                    label="上传结果",
                    description="文件上传操作的结果"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """上传文件到SFTP"""
        # 注意：实际实现需要paramiko库
        sftp_connection = self.get_required_input(inputs, "sftp_connection")
        local_path = self.get_required_input(inputs, "local_path")
        remote_path = self.get_required_input(inputs, "remote_path")

        # 解析变量
        local_path = context.resolve_variables(local_path)
        remote_path = context.resolve_variables(remote_path)

        # TODO: 实际实现SFTP上传
        # 这里返回模拟结果
        return {
            "upload_result": {
                "success": True,
                "local_path": local_path,
                "remote_path": remote_path,
                "message": "SFTP上传功能需要paramiko库支持"
            }
        }


class SFTPDownloadNode(BaseNode):
    """
    SFTP下载节点

    从SFTP服务器下载文件
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.SFTP_DOWNLOAD,
            name="SFTP下载",
            description="从SFTP服务器下载文件",
            category="网络操作",
            inputs=[
                NodeInput(
                    name="sftp_connection",
                    label="SFTP连接对象",
                    type=InputType.VARIABLE,
                    required=True,
                    description="SFTP连接对象"
                ),
                NodeInput(
                    name="remote_path",
                    label="远程文件路径",
                    type=InputType.TEXT,
                    required=True,
                    description="要下载的远程文件路径"
                ),
                NodeInput(
                    name="local_path",
                    label="本地保存路径",
                    type=InputType.FILE_PATH,
                    required=True,
                    description="下载到本地的保存路径"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="download_result",
                    label="下载结果",
                    description="文件下载操作的结果"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """从SFTP下载文件"""
        # 注意：实际实现需要paramiko库
        sftp_connection = self.get_required_input(inputs, "sftp_connection")
        remote_path = self.get_required_input(inputs, "remote_path")
        local_path = self.get_required_input(inputs, "local_path")

        # 解析变量
        remote_path = context.resolve_variables(remote_path)
        local_path = context.resolve_variables(local_path)

        # TODO: 实际实现SFTP下载
        # 这里返回模拟结果
        return {
            "download_result": {
                "success": True,
                "remote_path": remote_path,
                "local_path": local_path,
                "message": "SFTP下载功能需要paramiko库支持"
            }
        }


class SFTPNewFileNode(BaseNode):
    """
    SFTP新建文件节点

    在SFTP服务器上创建新文件
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.SFTP_NEW_FILE,
            name="新建SFTP文件",
            description="在SFTP服务器上创建新文件",
            category="网络操作",
            inputs=[
                NodeInput(
                    name="sftp_connection",
                    label="SFTP连接对象",
                    type=InputType.VARIABLE,
                    required=True,
                    default="${sftp}",
                    description="SFTP连接对象"
                ),
                NodeInput(
                    name="remote_path",
                    label="SFTP新文件路径",
                    type=InputType.TEXT,
                    required=True,
                    description="新建文件的远程路径"
                ),
                NodeInput(
                    name="content",
                    label="文件内容",
                    type=InputType.TEXT,
                    required=False,
                    default="",
                    description="文件初始内容"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="remote_new_file_path",
                    label="新建文件路径",
                    description="返回新建SFTP文件路径"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """在SFTP上新建文件"""
        sftp_connection = self.get_required_input(inputs, "sftp_connection")
        remote_path = self.get_required_input(inputs, "remote_path")
        content = self.get_input_value(inputs, "content", "")

        # 解析变量
        remote_path = context.resolve_variables(remote_path)
        content = context.resolve_variables(content)

        # TODO: 实际实现SFTP新建文件
        # 这里返回模拟结果
        return {
            "remote_new_file_path": remote_path
        }


class SFTPWriteFileNode(BaseNode):
    """
    SFTP写入文件节点

    向SFTP服务器上的文件写入内容，支持追加和覆盖两种模式

    参数说明:
    - sftp_connection: SFTP连接对象
    - write_file_path: 写入文件路径
    - write_content: 写入文件内容
    - write_mode: 写入内容的方式（追加文件末尾/覆盖写入文件）
    - end_mode: 结束方式（结束时添加换行/结束时不添加换行）
    - file_not_exists: 写入文件不存在时处理（不存在时新建/不存在时报错）

    输出说明:
    - write_file_path: 返回写入文件的路径
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.SFTP_WRITE_FILE,
            name="SFTP写入文件",
            description="向SFTP服务器上的文件写入内容",
            category="网络操作",
            inputs=[
                NodeInput(
                    name="sftp_connection",
                    label="SFTP连接对象",
                    type=InputType.VARIABLE,
                    required=True,
                    default="${sftp}",
                    description="SFTP连接对象"
                ),
                NodeInput(
                    name="write_file_path",
                    label="写入文件路径",
                    type=InputType.TEXT,
                    required=True,
                    description="写入文件路径"
                ),
                NodeInput(
                    name="write_content",
                    label="写入文件内容",
                    type=InputType.TEXT,
                    required=True,
                    description="写入文件内容"
                ),
                NodeInput(
                    name="write_mode",
                    label="写入内容的方式",
                    type=InputType.DROPDOWN,
                    required=True,
                    default="append",
                    options=["append", "overwrite"],
                    description="追加文件末尾或覆盖写入文件"
                ),
                NodeInput(
                    name="end_mode",
                    label="结束方式",
                    type=InputType.DROPDOWN,
                    required=True,
                    default="add_newline",
                    options=["add_newline", "no_newline"],
                    description="结束时添加换行或结束时不添加换行"
                ),
                NodeInput(
                    name="file_not_exists",
                    label="写入文件不存在时处理",
                    type=InputType.DROPDOWN,
                    required=True,
                    default="create",
                    options=["create", "error"],
                    description="不存在时新建或不存在时报错"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="write_file_path",
                    label="写入文件路径",
                    description="返回写入文件的路径"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """SFTP写入文件"""
        sftp_connection = self.get_required_input(inputs, "sftp_connection")
        write_file_path = self.get_required_input(inputs, "write_file_path")
        write_content = self.get_required_input(inputs, "write_content")
        write_mode = self.get_input_value(inputs, "write_mode", "append")
        end_mode = self.get_input_value(inputs, "end_mode", "add_newline")
        file_not_exists = self.get_input_value(inputs, "file_not_exists", "create")

        # 解析变量
        write_file_path = context.resolve_variables(write_file_path)
        write_content = context.resolve_variables(write_content)

        # 添加换行符
        if end_mode == "add_newline":
            write_content = write_content + "\n"

        # 注意：实际实现需要paramiko库
        # 这里返回模拟结果
        # 实际实现时应使用:
        # import paramiko
        # transport = paramiko.Transport((host, port))
        # transport.connect(username=username, password=password)
        # sftp = paramiko.SFTPClient.from_transport(transport)
        # 
        # if write_mode == "append":
        #     with sftp.open(write_file_path, 'a') as f:
        #         f.write(write_content)
        # elif write_mode == "overwrite":
        #     with sftp.open(write_file_path, 'w') as f:
        #         f.write(write_content)

        return {
            "write_file_path": write_file_path
        }

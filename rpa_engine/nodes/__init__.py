"""
RPA引擎 - 节点模块

提供各种自动化操作节点
"""

from .base import BaseNode
from .python_nodes import PythonExecNode, PythonScriptNode
from .file_nodes import FileOpenNode, FileReadNode, FileWriteNode, DirectoryListNode, PathExistsNode
from .system_nodes import SystemCmdNode, PowerShellNode, GetComputerInfoNode
from .sftp_nodes import SFTPConnectNode, SFTPUploadNode, SFTPDownloadNode, SFTPNewFileNode, SFTPWriteFileNode
from .ftp_nodes import FTPConnectNode, FTPListDirNode
from .logic_nodes import ConditionNode, LoopNode
from .math_nodes import MathOperationNode
from .string_nodes import StringOperationNode
from .xml_nodes import XMLSaveNode

# 节点注册表
NODE_REGISTRY = {
    # Python执行
    "python_exec": PythonExecNode,
    "python_script": PythonScriptNode,
    # 文件操作
    "file_open": FileOpenNode,
    "file_read": FileReadNode,
    "file_write": FileWriteNode,
    "directory_list": DirectoryListNode,
    "path_exists": PathExistsNode,
    # 系统操作
    "system_cmd": SystemCmdNode,
    "powershell": PowerShellNode,
    "computer_info": GetComputerInfoNode,
    # 逻辑控制
    "condition": ConditionNode,
    "loop": LoopNode,
    # SFTP操作
    "sftp_connect": SFTPConnectNode,
    "sftp_upload": SFTPUploadNode,
    "sftp_download": SFTPDownloadNode,
    "sftp_new_file": SFTPNewFileNode,
    "sftp_write_file": SFTPWriteFileNode,
    # FTP操作
    "ftp_connect": FTPConnectNode,
    "ftp_list_dir": FTPListDirNode,
    # 数据处理
    "xml_save": XMLSaveNode,
    "math_operation": MathOperationNode,
    "string_operation": StringOperationNode,
}


def get_node_class(node_type: str):
    """获取节点类"""
    return NODE_REGISTRY.get(node_type)


def get_all_node_definitions():
    """获取所有节点定义"""
    definitions = []
    for node_class in NODE_REGISTRY.values():
        node = node_class()
        definitions.append(node.definition)
    return definitions


__all__ = [
    "BaseNode",
    # Python
    "PythonExecNode",
    "PythonScriptNode",
    # 文件操作
    "FileOpenNode",
    "FileReadNode",
    "FileWriteNode",
    "DirectoryListNode",
    "PathExistsNode",
    # 系统操作
    "SystemCmdNode",
    "PowerShellNode",
    "GetComputerInfoNode",
    # 逻辑控制
    "ConditionNode",
    "LoopNode",
    # SFTP
    "SFTPConnectNode",
    "SFTPUploadNode",
    "SFTPDownloadNode",
    "SFTPNewFileNode",
    "SFTPWriteFileNode",
    # FTP
    "FTPConnectNode",
    "FTPListDirNode",
    # 数据处理
    "XMLSaveNode",
    "MathOperationNode",
    "StringOperationNode",
    # 工具函数
    "NODE_REGISTRY",
    "get_node_class",
    "get_all_node_definitions",
]

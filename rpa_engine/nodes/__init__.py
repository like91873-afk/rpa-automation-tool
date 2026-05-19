"""
RPA引擎 - 节点模块

提供各种自动化操作节点
"""

from .base import BaseNode
from .python_nodes import PythonExecNode, PythonScriptNode
from .file_nodes import FileOpenNode, FileReadNode, FileWriteNode, DirectoryListNode
from .system_nodes import SystemCmdNode, PowerShellNode, GetComputerInfoNode
from .sftp_nodes import SFTPConnectNode, SFTPUploadNode, SFTPDownloadNode, SFTPNewFileNode

# 节点注册表
NODE_REGISTRY = {
    "python_exec": PythonExecNode,
    "python_script": PythonScriptNode,
    "file_open": FileOpenNode,
    "file_read": FileReadNode,
    "file_write": FileWriteNode,
    "directory_list": DirectoryListNode,
    "system_cmd": SystemCmdNode,
    "powershell": PowerShellNode,
    "computer_info": GetComputerInfoNode,
    "sftp_connect": SFTPConnectNode,
    "sftp_upload": SFTPUploadNode,
    "sftp_download": SFTPDownloadNode,
    "sftp_new_file": SFTPNewFileNode,
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
    "PythonExecNode",
    "PythonScriptNode",
    "FileOpenNode",
    "FileReadNode",
    "FileWriteNode",
    "DirectoryListNode",
    "SystemCmdNode",
    "PowerShellNode",
    "GetComputerInfoNode",
    "SFTPConnectNode",
    "SFTPUploadNode",
    "SFTPDownloadNode",
    "SFTPNewFileNode",
    "NODE_REGISTRY",
    "get_node_class",
    "get_all_node_definitions",
]

"""
文件操作节点

提供文件读写、打开等操作
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


class FileOpenNode(BaseNode):
    """
    打开文件节点

    使用应用程序打开文件，支持默认程序或指定应用程序
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.FILE_OPEN,
            name="打开文件",
            description="使用应用程序打开文件",
            category="文件操作",
            inputs=[
                NodeInput(
                    name="file_path",
                    label="文件路径",
                    type=InputType.FILE_PATH,
                    required=True,
                    description="要打开的文件路径"
                ),
                NodeInput(
                    name="open_mode",
                    label="打开方式",
                    type=InputType.DROPDOWN,
                    required=True,
                    default="default",
                    options=["default", "application"],
                    description="使用默认程序或指定应用程序打开"
                ),
                NodeInput(
                    name="app_path",
                    label="应用程序路径",
                    type=InputType.FILE_PATH,
                    required=False,
                    description="应用程序路径（选择应用程序方式时必填）"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="file_open_result",
                    label="文件打开结果",
                    description="文件打开操作的结果"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """打开文件"""
        file_path = self.get_required_input(inputs, "file_path")
        open_mode = self.get_input_value(inputs, "open_mode", "default")
        app_path = self.get_input_value(inputs, "app_path", "")

        # 解析变量
        file_path = context.resolve_variables(file_path)
        app_path = context.resolve_variables(app_path)

        # 验证文件存在
        if not os.path.exists(file_path):
            return {
                "file_open_result": {
                    "success": False,
                    "error": f"文件不存在: {file_path}"
                }
            }

        try:
            system = platform.system()

            if open_mode == "default":
                # 使用系统默认程序
                if system == "Windows":
                    os.startfile(file_path)
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", file_path], check=True)
                else:  # Linux
                    subprocess.run(["xdg-open", file_path], check=True)
            else:
                # 使用指定应用程序
                if not app_path:
                    return {
                        "file_open_result": {
                            "success": False,
                            "error": "选择应用程序方式时，必须指定应用程序路径"
                        }
                    }
                subprocess.run([app_path, file_path], check=True)

            return {
                "file_open_result": {
                    "success": True,
                    "file_path": file_path,
                    "open_mode": open_mode
                }
            }

        except subprocess.CalledProcessError as e:
            return {
                "file_open_result": {
                    "success": False,
                    "error": f"打开文件失败: {str(e)}"
                }
            }
        except Exception as e:
            return {
                "file_open_result": {
                    "success": False,
                    "error": str(e)
                }
            }


class FileReadNode(BaseNode):
    """
    读取文件节点

    读取文件内容，支持文本和二进制文件
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.FILE_READ,
            name="读取文件",
            description="读取文件内容",
            category="文件操作",
            inputs=[
                NodeInput(
                    name="file_path",
                    label="文件路径",
                    type=InputType.FILE_PATH,
                    required=True,
                    description="要读取的文件路径"
                ),
                NodeInput(
                    name="encoding",
                    label="文件编码",
                    type=InputType.TEXT,
                    required=False,
                    default="utf-8",
                    description="文件编码格式"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="file_content",
                    label="文件内容",
                    description="读取到的文件内容"
                ),
                NodeOutput(
                    key="file_info",
                    label="文件信息",
                    description="文件的元信息"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """读取文件"""
        file_path = self.get_required_input(inputs, "file_path")
        encoding = self.get_input_value(inputs, "encoding", "utf-8")

        # 解析变量
        file_path = context.resolve_variables(file_path)

        # 验证文件存在
        if not os.path.exists(file_path):
            return {
                "file_content": None,
                "file_info": {
                    "success": False,
                    "error": f"文件不存在: {file_path}"
                }
            }

        try:
            # 获取文件信息
            stat = os.stat(file_path)
            file_info = {
                "success": True,
                "path": file_path,
                "exists": True,
                "type": "file" if os.path.isfile(file_path) else "directory",
                "dir": os.path.dirname(file_path),
                "name": os.path.basename(file_path),
                "size": stat.st_size,
                "create_time": stat.st_ctime,
                "modify_time": stat.st_mtime,
            }

            # 读取文件内容
            if os.path.isfile(file_path):
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                return {
                    "file_content": content,
                    "file_info": file_info
                }
            else:
                return {
                    "file_content": None,
                    "file_info": file_info
                }

        except UnicodeDecodeError:
            return {
                "file_content": None,
                "file_info": {
                    "success": False,
                    "error": f"无法使用编码 {encoding} 读取文件"
                }
            }
        except Exception as e:
            return {
                "file_content": None,
                "file_info": {
                    "success": False,
                    "error": str(e)
                }
            }


class FileWriteNode(BaseNode):
    """
    写入文件节点

    将内容写入文件
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.FILE_WRITE,
            name="写入文件",
            description="将内容写入文件",
            category="文件操作",
            inputs=[
                NodeInput(
                    name="file_path",
                    label="文件路径",
                    type=InputType.FILE_PATH,
                    required=True,
                    description="要写入的文件路径"
                ),
                NodeInput(
                    name="content",
                    label="写入内容",
                    type=InputType.TEXT,
                    required=True,
                    description="要写入的内容"
                ),
                NodeInput(
                    name="mode",
                    label="写入模式",
                    type=InputType.DROPDOWN,
                    required=True,
                    default="overwrite",
                    options=["overwrite", "append"],
                    description="覆盖或追加模式"
                ),
                NodeInput(
                    name="encoding",
                    label="文件编码",
                    type=InputType.TEXT,
                    required=False,
                    default="utf-8",
                    description="文件编码格式"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="file_write_result",
                    label="写入结果",
                    description="文件写入操作的结果"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """写入文件"""
        file_path = self.get_required_input(inputs, "file_path")
        content = self.get_required_input(inputs, "content")
        mode = self.get_input_value(inputs, "mode", "overwrite")
        encoding = self.get_input_value(inputs, "encoding", "utf-8")

        # 解析变量
        file_path = context.resolve_variables(file_path)
        content = context.resolve_variables(content)

        try:
            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 写入文件
            write_mode = "w" if mode == "overwrite" else "a"
            with open(file_path, write_mode, encoding=encoding) as f:
                f.write(content)

            return {
                "file_write_result": {
                    "success": True,
                    "file_path": file_path,
                    "mode": mode,
                    "bytes_written": len(content.encode(encoding))
                }
            }

        except Exception as e:
            return {
                "file_write_result": {
                    "success": False,
                    "error": str(e)
                }
            }


class DirectoryListNode(BaseNode):
    """
    列出目录内容节点

    列出指定目录下的文件和子目录
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.DIRECTORY_LIST,
            name="列出目录",
            description="列出目录下的文件和子目录",
            category="文件操作",
            inputs=[
                NodeInput(
                    name="dir_path",
                    label="目录路径",
                    type=InputType.FILE_PATH,
                    required=True,
                    description="要列出的目录路径"
                ),
                NodeInput(
                    name="pattern",
                    label="文件匹配模式",
                    type=InputType.TEXT,
                    required=False,
                    default="*",
                    description="文件匹配模式，如 *.txt"
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
                    key="dir_list",
                    label="目录内容",
                    description="目录下的文件和子目录列表"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """列出目录内容"""
        dir_path = self.get_required_input(inputs, "dir_path")
        pattern = self.get_input_value(inputs, "pattern", "*")
        recursive = self.get_input_value(inputs, "recursive", False)

        # 解析变量
        dir_path = context.resolve_variables(dir_path)

        # 验证目录存在
        if not os.path.exists(dir_path):
            return {
                "dir_list": {
                    "success": False,
                    "error": f"目录不存在: {dir_path}"
                }
            }

        if not os.path.isdir(dir_path):
            return {
                "dir_list": {
                    "success": False,
                    "error": f"路径不是目录: {dir_path}"
                }
            }

        try:
            path = Path(dir_path)

            if recursive:
                items = list(path.rglob(pattern))
            else:
                items = list(path.glob(pattern))

            # 构建结果
            result_items = []
            for item in items:
                stat = item.stat()
                result_items.append({
                    "path": str(item),
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else 0,
                    "modify_time": stat.st_mtime,
                })

            return {
                "dir_list": {
                    "success": True,
                    "dir_path": dir_path,
                    "count": len(result_items),
                    "items": result_items
                }
            }

        except Exception as e:
            return {
                "dir_list": {
                    "success": False,
                    "error": str(e)
                }
            }


class PathExistsNode(BaseNode):
    """
    路径存在检查节点

    检查指定路径是否存在，返回路径的详细信息

    参数说明:
    - path: 要检查的路径

    输出说明:
    - path_info: 路径信息字典
        - path: 原始路径
        - exists: 是否存在
        - type: 类型（file/directory）
        - dir: 所在目录
        - name: 文件/目录名
        - size: 大小
        - create_time: 创建时间
        - modify_time: 修改时间
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.PATH_EXISTS,
            name="路径存在检查",
            description="检查路径是否存在并返回详细信息",
            category="文件操作",
            inputs=[
                NodeInput(
                    name="path",
                    label="检查路径",
                    type=InputType.FILE_PATH,
                    required=True,
                    description="要检查的文件或目录路径"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="path_info",
                    label="路径信息",
                    description="路径的详细信息字典"
                ),
                NodeOutput(
                    key="exists",
                    label="是否存在",
                    description="路径是否存在（True/False）"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """检查路径是否存在"""
        path = self.get_required_input(inputs, "path")

        # 解析变量
        path = context.resolve_variables(path)

        # 路径不存在时的返回格式（与文档一致）
        if not os.path.exists(path):
            return {
                "path_info": {
                    "path": path,
                    "esxit": False  # 保持与文档一致的拼写
                },
                "exists": False
            }

        try:
            stat = os.stat(path)
            path_info = {
                "path": path,
                "esxit": True,  # 保持与文档一致的拼写
                "type": "file" if os.path.isfile(path) else "directory",
                "dir": os.path.dirname(path),
                "name": os.path.basename(path),
                "size": stat.st_size,
                "create_time": stat.st_ctime,
                "modify_time": stat.st_mtime,
            }

            return {
                "path_info": path_info,
                "exists": True
            }

        except Exception as e:
            return {
                "path_info": {
                    "path": path,
                    "esxit": False,
                    "error": str(e)
                },
                "exists": False
            }

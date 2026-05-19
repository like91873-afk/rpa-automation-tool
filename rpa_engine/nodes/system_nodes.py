"""
系统命令执行节点

支持Windows CMD、PowerShell、Unix Bash等命令行
"""

import os
import platform
import subprocess
from typing import Any, Dict

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


class SystemCmdNode(BaseNode):
    """
    命令行执行节点

    使用命令行执行命令，支持Windows CMD、PowerShell、Unix Bash等
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.SYSTEM_CMD,
            name="执行命令行",
            description="使用命令行执行命令，支持Windows CMD、PowerShell、Unix Bash",
            category="系统操作",
            inputs=[
                NodeInput(
                    name="command",
                    label="命令",
                    type=InputType.CODE,
                    required=True,
                    description="要执行的命令"
                ),
                NodeInput(
                    name="shell_type",
                    label="命令行类型",
                    type=InputType.DROPDOWN,
                    required=True,
                    default="auto",
                    options=["auto", "cmd", "powershell", "bash", "sh"],
                    description="命令行程序类型"
                ),
                NodeInput(
                    name="working_dir",
                    label="工作目录",
                    type=InputType.FILE_PATH,
                    required=False,
                    description="命令执行的工作目录"
                ),
                NodeInput(
                    name="timeout",
                    label="超时时间(秒)",
                    type=InputType.NUMBER,
                    required=False,
                    default=300,
                    description="命令执行超时时间"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="cmd_result",
                    label="命令执行结果",
                    description="命令行执行结果"
                ),
            ]
        )

    def _get_shell_command(self, shell_type: str, command: str):
        """获取shell命令"""
        system = platform.system()

        if shell_type == "auto":
            if system == "Windows":
                shell_type = "cmd"
            else:
                shell_type = "bash"

        if shell_type == "cmd":
            return ["cmd", "/c", command]
        elif shell_type == "powershell":
            return ["powershell", "-Command", command]
        elif shell_type == "bash":
            return ["bash", "-c", command]
        elif shell_type == "sh":
            return ["sh", "-c", command]
        else:
            raise ValueError(f"不支持的命令行类型: {shell_type}")

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """执行系统命令"""
        command = self.get_required_input(inputs, "command")
        shell_type = self.get_input_value(inputs, "shell_type", "auto")
        working_dir = self.get_input_value(inputs, "working_dir", None)
        timeout = self.get_input_value(inputs, "timeout", 300)

        # 解析变量
        command = context.resolve_variables(command)
        if working_dir:
            working_dir = context.resolve_variables(working_dir)

        try:
            # 获取shell命令
            cmd = self._get_shell_command(shell_type, command)

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir
            )

            return {
                "cmd_result": {
                    "success": result.returncode == 0,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": command
                }
            }

        except subprocess.TimeoutExpired:
            return {
                "cmd_result": {
                    "success": False,
                    "error": f"命令执行超时（{timeout}秒）",
                    "command": command
                }
            }
        except Exception as e:
            return {
                "cmd_result": {
                    "success": False,
                    "error": str(e),
                    "command": command
                }
            }


class PowerShellNode(BaseNode):
    """
    PowerShell执行节点

    专门用于执行PowerShell命令
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.POWERSHELL,
            name="执行PowerShell",
            description="执行PowerShell命令",
            category="系统操作",
            inputs=[
                NodeInput(
                    name="command",
                    label="PowerShell命令",
                    type=InputType.CODE,
                    required=True,
                    description="要执行的PowerShell命令"
                ),
                NodeInput(
                    name="working_dir",
                    label="工作目录",
                    type=InputType.FILE_PATH,
                    required=False,
                    description="命令执行的工作目录"
                ),
                NodeInput(
                    name="timeout",
                    label="超时时间(秒)",
                    type=InputType.NUMBER,
                    required=False,
                    default=300,
                    description="命令执行超时时间"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="powershell_result",
                    label="执行结果",
                    description="PowerShell命令执行结果"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """执行PowerShell命令"""
        command = self.get_required_input(inputs, "command")
        working_dir = self.get_input_value(inputs, "working_dir", None)
        timeout = self.get_input_value(inputs, "timeout", 300)

        # 解析变量
        command = context.resolve_variables(command)
        if working_dir:
            working_dir = context.resolve_variables(working_dir)

        try:
            # 执行PowerShell命令
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir
            )

            return {
                "powershell_result": {
                    "success": result.returncode == 0,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": command
                }
            }

        except subprocess.TimeoutExpired:
            return {
                "powershell_result": {
                    "success": False,
                    "error": f"命令执行超时（{timeout}秒）",
                    "command": command
                }
            }
        except FileNotFoundError:
            return {
                "powershell_result": {
                    "success": False,
                    "error": "PowerShell不可用",
                    "command": command
                }
            }
        except Exception as e:
            return {
                "powershell_result": {
                    "success": False,
                    "error": str(e),
                    "command": command
                }
            }


class GetComputerInfoNode(BaseNode):
    """
    获取电脑信息节点

    获取系统环境变量、系统文件夹路径等信息
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.COMPUTER_INFO,
            name="获取电脑信息",
            description="获取系统环境变量、文件夹路径等信息",
            category="系统操作",
            inputs=[
                NodeInput(
                    name="info_type",
                    label="信息类型",
                    type=InputType.DROPDOWN,
                    required=True,
                    options=[
                        "all_env_vars",
                        "get_env_var",
                        "temp_folder",
                        "user_folder",
                        "system_info"
                    ],
                    description="要获取的信息类型"
                ),
                NodeInput(
                    name="env_key",
                    label="环境变量名",
                    type=InputType.TEXT,
                    required=False,
                    description="获取指定环境变量时必填"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="computer_info",
                    label="电脑信息",
                    description="获取到的电脑信息"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """获取电脑信息"""
        info_type = self.get_required_input(inputs, "info_type")
        env_key = self.get_input_value(inputs, "env_key", "")

        try:
            if info_type == "all_env_vars":
                # 获取所有环境变量
                return {
                    "computer_info": {
                        "success": True,
                        "type": "all_env_vars",
                        "data": dict(os.environ)
                    }
                }

            elif info_type == "get_env_var":
                # 获取指定环境变量
                if not env_key:
                    return {
                        "computer_info": {
                            "success": False,
                            "error": "获取环境变量时必须指定变量名"
                        }
                    }
                value = os.environ.get(env_key)
                if value is None:
                    return {
                        "computer_info": {
                            "success": False,
                            "error": f"环境变量 {env_key} 不存在"
                        }
                    }
                return {
                    "computer_info": {
                        "success": True,
                        "type": "get_env_var",
                        "key": env_key,
                        "value": value
                    }
                }

            elif info_type == "temp_folder":
                # 获取临时文件夹路径
                import tempfile
                return {
                    "computer_info": {
                        "success": True,
                        "type": "temp_folder",
                        "path": tempfile.gettempdir()
                    }
                }

            elif info_type == "user_folder":
                # 获取用户文件夹路径
                return {
                    "computer_info": {
                        "success": True,
                        "type": "user_folder",
                        "path": os.path.expanduser("~")
                    }
                }

            elif info_type == "system_info":
                # 获取系统信息
                return {
                    "computer_info": {
                        "success": True,
                        "type": "system_info",
                        "system": platform.system(),
                        "release": platform.release(),
                        "version": platform.version(),
                        "machine": platform.machine(),
                        "processor": platform.processor(),
                        "python_version": platform.python_version()
                    }
                }

            else:
                return {
                    "computer_info": {
                        "success": False,
                        "error": f"不支持的信息类型: {info_type}"
                    }
                }

        except Exception as e:
            return {
                "computer_info": {
                    "success": False,
                    "error": str(e)
                }
            }

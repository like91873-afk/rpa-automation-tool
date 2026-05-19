"""
Python代码执行节点

执行Python代码，支持变量传递和结果获取
"""

import sys
import traceback
from io import StringIO
from typing import Any, Dict, List

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


class PythonExecNode(BaseNode):
    """
    Python代码执行节点

    参数说明:
    - python_code: Python代码，可使用已有全局变量，并且可以将特定变量定义到全局
    - timeout: 执行超时时间（单位：秒），默认最大1800秒
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.PYTHON_EXEC,
            name="Python代码执行",
            description="执行Python代码，支持变量传递和结果获取",
            category="Python",
            inputs=[
                NodeInput(
                    name="python_code",
                    label="Python代码",
                    type=InputType.CODE,
                    required=True,
                    description="Python代码，其中可以直接使用已有的全局变量，并且可以将特定变量定义到全局，以获取其结果"
                ),
                NodeInput(
                    name="timeout",
                    label="执行超时时间(秒)",
                    type=InputType.NUMBER,
                    required=False,
                    default=1800,
                    description="默认最大1800秒"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="python_code_result",
                    label="代码执行结果",
                    description="返回代码执行的输出及保存结果"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """执行Python代码"""
        code = self.get_required_input(inputs, "python_code")
        timeout = self.get_input_value(inputs, "timeout", 1800)

        # 准备执行环境
        exec_globals = {
            "__builtins__": __builtins__,
        }
        # 注入上下文变量
        exec_globals.update(context.variables)

        exec_locals = {}

        # 捕获输出
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        stdout_output = ""
        stderr_output = ""
        error_occurred = False

        try:
            # 执行代码
            exec(code, exec_globals, exec_locals)

            stdout_output = sys.stdout.getvalue()
            stderr_output = sys.stderr.getvalue()

            # 将新定义的变量保存到上下文
            saved_vars = {}
            for key, value in exec_locals.items():
                if not key.startswith("_") and key not in exec_globals:
                    context.set_variable(key, value)
                    saved_vars[key] = value

            return {
                "python_code_result": {
                    "success": True,
                    "stdout": stdout_output,
                    "stderr": stderr_output,
                    "variables": saved_vars
                }
            }

        except Exception as e:
            error_occurred = True
            stdout_output = sys.stdout.getvalue()
            stderr_output = sys.stderr.getvalue()
            error_message = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

            return {
                "python_code_result": {
                    "success": False,
                    "stdout": stdout_output,
                    "stderr": stderr_output,
                    "error": error_message
                }
            }

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


class PythonScriptNode(BaseNode):
    """
    Python脚本文件执行节点

    在新进程中执行Python文件，程序不会直接数据交互，适用于执行特定Python功能脚本
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.PYTHON_SCRIPT,
            name="执行Python脚本",
            description="在新进程中执行Python文件",
            category="Python",
            inputs=[
                NodeInput(
                    name="script_path",
                    label="脚本文件路径",
                    type=InputType.FILE_PATH,
                    required=True,
                    description="Python脚本文件的完整路径"
                ),
                NodeInput(
                    name="args",
                    label="命令行参数",
                    type=InputType.TEXT,
                    required=False,
                    default="",
                    description="传递给脚本的命令行参数，多个参数用空格分隔"
                ),
                NodeInput(
                    name="timeout",
                    label="执行超时时间(秒)",
                    type=InputType.NUMBER,
                    required=False,
                    default=1800,
                    description="-1表示不限制超时时间"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="script_result",
                    label="脚本执行结果",
                    description="脚本执行的输出结果"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """执行Python脚本"""
        import subprocess

        script_path = self.get_required_input(inputs, "script_path")
        args = self.get_input_value(inputs, "args", "")
        timeout = self.get_input_value(inputs, "timeout", 1800)

        # 解析变量
        script_path = context.resolve_variables(script_path)
        args = context.resolve_variables(args)

        # 构建命令
        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args.split())

        try:
            # 执行脚本
            timeout_val = timeout if timeout > 0 else None
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_val,
                cwd=None
            )

            return {
                "script_result": {
                    "success": result.returncode == 0,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            }

        except subprocess.TimeoutExpired:
            return {
                "script_result": {
                    "success": False,
                    "error": f"脚本执行超时（{timeout}秒）"
                }
            }
        except FileNotFoundError:
            return {
                "script_result": {
                    "success": False,
                    "error": f"脚本文件不存在: {script_path}"
                }
            }
        except Exception as e:
            return {
                "script_result": {
                    "success": False,
                    "error": str(e)
                }
            }

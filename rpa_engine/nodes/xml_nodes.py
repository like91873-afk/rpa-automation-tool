"""
XML操作节点

提供数据保存为XML文件的功能
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict
from pathlib import Path

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


class XMLSaveNode(BaseNode):
    """
    XML保存节点

    将数据保存为XML文件

    参数说明:
    - data_key: 数据保存到XML时的key（必须提供）
    - save_dir: 保存文件存放目录
    - file_name: 文件名
    - file_encoding: 文件编码（UTF-8/GBK/GB2312/ASCII）
    - exists_handle: 存在时处理方式（存在时忽略/存在时报错/存在时先备份再新建/存在时先删除再新建）

    输出说明:
    - data_xml_file_path: 返回保存数据的XML文件路径
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.XML_SAVE,
            name="保存为XML",
            description="将数据保存为XML文件",
            category="数据处理",
            inputs=[
                NodeInput(
                    name="data_key",
                    label="数据保存到XML时的key",
                    type=InputType.TEXT,
                    required=True,
                    description="必须提供，作为XML根元素的key名称"
                ),
                NodeInput(
                    name="save_dir",
                    label="保存文件存放目录",
                    type=InputType.FILE_PATH,
                    required=True,
                    description="保存文件存放目录"
                ),
                NodeInput(
                    name="file_name",
                    label="文件名",
                    type=InputType.TEXT,
                    required=True,
                    description="文件名（不含扩展名会自动添加.xml）"
                ),
                NodeInput(
                    name="file_encoding",
                    label="文件编码",
                    type=InputType.DROPDOWN,
                    required=True,
                    default="UTF-8",
                    options=["UTF-8", "GBK", "GB2312", "ASCII"],
                    description="文件编码格式"
                ),
                NodeInput(
                    name="exists_handle",
                    label="存在时处理方式",
                    type=InputType.DROPDOWN,
                    required=True,
                    default="backup",
                    options=["ignore", "error", "backup", "delete"],
                    description="存在时忽略(不新建)、存在时报错、存在时先备份再新建、存在时先删除再新建"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="data_xml_file_path",
                    label="XML文件路径",
                    description="返回保存数据的XML文件路径"
                ),
            ]
        )

    def _dict_to_xml(self, data: Any, root_tag: str, parent: ET.Element = None) -> ET.Element:
        """递归将字典/列表数据转换为XML元素"""
        if parent is None:
            root = ET.Element(root_tag)
        else:
            root = ET.SubElement(parent, root_tag)

        if isinstance(data, dict):
            for key, value in data.items():
                # 清理key名称（XML标签不能以数字开头）
                clean_key = str(key)
                if clean_key[0].isdigit():
                    clean_key = f"item_{clean_key}"
                self._dict_to_xml(value, clean_key, root)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._dict_to_xml(item, f"item", root)
        else:
            root.text = str(data) if data is not None else ""

        return root

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """保存数据为XML文件"""
        data_key = self.get_required_input(inputs, "data_key")
        save_dir = self.get_required_input(inputs, "save_dir")
        file_name = self.get_required_input(inputs, "file_name")
        file_encoding = self.get_input_value(inputs, "file_encoding", "UTF-8")
        exists_handle = self.get_input_value(inputs, "exists_handle", "backup")

        # 解析变量
        data_key = context.resolve_variables(data_key)
        save_dir = context.resolve_variables(save_dir)
        file_name = context.resolve_variables(file_name)

        # 确保文件名有.xml扩展名
        if not file_name.endswith(".xml"):
            file_name = f"{file_name}.xml"

        # 构建完整文件路径
        file_path = os.path.join(save_dir, file_name)

        try:
            # 创建目录（如果不存在）
            os.makedirs(save_dir, exist_ok=True)

            # 检查文件是否存在
            if os.path.exists(file_path):
                if exists_handle == "ignore":
                    return {
                        "data_xml_file_path": {
                            "success": True,
                            "path": file_path,
                            "action": "ignored",
                            "message": "文件已存在，忽略创建"
                        }
                    }
                elif exists_handle == "error":
                    raise FileExistsError(f"文件已存在: {file_path}")
                elif exists_handle == "backup":
                    # 备份现有文件
                    backup_path = f"{file_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
                    os.rename(file_path, backup_path)
                elif exists_handle == "delete":
                    os.remove(file_path)

            # 获取数据
            data = context.get_variable(data_key) if context.has_variable(data_key) else data_key

            # 创建XML
            root = self._dict_to_xml(data, data_key)

            # 创建XML树
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")

            # 保存文件
            tree.write(file_path, encoding=file_encoding, xml_declaration=True)

            return {
                "data_xml_file_path": {
                    "success": True,
                    "path": file_path,
                    "encoding": file_encoding,
                    "message": "XML文件保存成功"
                }
            }

        except FileExistsError as e:
            return {
                "data_xml_file_path": {
                    "success": False,
                    "error": str(e)
                }
            }
        except Exception as e:
            return {
                "data_xml_file_path": {
                    "success": False,
                    "error": f"保存XML文件失败: {str(e)}"
                }
            }

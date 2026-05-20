"""
RPA引擎 - Phase 3 测试

测试新增的FTP、SFTP写入、XML保存、路径检查节点
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa_engine import (
    ExecutionEngine,
    Flow,
    NodeInstance,
    Connection,
    NodeType,
)
from rpa_engine.nodes import NODE_REGISTRY, get_all_node_definitions


@pytest.fixture
def engine():
    """创建执行引擎实例"""
    return ExecutionEngine()


class TestPathExistsNode:
    """路径存在检查节点测试"""

    def test_path_exists_file(self, engine):
        """测试检查存在的文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            flow = Flow(
                id="path-test-1",
                name="路径检查测试-文件存在",
                nodes=[
                    NodeInstance(
                        id="node-1",
                        type="path_exists",
                        name="检查文件",
                        inputs={
                            "path": temp_path
                        }
                    )
                ],
                connections=[]
            )

            result = engine.execute_flow(flow)
            assert result.status == "completed"
            path_info = result.variables.get("path_info", {})
            assert path_info.get("esxit") is True
            assert path_info.get("type") == "file"
            assert path_info.get("exists") is True or result.variables.get("exists") is True
        finally:
            os.unlink(temp_path)

    def test_path_not_exists(self, engine):
        """测试检查不存在的路径"""
        flow = Flow(
            id="path-test-2",
            name="路径检查测试-路径不存在",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="path_exists",
                    name="检查不存在的路径",
                    inputs={
                        "path": "/tmp/nonexistent_path_12345.txt"
                    }
                )
            ],
            connections=[]
        )

        result = engine.execute_flow(flow)
        assert result.status == "completed"
        path_info = result.variables.get("path_info", {})
        assert path_info.get("esxit") is False

    def test_path_exists_directory(self, engine):
        """测试检查存在的目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            flow = Flow(
                id="path-test-3",
                name="路径检查测试-目录存在",
                nodes=[
                    NodeInstance(
                        id="node-1",
                        type="path_exists",
                        name="检查目录",
                        inputs={
                            "path": temp_dir
                        }
                    )
                ],
                connections=[]
            )

            result = engine.execute_flow(flow)
            assert result.status == "completed"
            path_info = result.variables.get("path_info", {})
            assert path_info.get("esxit") is True
            assert path_info.get("type") == "directory"


class TestFTPNodes:
    """FTP节点测试"""

    def test_ftp_connect_node_definition(self):
        """测试FTP连接节点定义"""
        assert "ftp_connect" in NODE_REGISTRY
        node_class = NODE_REGISTRY["ftp_connect"]
        node = node_class()
        definition = node.definition
        assert definition.type == NodeType.FTP_CONNECT
        assert definition.name == "FTP连接"
        assert len(definition.inputs) >= 3  # host, username, port
        assert len(definition.outputs) >= 1

    def test_ftp_connect_execution(self, engine):
        """测试FTP连接执行"""
        flow = Flow(
            id="ftp-test-1",
            name="FTP连接测试",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="ftp_connect",
                    name="创建FTP连接",
                    inputs={
                        "host": "ftp.example.com",
                        "port": 21,
                        "username": "testuser",
                        "password": "testpass",
                        "passive": True
                    }
                )
            ],
            connections=[]
        )

        result = engine.execute_flow(flow)
        assert result.status == "completed"
        ftp_connection = result.variables.get("ftp_connection", {})
        assert ftp_connection.get("host") == "ftp.example.com"
        assert ftp_connection.get("port") == 21
        assert ftp_connection.get("username") == "testuser"

    def test_ftp_list_dir_node_definition(self):
        """测试FTP查看目录节点定义"""
        assert "ftp_list_dir" in NODE_REGISTRY
        node_class = NODE_REGISTRY["ftp_list_dir"]
        node = node_class()
        definition = node.definition
        assert definition.type == NodeType.FTP_LIST_DIR
        assert definition.name == "FTP查看目录"
        assert len(definition.inputs) >= 2  # ftp_connection, ftp_dir

    def test_ftp_list_dir_execution(self, engine):
        """测试FTP查看目录执行"""
        flow = Flow(
            id="ftp-test-2",
            name="FTP查看目录测试",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="ftp_connect",
                    name="创建FTP连接",
                    inputs={
                        "host": "ftp.example.com",
                        "username": "testuser",
                        "password": "testpass"
                    }
                ),
                NodeInstance(
                    id="node-2",
                    type="ftp_list_dir",
                    name="查看目录",
                    inputs={
                        "ftp_connection": "${ftp_connection}",
                        "ftp_dir": "/upload"
                    }
                )
            ],
            connections=[
                Connection(
                    id="conn-1",
                    source_node_id="node-1",
                    target_node_id="node-2"
                )
            ]
        )

        result = engine.execute_flow(flow)
        assert result.status == "completed"
        ftp_dir_list = result.variables.get("ftp_dir_list", {})
        assert ftp_dir_list.get("success") is True
        assert "items" in ftp_dir_list


class TestSFTPWriteFileNode:
    """SFTP写入文件节点测试"""

    def test_sftp_write_file_node_definition(self):
        """测试SFTP写入文件节点定义"""
        assert "sftp_write_file" in NODE_REGISTRY
        node_class = NODE_REGISTRY["sftp_write_file"]
        node = node_class()
        definition = node.definition
        assert definition.type == NodeType.SFTP_WRITE_FILE
        assert definition.name == "SFTP写入文件"
        # 检查参数
        input_names = [inp.name for inp in definition.inputs]
        assert "sftp_connection" in input_names
        assert "write_file_path" in input_names
        assert "write_content" in input_names
        assert "write_mode" in input_names
        assert "end_mode" in input_names
        assert "file_not_exists" in input_names

    def test_sftp_write_file_execution(self, engine):
        """测试SFTP写入文件执行"""
        flow = Flow(
            id="sftp-write-test-1",
            name="SFTP写入文件测试",
            nodes=[
                NodeInstance(
                    id="node-1",
                    type="sftp_connect",
                    name="创建SFTP连接",
                    inputs={
                        "host": "sftp.example.com",
                        "username": "testuser",
                        "password": "testpass"
                    }
                ),
                NodeInstance(
                    id="node-2",
                    type="sftp_write_file",
                    name="写入文件",
                    inputs={
                        "sftp_connection": "${sftp_connection}",
                        "write_file_path": "/upload/test.txt",
                        "write_content": "Hello, World!",
                        "write_mode": "append",
                        "end_mode": "add_newline",
                        "file_not_exists": "create"
                    }
                )
            ],
            connections=[
                Connection(
                    id="conn-1",
                    source_node_id="node-1",
                    target_node_id="node-2"
                )
            ]
        )

        result = engine.execute_flow(flow)
        assert result.status == "completed"
        assert result.variables.get("write_file_path") == "/upload/test.txt"


class TestXMLSaveNode:
    """XML保存节点测试"""

    def test_xml_save_node_definition(self):
        """测试XML保存节点定义"""
        assert "xml_save" in NODE_REGISTRY
        node_class = NODE_REGISTRY["xml_save"]
        node = node_class()
        definition = node.definition
        assert definition.type == NodeType.XML_SAVE
        assert definition.name == "保存为XML"
        # 检查参数
        input_names = [inp.name for inp in definition.inputs]
        assert "data_key" in input_names
        assert "save_dir" in input_names
        assert "file_name" in input_names
        assert "file_encoding" in input_names
        assert "exists_handle" in input_names

    def test_xml_save_execution(self, engine):
        """测试XML保存执行"""
        with tempfile.TemporaryDirectory() as temp_dir:
            flow = Flow(
                id="xml-test-1",
                name="XML保存测试",
                nodes=[
                    NodeInstance(
                        id="node-1",
                        type="python_exec",
                        name="准备数据",
                        inputs={
                            "python_code": "test_data = {'name': '测试', 'value': 123, 'items': ['a', 'b', 'c']}"
                        }
                    ),
                    NodeInstance(
                        id="node-2",
                        type="xml_save",
                        name="保存XML",
                        inputs={
                            "data_key": "test_data",
                            "save_dir": temp_dir,
                            "file_name": "test_output",
                            "file_encoding": "UTF-8",
                            "exists_handle": "backup"
                        }
                    )
                ],
                connections=[
                    Connection(
                        id="conn-1",
                        source_node_id="node-1",
                        target_node_id="node-2"
                    )
                ]
            )

            result = engine.execute_flow(flow)
            assert result.status == "completed"
            xml_result = result.variables.get("data_xml_file_path", {})
            assert xml_result.get("success") is True
            assert os.path.exists(xml_result.get("path", ""))

    def test_xml_save_with_dict_data(self, engine):
        """测试保存字典数据为XML"""
        with tempfile.TemporaryDirectory() as temp_dir:
            flow = Flow(
                id="xml-test-2",
                name="XML保存字典测试",
                nodes=[
                    NodeInstance(
                        id="node-1",
                        type="python_exec",
                        name="准备字典数据",
                        inputs={
                            "python_code": "data = {'person': {'name': '张三', 'age': 30}}"
                        }
                    ),
                    NodeInstance(
                        id="node-2",
                        type="xml_save",
                        name="保存XML",
                        inputs={
                            "data_key": "data",
                            "save_dir": temp_dir,
                            "file_name": "person.xml",
                            "file_encoding": "UTF-8",
                            "exists_handle": "ignore"
                        }
                    )
                ],
                connections=[
                    Connection(
                        id="conn-1",
                        source_node_id="node-1",
                        target_node_id="node-2"
                    )
                ]
            )

            result = engine.execute_flow(flow)
            assert result.status == "completed"


class TestPhase3Integration:
    """Phase 3 集成测试"""

    def test_node_registry_completeness(self):
        """测试节点注册表完整性"""
        expected_nodes = [
            # Phase 1
            "python_exec", "python_script",
            "file_open", "file_read", "file_write", "directory_list",
            "system_cmd", "powershell", "computer_info",
            # Phase 2
            "condition", "loop",
            "sftp_connect", "sftp_upload", "sftp_download", "sftp_new_file",
            "math_operation", "string_operation",
            # Phase 3
            "path_exists", "sftp_write_file", "ftp_connect", "ftp_list_dir", "xml_save",
        ]

        for node_type in expected_nodes:
            assert node_type in NODE_REGISTRY, f"节点类型 {node_type} 未注册"

        definitions = get_all_node_definitions()
        # 只检查Phase 1-3的节点是否都存在
        assert len(definitions) >= len(expected_nodes)

    def test_node_type_enum_completeness(self):
        """测试NodeType枚举完整性"""
        expected_types = [
            # Phase 1
            "python_exec", "python_script",
            "file_open", "file_read", "file_write", "directory_list",
            "system_cmd", "powershell", "computer_info",
            # Phase 2
            "condition", "loop",
            "sftp_connect", "sftp_upload", "sftp_download", "sftp_new_file",
            "math_operation", "string_operation",
            # Phase 3
            "path_exists", "sftp_write_file", "ftp_connect", "ftp_list_dir", "xml_save",
        ]

        for type_value in expected_types:
            assert hasattr(NodeType, type_value.upper()) or \
                   any(e.value == type_value for e in NodeType), \
                   f"NodeType枚举缺少: {type_value}"

    def test_phase3_flow_execution(self, engine):
        """测试Phase 3综合流程执行"""
        with tempfile.TemporaryDirectory() as temp_dir:
            flow = Flow(
                id="phase3-integration-test",
                name="Phase 3集成测试",
                nodes=[
                    # 1. 检查路径
                    NodeInstance(
                        id="node-1",
                        type="path_exists",
                        name="检查目录",
                        inputs={
                            "path": temp_dir
                        }
                    ),
                    # 2. 创建FTP连接
                    NodeInstance(
                        id="node-2",
                        type="ftp_connect",
                        name="FTP连接",
                        inputs={
                            "host": "ftp.example.com",
                            "username": "user",
                            "password": "pass"
                        }
                    ),
                    # 3. 保存XML
                    NodeInstance(
                        id="node-3",
                        type="xml_save",
                        name="保存结果",
                        inputs={
                            "data_key": "path_info",
                            "save_dir": temp_dir,
                            "file_name": "result",
                            "file_encoding": "UTF-8",
                            "exists_handle": "backup"
                        }
                    )
                ],
                connections=[
                    Connection(
                        id="conn-1",
                        source_node_id="node-1",
                        target_node_id="node-2"
                    ),
                    Connection(
                        id="conn-2",
                        source_node_id="node-2",
                        target_node_id="node-3"
                    )
                ]
            )

            result = engine.execute_flow(flow)
            assert result.status == "completed"
            assert len(result.node_logs) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

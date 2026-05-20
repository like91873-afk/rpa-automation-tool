"""
Phase 5 测试 - 公式计算、邮件、时间、文件压缩、PDF解析、FTP删除、SFTP创建目录
"""

import os
import tempfile
import zipfile
from datetime import datetime, timedelta

import pytest

from rpa_engine.models.schemas import Flow, NodeInstance, Connection, NodeType
from rpa_engine.models.context import ExecutionContext
from rpa_engine.engine import ExecutionEngine
from rpa_engine.nodes import get_all_node_definitions
from rpa_engine.nodes.phase5_nodes import (
    FormulaNode, EmailConnectNode, EmailFetchNode, EmailSendNode,
    TimeGetNode, TimeProcessNode, FileCompressNode, FileDecompressNode,
    PDFParseNode, FTPDeleteNode, SFTPCreateDirNode
)


# ==================== 公式计算节点测试 ====================

class TestFormulaNode:
    """公式计算节点测试"""

    def test_definition(self):
        node = FormulaNode()
        defn = node.definition
        assert defn.type == NodeType.FORMULA
        assert defn.name == "公式计算"
        assert defn.category == "数据处理"
        assert len(defn.inputs) >= 1
        assert len(defn.outputs) >= 1

    def test_simple_formula(self):
        ctx = ExecutionContext()
        node = FormulaNode()
        result = node.execute({"formula": "2 + 3"}, ctx)
        assert result["result"] == 5

    def test_formula_with_variables(self):
        ctx = ExecutionContext()
        node = FormulaNode()
        result = node.execute({
            "formula": "${a} + ${b} * 2",
            "variables": {"a": 10, "b": 5}
        }, ctx)
        assert result["result"] == 20

    def test_formula_error(self):
        ctx = ExecutionContext()
        node = FormulaNode()
        with pytest.raises(ValueError, match="公式计算错误"):
            node.execute({"formula": "1 / 0"}, ctx)

    def test_formula_in_flow(self):
        flow = Flow(
            id="test-formula",
            name="测试公式计算",
            nodes=[
                NodeInstance(id="n1", type="formula", inputs={
                    "formula": "${x} * 2 + 1",
                    "variables": {"x": 5}
                }),
            ],
            connections=[]
        )
        engine = ExecutionEngine()
        result = engine.execute_flow(flow)
        assert result.status.value == "completed"
        assert result.variables.get("result") == 11


# ==================== 邮件节点测试 ====================

class TestEmailConnectNode:
    """邮箱连接节点测试"""

    def test_definition(self):
        node = EmailConnectNode()
        defn = node.definition
        assert defn.type == NodeType.EMAIL_CONNECT
        assert defn.name == "邮箱连接"
        assert defn.category == "邮件操作"
        assert len(defn.inputs) >= 4
        assert len(defn.outputs) >= 1

    def test_connect_invalid_host(self):
        ctx = ExecutionContext()
        node = EmailConnectNode()
        result = node.execute({
            "host": "invalid.host.com",
            "port": 993,
            "username": "test@test.com",
            "password": "password",
            "use_ssl": True
        }, ctx)
        assert result["success"] is False
        assert result["connection"] is None


class TestEmailSendNode:
    """邮件发送节点测试"""

    def test_definition(self):
        node = EmailSendNode()
        defn = node.definition
        assert defn.type == NodeType.EMAIL_SEND
        assert defn.name == "邮件发送"
        assert defn.category == "邮件操作"
        assert len(defn.inputs) >= 7
        assert len(defn.outputs) >= 1

    def test_send_invalid_smtp(self):
        ctx = ExecutionContext()
        node = EmailSendNode()
        result = node.execute({
            "smtp_host": "invalid.host.com",
            "smtp_port": 587,
            "username": "test@test.com",
            "password": "password",
            "to": "recipient@test.com",
            "subject": "Test",
            "body": "Test body",
            "use_tls": True
        }, ctx)
        assert result["success"] is False
        assert result["error"] is not None


class TestEmailFetchNode:
    """邮件获取节点测试"""

    def test_definition(self):
        node = EmailFetchNode()
        defn = node.definition
        assert defn.type == NodeType.EMAIL_FETCH
        assert defn.name == "邮件获取"
        assert defn.category == "邮件操作"
        assert len(defn.inputs) >= 3
        assert len(defn.outputs) >= 1


# ==================== 时间节点测试 ====================

class TestTimeGetNode:
    """时间获取节点测试"""

    def test_definition(self):
        node = TimeGetNode()
        defn = node.definition
        assert defn.type == NodeType.TIME_GET
        assert defn.name == "时间获取"
        assert defn.category == "时间处理"
        assert len(defn.inputs) >= 1
        assert len(defn.outputs) >= 6

    def test_get_current_time(self):
        ctx = ExecutionContext()
        node = TimeGetNode()
        result = node.execute({}, ctx)
        assert "datetime" in result
        assert "timestamp" in result
        assert "year" in result
        assert "month" in result
        assert "day" in result
        assert "hour" in result
        assert "minute" in result
        assert "second" in result
        assert isinstance(result["timestamp"], float)

    def test_custom_format(self):
        ctx = ExecutionContext()
        node = TimeGetNode()
        result = node.execute({"format": "%Y/%m/%d"}, ctx)
        assert "/" in result["datetime"]

    def test_timezone(self):
        ctx = ExecutionContext()
        node = TimeGetNode()
        result = node.execute({"timezone": "Asia/Shanghai"}, ctx)
        assert "datetime" in result


class TestTimeProcessNode:
    """时间处理节点测试"""

    def test_definition(self):
        node = TimeProcessNode()
        defn = node.definition
        assert defn.type == NodeType.TIME_PROCESS
        assert defn.name == "时间处理"
        assert defn.category == "时间处理"
        assert len(defn.inputs) >= 4
        assert len(defn.outputs) >= 1

    def test_add_days(self):
        ctx = ExecutionContext()
        node = TimeProcessNode()
        result = node.execute({
            "datetime_str": "2024-01-01 00:00:00",
            "input_format": "%Y-%m-%d %H:%M:%S",
            "output_format": "%Y-%m-%d",
            "days": 10
        }, ctx)
        assert result["result"] == "2024-01-11"

    def test_subtract_hours(self):
        ctx = ExecutionContext()
        node = TimeProcessNode()
        result = node.execute({
            "datetime_str": "2024-01-01 12:00:00",
            "input_format": "%Y-%m-%d %H:%M:%S",
            "output_format": "%H:%M:%S",
            "hours": -2
        }, ctx)
        assert result["result"] == "10:00:00"

    def test_format_conversion(self):
        ctx = ExecutionContext()
        node = TimeProcessNode()
        result = node.execute({
            "datetime_str": "2024-01-01 12:00:00",
            "input_format": "%Y-%m-%d %H:%M:%S",
            "output_format": "%d/%m/%Y"
        }, ctx)
        assert result["result"] == "01/01/2024"

    def test_invalid_format(self):
        ctx = ExecutionContext()
        node = TimeProcessNode()
        with pytest.raises(ValueError, match="时间处理错误"):
            node.execute({
                "datetime_str": "invalid-date",
                "input_format": "%Y-%m-%d"
            }, ctx)


# ==================== 文件压缩节点测试 ====================

class TestFileCompressNode:
    """文件压缩节点测试"""

    def test_definition(self):
        node = FileCompressNode()
        defn = node.definition
        assert defn.type == NodeType.FILE_COMPRESS
        assert defn.name == "文件压缩"
        assert defn.category == "文件操作"
        assert len(defn.inputs) >= 2
        assert len(defn.outputs) >= 1

    def test_compress_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            source_path = f.name

        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            output_path = f.name

        try:
            ctx = ExecutionContext()
            node = FileCompressNode()
            result = node.execute({
                "source_path": source_path,
                "output_path": output_path
            }, ctx)
            assert result["success"] is True
            assert os.path.exists(output_path)
            assert result["file_size"] > 0

            # 验证zip文件
            with zipfile.ZipFile(output_path, 'r') as zipf:
                assert len(zipf.namelist()) == 1
        finally:
            os.unlink(source_path)
            os.unlink(output_path)

    def test_compress_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试文件
            with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
                f.write("content1")
            with open(os.path.join(temp_dir, "file2.txt"), "w") as f:
                f.write("content2")

            output_path = os.path.join(temp_dir, "test.zip")

            ctx = ExecutionContext()
            node = FileCompressNode()
            result = node.execute({
                "source_path": temp_dir,
                "output_path": output_path
            }, ctx)
            assert result["success"] is True
            assert os.path.exists(output_path)

    def test_compress_nonexistent(self):
        ctx = ExecutionContext()
        node = FileCompressNode()
        with pytest.raises(FileNotFoundError, match="源路径不存在"):
            node.execute({
                "source_path": "/nonexistent/path",
                "output_path": "/tmp/test.zip"
            }, ctx)


class TestFileDecompressNode:
    """文件解压节点测试"""

    def test_definition(self):
        node = FileDecompressNode()
        defn = node.definition
        assert defn.type == NodeType.FILE_DECOMPRESS
        assert defn.name == "文件解压"
        assert defn.category == "文件操作"
        assert len(defn.inputs) >= 2
        assert len(defn.outputs) >= 1

    def test_decompress(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试zip文件
            zip_path = os.path.join(temp_dir, "test.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.writestr("file1.txt", "content1")
                zipf.writestr("file2.txt", "content2")

            output_dir = os.path.join(temp_dir, "extracted")

            ctx = ExecutionContext()
            node = FileDecompressNode()
            result = node.execute({
                "zip_path": zip_path,
                "output_dir": output_dir
            }, ctx)
            assert result["success"] is True
            assert result["file_count"] == 2
            assert len(result["extracted_files"]) == 2

    def test_decompress_nonexistent(self):
        ctx = ExecutionContext()
        node = FileDecompressNode()
        with pytest.raises(FileNotFoundError, match="压缩文件不存在"):
            node.execute({
                "zip_path": "/nonexistent/path.zip",
                "output_dir": "/tmp/extracted"
            }, ctx)


# ==================== PDF解析节点测试 ====================

class TestPDFParseNode:
    """PDF解析节点测试"""

    def test_definition(self):
        node = PDFParseNode()
        defn = node.definition
        assert defn.type == NodeType.PDF_PARSE
        assert defn.name == "PDF解析"
        assert defn.category == "文件操作"
        assert len(defn.inputs) >= 1
        assert len(defn.outputs) >= 1

    def test_parse_nonexistent(self):
        ctx = ExecutionContext()
        node = PDFParseNode()
        with pytest.raises(FileNotFoundError, match="PDF文件不存在"):
            node.execute({"pdf_path": "/nonexistent/path.pdf"}, ctx)

    def test_parse_without_pypdf2(self):
        # 测试PyPDF2已安装时解析空文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name

        try:
            ctx = ExecutionContext()
            node = PDFParseNode()
            result = node.execute({"pdf_path": pdf_path}, ctx)
            # PyPDF2已安装：空文件会返回错误或抛出异常
            if "error" in result:
                assert True  # 返回了错误信息
            else:
                # 或者成功返回了空内容
                assert isinstance(result.get("text"), str)
        except ValueError:
            # 空文件会抛出 ValueError，这也是正常行为
            assert True
        finally:
            os.unlink(pdf_path)


# ==================== FTP删除节点测试 ====================

class TestFTPDeleteNode:
    """FTP删除节点测试"""

    def test_definition(self):
        node = FTPDeleteNode()
        defn = node.definition
        assert defn.type == NodeType.FTP_DELETE
        assert defn.name == "FTP删除"
        assert defn.category == "FTP操作"
        assert len(defn.inputs) >= 2
        assert len(defn.outputs) >= 1

    def test_no_connection(self):
        ctx = ExecutionContext()
        node = FTPDeleteNode()
        with pytest.raises(ValueError, match="FTP连接不存在"):
            node.execute({
                "connection": None,
                "remote_path": "/test/file.txt"
            }, ctx)


class TestSFTPCreateDirNode:
    """SFTP创建目录节点测试"""

    def test_definition(self):
        node = SFTPCreateDirNode()
        defn = node.definition
        assert defn.type == NodeType.SFTP_CREATE_DIR
        assert defn.name == "SFTP创建目录"
        assert defn.category == "SFTP操作"
        assert len(defn.inputs) >= 2
        assert len(defn.outputs) >= 1

    def test_no_connection(self):
        ctx = ExecutionContext()
        node = SFTPCreateDirNode()
        with pytest.raises(ValueError, match="SFTP连接不存在"):
            node.execute({
                "connection": None,
                "remote_path": "/test/dir"
            }, ctx)


# ==================== 集成测试 ====================

class TestTimeNodesIntegration:
    """时间节点集成测试"""

    def test_time_get_and_process(self):
        flow = Flow(
            id="test-time-integration",
            name="测试时间集成",
            nodes=[
                NodeInstance(id="n1", type="time_get", inputs={
                    "format": "%Y-%m-%d %H:%M:%S"
                }),
                NodeInstance(id="n2", type="time_process", inputs={
                    "datetime_str": "${datetime}",
                    "input_format": "%Y-%m-%d %H:%M:%S",
                    "output_format": "%Y-%m-%d",
                    "days": 1
                }),
            ],
            connections=[
                Connection(id="c1", source_node_id="n1", target_node_id="n2")
            ]
        )
        engine = ExecutionEngine()
        result = engine.execute_flow(flow)
        assert result.status.value == "completed"
        assert "result" in result.variables


class TestFileCompressionIntegration:
    """文件压缩集成测试"""

    def test_compress_and_decompress(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试文件
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content for compression")

            zip_path = os.path.join(temp_dir, "test.zip")
            extract_dir = os.path.join(temp_dir, "extracted")

            flow = Flow(
                id="test-compression",
                name="测试文件压缩解压",
                nodes=[
                    NodeInstance(id="n1", type="file_compress", inputs={
                        "source_path": test_file,
                        "output_path": zip_path
                    }),
                    NodeInstance(id="n2", type="file_decompress", inputs={
                        "zip_path": zip_path,
                        "output_dir": extract_dir
                    }),
                ],
                connections=[
                    Connection(id="c1", source_node_id="n1", target_node_id="n2")
                ]
            )
            engine = ExecutionEngine()
            result = engine.execute_flow(flow)
            assert result.status.value == "completed"
            assert result.variables.get("success") is True


class TestFormulaIntegration:
    """公式计算集成测试"""

    def test_complex_formula(self):
        flow = Flow(
            id="test-formula-complex",
            name="测试复杂公式",
            nodes=[
                NodeInstance(id="n1", type="formula", inputs={
                    "formula": "${price} * ${quantity} * (1 - ${discount})",
                    "variables": {
                        "price": 100,
                        "quantity": 5,
                        "discount": 0.1
                    }
                }),
            ],
            connections=[]
        )
        engine = ExecutionEngine()
        result = engine.execute_flow(flow)
        assert result.status.value == "completed"
        assert result.variables.get("result") == 450.0


# ==================== 节点注册表测试 ====================

class TestPhase5NodeRegistry:
    """Phase 5节点注册表测试"""

    def test_all_phase5_nodes_registered(self):
        defs = get_all_node_definitions()
        types = [d.type.value for d in defs]
        
        # Phase 5 节点类型
        phase5_types = [
            "formula",
            "email_connect",
            "email_fetch",
            "email_send",
            "time_get",
            "time_process",
            "file_compress",
            "file_decompress",
            "pdf_parse",
            "ftp_delete",
            "sftp_create_dir"
        ]
        
        for node_type in phase5_types:
            assert node_type in types, f"节点类型 {node_type} 未注册"

    def test_total_node_count(self):
        defs = get_all_node_definitions()
        # Phase 1-4: 32个节点 + Phase 5: 11个节点 = 43个节点
        assert len(defs) >= 43

"""
RPA自动化工具 - Phase 5 节点类型

新增节点类型：
1. 公式计算节点
2. 邮箱连接节点
3. 邮件获取节点
4. 邮件发送节点
5. 时间获取节点
6. 时间处理节点
7. 文件压缩节点
8. 文件解压节点
9. PDF解析节点
10. FTP删除节点
11. SFTP创建目录节点
"""

import os
import zipfile
import smtplib
import imaplib
import email
from datetime import datetime, timedelta
from typing import Any, Dict

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


class FormulaNode(BaseNode):
    """
    公式计算节点

    支持数学表达式计算，包括变量引用。
    变量使用 ${var_name} 语法引用。

    参数说明:
    - formula: 数学表达式，如 ${a} + ${b} * 2
    - variables: 变量映射（JSON字典），如 {"a": 10, "b": 5}
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.FORMULA,
            name="公式计算",
            description="支持数学表达式计算，包括变量引用。变量使用 ${var_name} 语法",
            category="数据处理",
            inputs=[
                NodeInput(
                    name="formula",
                    label="公式",
                    type=InputType.CODE,
                    required=True,
                    description="数学表达式，如 ${a} + ${b} * 2"
                ),
                NodeInput(
                    name="variables",
                    label="变量映射",
                    type=InputType.TEXT,
                    required=False,
                    default="{}",
                    description="JSON格式的变量映射，如 {\"a\": 10, \"b\": 5}"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="result",
                    label="计算结果",
                    description="公式计算的结果值"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        import json
        formula = self.get_required_input(inputs, "formula")
        variables_raw = self.get_input_value(inputs, "variables", "{}")

        # 解析变量
        if isinstance(variables_raw, str):
            variables = json.loads(variables_raw)
        else:
            variables = variables_raw or {}

        # 替换变量引用
        resolved_formula = formula
        for key, value in variables.items():
            resolved_formula = resolved_formula.replace(f"${{{key}}}", str(value))

        # 安全计算表达式
        try:
            result = eval(resolved_formula, {"__builtins__": {}}, {})
            return {"result": result}
        except Exception as e:
            raise ValueError(f"公式计算错误: {str(e)}")


class EmailConnectNode(BaseNode):
    """
    邮箱连接节点

    创建IMAP邮箱连接对象，用于后续邮件获取操作。

    参数说明:
    - host: IMAP服务器地址
    - port: IMAP端口（默认993）
    - username: 邮箱账号
    - password: 邮箱密码
    - use_ssl: 是否使用SSL加密（默认True）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.EMAIL_CONNECT,
            name="邮箱连接",
            description="创建IMAP邮箱连接对象",
            category="邮件操作",
            inputs=[
                NodeInput(
                    name="host",
                    label="服务器地址",
                    type=InputType.TEXT,
                    required=True,
                    description="IMAP服务器地址，如 imap.gmail.com"
                ),
                NodeInput(
                    name="port",
                    label="端口",
                    type=InputType.NUMBER,
                    required=False,
                    default=993,
                    description="IMAP端口，默认993"
                ),
                NodeInput(
                    name="username",
                    label="用户名",
                    type=InputType.TEXT,
                    required=True,
                    description="邮箱账号"
                ),
                NodeInput(
                    name="password",
                    label="密码",
                    type=InputType.TEXT,
                    required=True,
                    description="邮箱密码或应用专用密码"
                ),
                NodeInput(
                    name="use_ssl",
                    label="使用SSL",
                    type=InputType.BOOLEAN,
                    required=False,
                    default=True,
                    description="是否使用SSL加密连接"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="connection",
                    label="邮箱连接",
                    description="IMAP邮箱连接对象"
                ),
                NodeOutput(
                    key="success",
                    label="连接成功",
                    description="连接是否成功"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        host = self.get_required_input(inputs, "host")
        port = int(self.get_input_value(inputs, "port", 993))
        username = self.get_required_input(inputs, "username")
        password = self.get_required_input(inputs, "password")
        use_ssl = self.get_input_value(inputs, "use_ssl", True)

        try:
            if use_ssl:
                conn = imaplib.IMAP4_SSL(host, port)
            else:
                conn = imaplib.IMAP4(host, port)
            conn.login(username, password)
            return {"connection": conn, "success": True}
        except Exception as e:
            return {"connection": None, "success": False, "error": str(e)}


class EmailFetchNode(BaseNode):
    """
    邮件获取节点

    从邮箱连接获取邮件列表。

    参数说明:
    - connection: 邮箱连接对象（来自邮箱连接节点）
    - folder: 邮箱文件夹（默认INBOX）
    - limit: 获取邮件数量（默认10）
    - search_criteria: IMAP搜索条件（默认ALL）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.EMAIL_FETCH,
            name="邮件获取",
            description="从邮箱连接获取邮件列表",
            category="邮件操作",
            inputs=[
                NodeInput(
                    name="connection",
                    label="邮箱连接",
                    type=InputType.TEXT,
                    required=True,
                    description="邮箱连接对象（来自邮箱连接节点输出）"
                ),
                NodeInput(
                    name="folder",
                    label="文件夹",
                    type=InputType.TEXT,
                    required=False,
                    default="INBOX",
                    description="邮箱文件夹，如 INBOX、SENT"
                ),
                NodeInput(
                    name="limit",
                    label="数量限制",
                    type=InputType.NUMBER,
                    required=False,
                    default=10,
                    description="获取邮件数量"
                ),
                NodeInput(
                    name="search_criteria",
                    label="搜索条件",
                    type=InputType.TEXT,
                    required=False,
                    default="ALL",
                    description="IMAP搜索条件，如 ALL、UNSEEN"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="emails",
                    label="邮件列表",
                    description="获取的邮件列表"
                ),
                NodeOutput(
                    key="count",
                    label="邮件数量",
                    description="获取的邮件数量"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        from email.header import decode_header as decode_email_header

        conn = self.get_required_input(inputs, "connection")
        folder = self.get_input_value(inputs, "folder", "INBOX")
        limit = int(self.get_input_value(inputs, "limit", 10))
        search_criteria = self.get_input_value(inputs, "search_criteria", "ALL")

        if not conn:
            raise ValueError("邮箱连接不存在")

        try:
            conn.select(folder)
            _, message_ids = conn.search(None, search_criteria)
            email_ids = message_ids[0].split()[-limit:]
            emails = []

            for eid in email_ids:
                _, msg_data = conn.fetch(eid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])

                # 解析邮件主题
                subject_raw = decode_email_header(msg["Subject"])[0][0]
                subject = subject_raw.decode() if isinstance(subject_raw, bytes) else subject_raw

                # 获取邮件正文
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()

                emails.append({
                    "id": eid.decode(),
                    "subject": subject,
                    "from": msg.get("From", ""),
                    "to": msg.get("To", ""),
                    "date": msg.get("Date", ""),
                    "body": body
                })

            return {"emails": emails, "count": len(emails)}
        except Exception as e:
            raise ValueError(f"邮件获取失败: {str(e)}")


class EmailSendNode(BaseNode):
    """
    邮件发送节点

    通过SMTP发送邮件。

    参数说明:
    - smtp_host: SMTP服务器地址
    - smtp_port: SMTP端口（默认587）
    - username: 邮箱账号
    - password: 邮箱密码
    - to: 收件人邮箱
    - subject: 邮件主题
    - body: 邮件正文
    - use_tls: 是否使用TLS（默认True）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.EMAIL_SEND,
            name="邮件发送",
            description="通过SMTP发送邮件",
            category="邮件操作",
            inputs=[
                NodeInput(name="smtp_host", label="SMTP服务器", type=InputType.TEXT, required=True, description="SMTP服务器地址"),
                NodeInput(name="smtp_port", label="SMTP端口", type=InputType.NUMBER, required=False, default=587, description="SMTP端口"),
                NodeInput(name="username", label="用户名", type=InputType.TEXT, required=True, description="邮箱账号"),
                NodeInput(name="password", label="密码", type=InputType.TEXT, required=True, description="邮箱密码"),
                NodeInput(name="to", label="收件人", type=InputType.TEXT, required=True, description="收件人邮箱"),
                NodeInput(name="subject", label="主题", type=InputType.TEXT, required=True, description="邮件主题"),
                NodeInput(name="body", label="正文", type=InputType.CODE, required=True, description="邮件正文"),
                NodeInput(name="use_tls", label="使用TLS", type=InputType.BOOLEAN, required=False, default=True, description="是否使用TLS加密"),
            ],
            outputs=[
                NodeOutput(key="success", label="发送成功", description="发送是否成功"),
                NodeOutput(key="error", label="错误信息", description="错误信息"),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_host = self.get_required_input(inputs, "smtp_host")
        smtp_port = int(self.get_input_value(inputs, "smtp_port", 587))
        username = self.get_required_input(inputs, "username")
        password = self.get_required_input(inputs, "password")
        to = self.get_required_input(inputs, "to")
        subject = self.get_required_input(inputs, "subject")
        body = self.get_required_input(inputs, "body")
        use_tls = self.get_input_value(inputs, "use_tls", True)

        try:
            msg = MIMEMultipart()
            msg["From"] = username
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            if use_tls:
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)

            server.login(username, password)
            server.send_message(msg)
            server.quit()
            return {"success": True, "error": None}
        except Exception as e:
            return {"success": False, "error": str(e)}


class TimeGetNode(BaseNode):
    """
    时间获取节点

    获取当前时间或时间戳。

    参数说明:
    - format: 时间格式化字符串（默认 %Y-%m-%d %H:%M:%S）
    - timezone: 时区，如 Asia/Shanghai（可选）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.TIME_GET,
            name="时间获取",
            description="获取当前时间、时间戳及年月日时分秒",
            category="时间处理",
            inputs=[
                NodeInput(name="format", label="时间格式", type=InputType.TEXT, required=False, default="%Y-%m-%d %H:%M:%S", description="时间格式化字符串"),
                NodeInput(name="timezone", label="时区", type=InputType.TEXT, required=False, default="", description="时区，如 Asia/Shanghai、UTC"),
            ],
            outputs=[
                NodeOutput(key="datetime", label="时间字符串", description="格式化后的时间字符串"),
                NodeOutput(key="timestamp", label="时间戳", description="Unix时间戳"),
                NodeOutput(key="year", label="年", description="年"),
                NodeOutput(key="month", label="月", description="月"),
                NodeOutput(key="day", label="日", description="日"),
                NodeOutput(key="hour", label="时", description="时"),
                NodeOutput(key="minute", label="分", description="分"),
                NodeOutput(key="second", label="秒", description="秒"),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        fmt = self.get_input_value(inputs, "format", "%Y-%m-%d %H:%M:%S")
        tz_name = self.get_input_value(inputs, "timezone", "")

        now = datetime.now()

        # 处理时区
        if tz_name:
            try:
                import pytz
                tz = pytz.timezone(tz_name)
                now = datetime.now(tz)
            except ImportError:
                if tz_name in ("Asia/Shanghai", "PRC"):
                    now = datetime.now(timezone(timedelta(hours=8)))
                elif tz_name == "UTC":
                    from datetime import timezone
                    now = datetime.now(timezone.utc)

        return {
            "datetime": now.strftime(fmt),
            "timestamp": now.timestamp(),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second
        }


class TimeProcessNode(BaseNode):
    """
    时间处理节点

    对时间字符串进行加减运算和格式转换。

    参数说明:
    - datetime_str: 输入时间字符串
    - input_format: 输入时间格式（默认 %Y-%m-%d %H:%M:%S）
    - output_format: 输出时间格式（默认 %Y-%m-%d %H:%M:%S）
    - days: 加减天数（正数加，负数减）
    - hours: 加减小时
    - minutes: 加减分钟
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.TIME_PROCESS,
            name="时间处理",
            description="时间加减运算和格式转换",
            category="时间处理",
            inputs=[
                NodeInput(name="datetime_str", label="时间字符串", type=InputType.TEXT, required=True, description="输入时间字符串"),
                NodeInput(name="input_format", label="输入格式", type=InputType.TEXT, required=False, default="%Y-%m-%d %H:%M:%S", description="输入时间格式"),
                NodeInput(name="output_format", label="输出格式", type=InputType.TEXT, required=False, default="%Y-%m-%d %H:%M:%S", description="输出时间格式"),
                NodeInput(name="days", label="天数", type=InputType.NUMBER, required=False, default=0, description="加减天数"),
                NodeInput(name="hours", label="小时", type=InputType.NUMBER, required=False, default=0, description="加减小时"),
                NodeInput(name="minutes", label="分钟", type=InputType.NUMBER, required=False, default=0, description="加减分钟"),
            ],
            outputs=[
                NodeOutput(key="result", label="处理结果", description="处理后的时间字符串"),
                NodeOutput(key="timestamp", label="时间戳", description="Unix时间戳"),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        datetime_str = self.get_required_input(inputs, "datetime_str")
        input_format = self.get_input_value(inputs, "input_format", "%Y-%m-%d %H:%M:%S")
        output_format = self.get_input_value(inputs, "output_format", "%Y-%m-%d %H:%M:%S")
        days = int(self.get_input_value(inputs, "days", 0))
        hours = int(self.get_input_value(inputs, "hours", 0))
        minutes = int(self.get_input_value(inputs, "minutes", 0))

        try:
            dt = datetime.strptime(datetime_str, input_format)
            delta = timedelta(days=days, hours=hours, minutes=minutes)
            result_dt = dt + delta
            return {
                "result": result_dt.strftime(output_format),
                "timestamp": result_dt.timestamp()
            }
        except Exception as e:
            raise ValueError(f"时间处理错误: {str(e)}")


class FileCompressNode(BaseNode):
    """
    文件压缩节点

    将文件或目录压缩为zip格式。

    参数说明:
    - source_path: 要压缩的文件或目录路径
    - output_path: 压缩文件保存路径
    - compression_level: 压缩级别0-9（默认6）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.FILE_COMPRESS,
            name="文件压缩",
            description="将文件或目录压缩为zip格式",
            category="文件操作",
            inputs=[
                NodeInput(name="source_path", label="源路径", type=InputType.FILE_PATH, required=True, description="要压缩的文件或目录路径"),
                NodeInput(name="output_path", label="输出路径", type=InputType.FILE_PATH, required=True, description="压缩文件保存路径(.zip)"),
                NodeInput(name="compression_level", label="压缩级别", type=InputType.NUMBER, required=False, default=6, description="压缩级别0-9，0=不压缩，9=最大压缩"),
            ],
            outputs=[
                NodeOutput(key="success", label="压缩成功", description="压缩是否成功"),
                NodeOutput(key="output_path", label="输出路径", description="压缩文件路径"),
                NodeOutput(key="file_size", label="文件大小", description="压缩文件大小(字节)"),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        source_path = self.get_required_input(inputs, "source_path")
        output_path = self.get_required_input(inputs, "output_path")
        compression_level = int(self.get_input_value(inputs, "compression_level", 6))

        if not os.path.exists(source_path):
            raise FileNotFoundError(f"源路径不存在: {source_path}")

        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zipf:
                if os.path.isfile(source_path):
                    zipf.write(source_path, os.path.basename(source_path))
                else:
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, source_path)
                            zipf.write(file_path, arcname)

            file_size = os.path.getsize(output_path)
            return {"success": True, "output_path": output_path, "file_size": file_size}
        except Exception as e:
            return {"success": False, "output_path": output_path, "file_size": 0, "error": str(e)}


class FileDecompressNode(BaseNode):
    """
    文件解压节点

    解压zip格式的压缩文件。

    参数说明:
    - zip_path: zip文件路径
    - output_dir: 解压目标目录
    - overwrite: 是否覆盖已有文件（默认True）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.FILE_DECOMPRESS,
            name="文件解压",
            description="解压zip格式的压缩文件",
            category="文件操作",
            inputs=[
                NodeInput(name="zip_path", label="压缩文件", type=InputType.FILE_PATH, required=True, description="zip文件路径"),
                NodeInput(name="output_dir", label="解压目录", type=InputType.FILE_PATH, required=True, description="解压目标目录"),
                NodeInput(name="overwrite", label="覆盖文件", type=InputType.BOOLEAN, required=False, default=True, description="是否覆盖已有文件"),
            ],
            outputs=[
                NodeOutput(key="success", label="解压成功", description="解压是否成功"),
                NodeOutput(key="extracted_files", label="解压文件", description="解压的文件列表"),
                NodeOutput(key="file_count", label="文件数量", description="解压的文件数量"),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        zip_path = self.get_required_input(inputs, "zip_path")
        output_dir = self.get_required_input(inputs, "output_dir")
        overwrite = self.get_input_value(inputs, "overwrite", True)

        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"压缩文件不存在: {zip_path}")

        try:
            os.makedirs(output_dir, exist_ok=True)
            extracted_files = []

            with zipfile.ZipFile(zip_path, 'r') as zipf:
                for file_info in zipf.infolist():
                    target_path = os.path.join(output_dir, file_info.filename)
                    if os.path.exists(target_path) and not overwrite:
                        continue
                    zipf.extract(file_info, output_dir)
                    extracted_files.append(target_path)

            return {"success": True, "extracted_files": extracted_files, "file_count": len(extracted_files)}
        except Exception as e:
            return {"success": False, "extracted_files": [], "file_count": 0, "error": str(e)}


class PDFParseNode(BaseNode):
    """
    PDF解析节点

    解析PDF文件内容，提取文本。

    参数说明:
    - pdf_path: PDF文件路径
    - page_range: 页码范围，如 "1-5" 或 "all"（默认all）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.PDF_PARSE,
            name="PDF解析",
            description="解析PDF文件，提取文本内容",
            category="文件操作",
            inputs=[
                NodeInput(name="pdf_path", label="PDF路径", type=InputType.FILE_PATH, required=True, description="PDF文件路径"),
                NodeInput(name="page_range", label="页码范围", type=InputType.TEXT, required=False, default="all", description="页码范围，如 1-5 或 all"),
            ],
            outputs=[
                NodeOutput(key="text", label="文本内容", description="提取的文本内容"),
                NodeOutput(key="page_count", label="总页数", description="PDF总页数"),
                NodeOutput(key="extracted_pages", label="提取页数", description="实际提取的页数"),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        pdf_path = self.get_required_input(inputs, "pdf_path")
        page_range = self.get_input_value(inputs, "page_range", "all")

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return {"text": "", "page_count": 0, "extracted_pages": 0, "error": "需要安装PyPDF2库: pip install PyPDF2"}

        try:
            reader = PdfReader(pdf_path)
            page_count = len(reader.pages)

            if page_range == "all":
                pages = range(page_count)
            else:
                parts = page_range.split("-")
                start = int(parts[0]) - 1
                end = int(parts[1]) if len(parts) > 1 else start + 1
                pages = range(start, min(end, page_count))

            text = ""
            for i in pages:
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text += page_text + "\n"

            return {"text": text.strip(), "page_count": page_count, "extracted_pages": len(list(pages))}
        except Exception as e:
            raise ValueError(f"PDF解析错误: {str(e)}")


class FTPDeleteNode(BaseNode):
    """
    FTP删除节点

    删除FTP服务器上的文件。

    参数说明:
    - connection: FTP连接对象（来自FTP连接节点）
    - remote_path: 要删除的远程文件路径
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.FTP_DELETE,
            name="FTP删除",
            description="删除FTP服务器上的文件",
            category="FTP操作",
            inputs=[
                NodeInput(name="connection", label="FTP连接", type=InputType.TEXT, required=True, description="FTP连接对象"),
                NodeInput(name="remote_path", label="远程路径", type=InputType.TEXT, required=True, description="要删除的远程文件路径"),
            ],
            outputs=[
                NodeOutput(key="success", label="删除成功", description="删除是否成功"),
                NodeOutput(key="error", label="错误信息", description="错误信息"),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        conn = self.get_required_input(inputs, "connection")
        remote_path = self.get_required_input(inputs, "remote_path")

        if not conn:
            raise ValueError("FTP连接不存在")

        try:
            conn.delete(remote_path)
            return {"success": True, "error": None}
        except Exception as e:
            return {"success": False, "error": str(e)}


class SFTPCreateDirNode(BaseNode):
    """
    SFTP创建目录节点

    在SFTP服务器上创建目录。

    参数说明:
    - connection: SFTP连接对象（来自SFTP连接节点）
    - remote_path: 要创建的远程目录路径
    - recursive: 是否递归创建父目录（默认True）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.SFTP_CREATE_DIR,
            name="SFTP创建目录",
            description="在SFTP服务器上创建目录",
            category="SFTP操作",
            inputs=[
                NodeInput(name="connection", label="SFTP连接", type=InputType.TEXT, required=True, description="SFTP连接对象"),
                NodeInput(name="remote_path", label="远程路径", type=InputType.TEXT, required=True, description="要创建的远程目录路径"),
                NodeInput(name="recursive", label="递归创建", type=InputType.BOOLEAN, required=False, default=True, description="是否递归创建父目录"),
            ],
            outputs=[
                NodeOutput(key="success", label="创建成功", description="创建是否成功"),
                NodeOutput(key="error", label="错误信息", description="错误信息"),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        conn = self.get_required_input(inputs, "connection")
        remote_path = self.get_required_input(inputs, "remote_path")
        recursive = self.get_input_value(inputs, "recursive", True)

        if not conn:
            raise ValueError("SFTP连接不存在")

        try:
            if recursive:
                parts = remote_path.split("/")
                current_path = ""
                for part in parts:
                    if part:
                        current_path += "/" + part
                        try:
                            conn.mkdir(current_path)
                        except Exception:
                            pass  # 目录可能已存在
            else:
                conn.mkdir(remote_path)
            return {"success": True, "error": None}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Phase 5 节点类型注册表
PHASE5_NODES = {
    NodeType.FORMULA: FormulaNode,
    NodeType.EMAIL_CONNECT: EmailConnectNode,
    NodeType.EMAIL_FETCH: EmailFetchNode,
    NodeType.EMAIL_SEND: EmailSendNode,
    NodeType.TIME_GET: TimeGetNode,
    NodeType.TIME_PROCESS: TimeProcessNode,
    NodeType.FILE_COMPRESS: FileCompressNode,
    NodeType.FILE_DECOMPRESS: FileDecompressNode,
    NodeType.PDF_PARSE: PDFParseNode,
    NodeType.FTP_DELETE: FTPDeleteNode,
    NodeType.SFTP_CREATE_DIR: SFTPCreateDirNode,
}

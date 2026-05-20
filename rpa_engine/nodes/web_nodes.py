"""
Web操作节点

支持HTTP请求和网页抓取操作
"""

import json
from typing import Any, Dict, Optional

from ..models.schemas import NodeDefinition, NodeInput, NodeOutput, NodeType, InputType
from ..models.context import ExecutionContext
from .base import BaseNode


class HTTPRequestNode(BaseNode):
    """
    HTTP请求节点

    发送HTTP请求，支持GET/POST/PUT/DELETE等方法。

    参数说明:
    - url: 请求URL
    - method: HTTP方法（GET/POST/PUT/DELETE/PATCH）
    - headers: 请求头（JSON格式）
    - body: 请求体（POST/PUT时使用）
    - timeout: 超时时间（秒，默认30）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.HTTP_REQUEST,
            name="HTTP请求",
            description="发送HTTP请求，支持GET/POST/PUT/DELETE等方法",
            category="Web",
            inputs=[
                NodeInput(
                    name="url",
                    label="请求URL",
                    type=InputType.TEXT,
                    required=True,
                    description="请求的URL地址，如: https://api.example.com/data"
                ),
                NodeInput(
                    name="method",
                    label="HTTP方法",
                    type=InputType.DROPDOWN,
                    required=False,
                    default="GET",
                    options=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
                    description="HTTP请求方法"
                ),
                NodeInput(
                    name="headers",
                    label="请求头",
                    type=InputType.CODE,
                    required=False,
                    default="{}",
                    description="请求头（JSON格式），如: {\"Content-Type\": \"application/json\"}"
                ),
                NodeInput(
                    name="body",
                    label="请求体",
                    type=InputType.CODE,
                    required=False,
                    default="",
                    description="请求体内容（POST/PUT时使用），支持JSON格式"
                ),
                NodeInput(
                    name="timeout",
                    label="超时时间(秒)",
                    type=InputType.NUMBER,
                    required=False,
                    default=30,
                    description="请求超时时间（秒）"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="response",
                    label="响应结果",
                    description="HTTP响应结果，包含status_code、headers、body等"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        try:
            import urllib.request
            import urllib.error
            import urllib.parse
        except ImportError:
            raise ImportError("urllib模块不可用")

        url = self.get_required_input(inputs, "url")
        method = self.get_input_value(inputs, "method", "GET").upper()
        headers_str = self.get_input_value(inputs, "headers", "{}")
        body = self.get_input_value(inputs, "body", "")
        timeout = int(self.get_input_value(inputs, "timeout", 30))

        # 解析请求头
        try:
            headers = json.loads(headers_str) if isinstance(headers_str, str) else headers_str
        except json.JSONDecodeError:
            headers = {}

        try:
            # 准备请求体
            data = None
            if body and method in ("POST", "PUT", "PATCH"):
                if isinstance(body, str):
                    data = body.encode("utf-8")
                else:
                    data = json.dumps(body).encode("utf-8")
                if "Content-Type" not in headers:
                    headers["Content-Type"] = "application/json"

            # 创建请求
            req = urllib.request.Request(url, data=data, headers=headers, method=method)

            # 发送请求
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_body = response.read().decode("utf-8")
                response_headers = dict(response.headers)
                status_code = response.status

            # 尝试解析JSON响应
            try:
                response_json = json.loads(response_body)
            except (json.JSONDecodeError, ValueError):
                response_json = None

            return {
                "response": {
                    "success": True,
                    "status_code": status_code,
                    "headers": response_headers,
                    "body": response_body,
                    "json": response_json,
                    "url": url,
                    "method": method
                }
            }
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            return {
                "response": {
                    "success": False,
                    "status_code": e.code,
                    "error": str(e.reason),
                    "body": error_body,
                    "url": url,
                    "method": method
                }
            }
        except Exception as e:
            return {
                "response": {
                    "success": False,
                    "error": str(e),
                    "url": url,
                    "method": method
                }
            }


class WebScrapeNode(BaseNode):
    """
    网页抓取节点

    抓取网页内容，提取文本或特定元素。

    参数说明:
    - url: 网页URL
    - selector: CSS选择器（可选，不指定则获取整个页面文本）
    - extract: 提取方式（text/html/attr）
    - attr_name: 属性名称（extract为attr时使用）
    """

    def _create_definition(self) -> NodeDefinition:
        return NodeDefinition(
            type=NodeType.WEB_SCRAPE,
            name="网页抓取",
            description="抓取网页内容，提取文本或HTML",
            category="Web",
            inputs=[
                NodeInput(
                    name="url",
                    label="网页URL",
                    type=InputType.TEXT,
                    required=True,
                    description="要抓取的网页URL"
                ),
                NodeInput(
                    name="extract",
                    label="提取方式",
                    type=InputType.DROPDOWN,
                    required=False,
                    default="text",
                    options=["text", "html"],
                    description="提取方式：text=纯文本，html=HTML内容"
                ),
                NodeInput(
                    name="encoding",
                    label="编码",
                    type=InputType.TEXT,
                    required=False,
                    default="auto",
                    description="网页编码，auto=自动检测，或指定如utf-8, gbk等"
                ),
                NodeInput(
                    name="timeout",
                    label="超时时间(秒)",
                    type=InputType.NUMBER,
                    required=False,
                    default=30,
                    description="请求超时时间（秒）"
                ),
            ],
            outputs=[
                NodeOutput(
                    key="scrape_result",
                    label="抓取结果",
                    description="网页抓取结果，包含content(内容)、title(标题)等"
                ),
            ]
        )

    def execute(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        import urllib.request
        import urllib.error
        import re

        url = self.get_required_input(inputs, "url")
        extract = self.get_input_value(inputs, "extract", "text")
        encoding = self.get_input_value(inputs, "encoding", "auto")
        timeout = int(self.get_input_value(inputs, "timeout", 30))

        try:
            # 设置请求头模拟浏览器
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=timeout) as response:
                # 检测编码
                if encoding == "auto":
                    content_type = response.headers.get("Content-Type", "")
                    charset_match = re.search(r'charset=([^\s;]+)', content_type, re.IGNORECASE)
                    if charset_match:
                        encoding = charset_match.group(1)
                    else:
                        encoding = "utf-8"

                html_content = response.read().decode(encoding, errors="replace")

            # 提取标题
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.DOTALL | re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else ""

            if extract == "text":
                # 简单的HTML转文本
                # 移除script和style标签
                text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                # 移除HTML标签
                text = re.sub(r'<[^>]+>', ' ', text)
                # 清理空白
                text = re.sub(r'\s+', ' ', text).strip()
                content = text
            else:
                content = html_content

            return {
                "scrape_result": {
                    "success": True,
                    "content": content,
                    "title": title,
                    "url": url,
                    "content_length": len(content)
                }
            }
        except Exception as e:
            return {
                "scrape_result": {
                    "success": False,
                    "error": str(e),
                    "url": url
                }
            }

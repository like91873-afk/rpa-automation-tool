#!/usr/bin/env python3
"""
RPA自动化工具 - 主入口

使用方法:
    # 启动API服务器
    python -m rpa_engine serve --host 0.0.0.0 --port 8000

    # 执行流程文件
    python -m rpa_engine run flow.json --variables '{"key": "value"}'

    # 创建示例流程
    python -m rpa_engine sample --output sample.json
"""

import argparse
import json
import sys

from .engine import ExecutionEngine
from .utils import create_sample_flow, load_flow_from_file, save_flow_to_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="RPA自动化工具",
        prog="rpa_engine"
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # serve命令 - 启动API服务器
    serve_parser = subparsers.add_parser("serve", help="启动API服务器")
    serve_parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    serve_parser.add_argument("--port", type=int, default=8000, help="监听端口")

    # run命令 - 执行流程
    run_parser = subparsers.add_parser("run", help="执行流程文件")
    run_parser.add_argument("flow_file", help="流程文件路径")
    run_parser.add_argument("--variables", help="初始变量（JSON格式）")
    run_parser.add_argument("--timeout", type=int, default=3600, help="超时时间（秒）")
    run_parser.add_argument("--debug", action="store_true", help="调试模式")

    # sample命令 - 创建示例流程
    sample_parser = subparsers.add_parser("sample", help="创建示例流程")
    sample_parser.add_argument("--output", default="sample.json", help="输出文件路径")

    # validate命令 - 验证流程
    validate_parser = subparsers.add_parser("validate", help="验证流程文件")
    validate_parser.add_argument("flow_file", help="流程文件路径")

    args = parser.parse_args()

    if args.command == "serve":
        # 启动API服务器
        from .api import start_server
        print(f"启动RPA API服务器: http://{args.host}:{args.port}")
        start_server(host=args.host, port=args.port)

    elif args.command == "run":
        # 执行流程
        try:
            flow = load_flow_from_file(args.flow_file)

            # 解析变量
            initial_variables = {}
            if args.variables:
                initial_variables = json.loads(args.variables)

            # 执行流程
            engine = ExecutionEngine()
            result = engine.execute_flow(
                flow=flow,
                initial_variables=initial_variables,
                timeout=args.timeout,
                debug=args.debug
            )

            # 输出结果
            print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2, default=str))

            # 返回退出码
            sys.exit(0 if result.status == "completed" else 1)

        except Exception as e:
            print(f"执行失败: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "sample":
        # 创建示例流程
        flow = create_sample_flow()
        save_flow_to_file(flow, args.output)
        print(f"示例流程已保存到: {args.output}")

    elif args.command == "validate":
        # 验证流程
        from .utils import validate_flow
        try:
            flow = load_flow_from_file(args.flow_file)
            errors = validate_flow(flow)

            if errors:
                print("验证失败:")
                for error in errors:
                    print(f"  - {error}")
                sys.exit(1)
            else:
                print("验证通过")
                print(f"  - 流程名称: {flow.name}")
                print(f"  - 节点数量: {len(flow.nodes)}")
                print(f"  - 连接数量: {len(flow.connections)}")

        except Exception as e:
            print(f"验证失败: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

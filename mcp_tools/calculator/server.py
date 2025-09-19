"""
Calculator MCP Server

Model Context Protocol準拠の計算サーバー
stdio通信でADKエージェントと連携
"""

import sys
import json
import asyncio
from typing import Dict, Any, List
from .calculator import SafeCalculator


class CalculatorMCPServer:
    """Calculator MCP Server Implementation"""

    def __init__(self):
        self.calculator = SafeCalculator()
        self.server_info = {
            "name": "calculator",
            "version": "1.0.0",
            "description": "数学計算を安全に実行するMCPサーバー",
            "author": "Maidel 2.2 Project"
        }

    def get_server_info(self) -> Dict[str, Any]:
        """サーバー情報を取得"""
        return self.server_info

    def list_tools(self) -> Dict[str, Any]:
        """利用可能なツール一覧を返す"""
        return {
            "tools": [
                {
                    "name": "calculate",
                    "description": "数学的な計算式を評価し、結果を返す",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "計算する数式 (例: '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)')"
                            }
                        },
                        "required": ["expression"]
                    }
                },
                {
                    "name": "validate_expression",
                    "description": "数式の妥当性を事前チェック",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "検証する数式"
                            }
                        },
                        "required": ["expression"]
                    }
                },
                {
                    "name": "get_supported_functions",
                    "description": "サポートされている数学関数の一覧を取得",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """ツール実行"""
        try:
            if name == "calculate":
                expression = arguments.get("expression", "")
                result = self.calculator.calculate(expression)
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2)
                    }],
                    "isError": not result.get("success", False)
                }

            elif name == "validate_expression":
                expression = arguments.get("expression", "")
                result = self.calculator.validate_expression(expression)
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2)
                    }],
                    "isError": not result.get("valid", False)
                }

            elif name == "get_supported_functions":
                functions = list(self.calculator.functions.keys())
                result = {
                    "success": True,
                    "supported_functions": functions,
                    "total_count": len(functions)
                }
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2)
                    }],
                    "isError": False
                }

            else:
                error_result = {
                    "success": False,
                    "error": f"未知のツール: {name}",
                    "error_type": "unknown_tool"
                }
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(error_result, ensure_ascii=False, indent=2)
                    }],
                    "isError": True
                }

        except Exception as e:
            error_result = {
                "success": False,
                "error": f"ツール実行エラー: {str(e)}",
                "error_type": "tool_execution_error"
            }
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(error_result, ensure_ascii=False, indent=2)
                }],
                "isError": True
            }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """リクエスト処理"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            if method == "initialize":
                response = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": self.server_info
                }
            elif method == "tools/list":
                response = self.list_tools()
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                response = self.call_tool(tool_name, arguments)
            else:
                response = {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

            # レスポンスにIDを追加
            if request_id is not None:
                response["id"] = request_id

            return response

        except Exception as e:
            error_response = {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            if request.get("id") is not None:
                error_response["id"] = request["id"]
            return error_response

    async def run_stdio_server(self):
        """stdio通信でのサーバー実行"""
        print(f"Calculator MCP Server starting...", file=sys.stderr)
        print(f"Server info: {self.server_info}", file=sys.stderr)

        try:
            while True:
                try:
                    # 標準入力から1行読み取り
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, sys.stdin.readline
                    )

                    if not line:  # EOF
                        break

                    line = line.strip()
                    if not line:
                        continue

                    # JSON解析
                    try:
                        request = json.loads(line)
                    except json.JSONDecodeError as e:
                        error_response = {
                            "error": {
                                "code": -32700,
                                "message": f"Parse error: {str(e)}"
                            }
                        }
                        print(json.dumps(error_response, ensure_ascii=False), flush=True)
                        continue

                    # リクエスト処理
                    response = await self.handle_request(request)

                    # レスポンス送信
                    print(json.dumps(response, ensure_ascii=False), flush=True)

                except KeyboardInterrupt:
                    print("Server shutting down...", file=sys.stderr)
                    break
                except Exception as e:
                    print(f"Error processing request: {e}", file=sys.stderr)
                    error_response = {
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response, ensure_ascii=False), flush=True)

        except Exception as e:
            print(f"Fatal server error: {e}", file=sys.stderr)
            sys.exit(1)


async def main():
    """メイン実行関数"""
    server = CalculatorMCPServer()
    await server.run_stdio_server()


if __name__ == "__main__":
    asyncio.run(main())
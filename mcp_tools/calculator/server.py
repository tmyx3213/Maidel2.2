"""
Calculator MCP Server (JSON-RPC over stdio with Content-Length framing)
"""

import sys
import json
import asyncio
from typing import Dict, Any
from .calculator import SafeCalculator


def _read_message() -> Dict[str, Any]:
    content_length = None
    saw_any_header = False
    # Read headers (or detect JSON line fallback)
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return {}
        # Detect JSON line mode (no headers)
        stripped = line.strip()
        if stripped.startswith(b"{") or stripped.startswith(b"["):
            try:
                return json.loads(stripped.decode("utf-8"))
            except Exception:
                return {}
        # Header mode
        saw_any_header = True
        if line in (b"\r\n", b"\n"):
            break
        try:
            header = line.decode("utf-8").strip()
        except Exception:
            header = ""
        if header.lower().startswith("content-length:"):
            try:
                content_length = int(header.split(":", 1)[1].strip())
            except Exception:
                content_length = None
    if content_length is None:
        return {}
    body = sys.stdin.buffer.read(content_length)
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return {}


def _write_message(payload: Dict[str, Any]) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    # Some MCP clients require only Content-Length header
    headers = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(headers)
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


class CalculatorMCPServer:
    def __init__(self) -> None:
        self.calculator = SafeCalculator()
        self.server_info = {
            "name": "calculator",
            "version": "1.0.0",
            "description": "安全な数学計算を提供する MCP サーバー",
            "author": "Maidel 2.2 Project",
        }

    def list_tools(self) -> Dict[str, Any]:
        return {
            "tools": [
                {
                    "name": "calculate",
                    "description": "数式を評価して結果を返します",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "計算する数式 (例: '2 + 3 * 4')",
                            }
                        },
                        "required": ["expression"],
                    },
                },
                {
                    "name": "get_supported_functions",
                    "description": "サポート関数一覧を返します",
                    "inputSchema": {"type": "object", "properties": {}},
                },
            ]
        }

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "calculate":
                expression = arguments.get("expression", "")
                result = self.calculator.calculate(expression)
                return {
                    "content": [
                        {"type": "text", "text": json.dumps(result, ensure_ascii=False)}
                    ],
                    "isError": not result.get("success", False),
                }
            elif name == "get_supported_functions":
                functions = list(self.calculator.functions.keys())
                result = {
                    "success": True,
                    "supported_functions": functions,
                    "total_count": len(functions),
                }
                return {
                    "content": [
                        {"type": "text", "text": json.dumps(result, ensure_ascii=False)}
                    ],
                    "isError": False,
                }
            else:
                err = {
                    "success": False,
                    "error": f"unknown tool: {name}",
                    "error_type": "unknown_tool",
                }
                return {"content": [{"type": "text", "text": json.dumps(err)}], "isError": True}
        except Exception as e:
            err = {"success": False, "error": f"tool_execution_error: {e}"}
            return {"content": [{"type": "text", "text": json.dumps(err)}], "isError": True}

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        try:
            method = request.get("method")
            params = request.get("params", {})
            req_id = request.get("id")
            # minimal debug
            print(f"[MCP] recv method={method}", file=sys.stderr)

            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {},
                        "prompts": {},
                    },
                    "serverInfo": self.server_info,
                }
            elif method == "tools/list":
                result = self.list_tools()
            elif method == "tools/call":
                result = self.call_tool(params.get("name"), params.get("arguments", {}))
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }

            resp = {"jsonrpc": "2.0", "id": req_id, "result": result}
            print(f"[MCP] send ok for {method}", file=sys.stderr)
            return resp
        except Exception as e:
            err = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": f"Internal error: {e}"},
            }
            print(f"[MCP] send error for {request.get('method')}: {e}", file=sys.stderr)
            return err

    async def run_stdio_server(self) -> None:
        print("Calculator MCP Server starting...", file=sys.stderr)
        print(f"Server info: {self.server_info}", file=sys.stderr)
        loop = asyncio.get_event_loop()
        try:
            while True:
                req = await loop.run_in_executor(None, _read_message)
                if not req:
                    break
                print("[MCP] request received", file=sys.stderr)
                resp = await self.handle_request(req)
                await loop.run_in_executor(None, _write_message, resp)
        except KeyboardInterrupt:
            print("Server shutting down...", file=sys.stderr)
        except Exception as e:
            print(f"Fatal server error: {e}", file=sys.stderr)
            sys.exit(1)


async def main():
    server = CalculatorMCPServer()
    await server.run_stdio_server()


if __name__ == "__main__":
    asyncio.run(main())

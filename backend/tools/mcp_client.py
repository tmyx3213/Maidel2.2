import sys
import json
import subprocess
import threading
from typing import Any, Dict, Optional


class SimpleMCPClient:
    """Minimal JSON-RPC client for the calculator MCP server over stdio."""

    def __init__(self, command: Optional[str] = None) -> None:
        self.command = command or f"{sys.executable} -m mcp_tools.calculator"
        self.process: Optional[subprocess.Popen] = None
        self.lock = threading.Lock()

    def start(self) -> None:
        if self.process is not None and self.process.poll() is None:
            return
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        # initialize
        _ = self.request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})

    def stop(self) -> None:
        if self.process is not None:
            try:
                self.process.terminate()
            except Exception:
                pass
            self.process = None

    def request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("MCP server not started")
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = f"Content-Type: application/json\r\nContent-Length: {len(data)}\r\n\r\n".encode("ascii")
        with self.lock:
            self.process.stdin.buffer.write(headers)
            self.process.stdin.buffer.write(data)
            self.process.stdin.buffer.flush()
            # Read headers
            content_length = None
            while True:
                line = self.process.stdout.buffer.readline()
                if not line:
                    return {"error": "eof"}
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
                return {"error": "missing_content_length"}
            body = self.process.stdout.buffer.read(content_length)
        try:
            return json.loads(body.decode("utf-8"))
        except Exception as e:
            return {"error": f"invalid_response: {e}", "raw": body.decode('utf-8', 'ignore')}

    def calculate(self, expression: str) -> Dict[str, Any]:
        if not self.process:
            self.start()
        req = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {"name": "calculate", "arguments": {"expression": expression}},
        }
        resp = self.request(req)
        # Unwrap content
        try:
            result = resp.get("result", resp)
            content = (result.get("content") or [{}])[0].get("text", "{}")
            return json.loads(content)
        except Exception:
            return {"success": False, "error": "mcp_invalid_content", "raw": resp}

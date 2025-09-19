"""
Simple Calculator MCP Server Test
Unicode文字を使わないシンプルなテスト
"""

import subprocess
import json
import time
import sys


def test_calculator():
    """Calculator MCP サーバーのシンプルテスト"""
    print("Starting Calculator MCP Server Test...")

    try:
        # サーバー起動
        process = subprocess.Popen(
            [sys.executable, "-m", "mcp_tools.calculator"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        print("OK: Server started")
        time.sleep(1)

        # 初期化テスト
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }

        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json)
        process.stdin.flush()

        response_line = process.stdout.readline()
        response = json.loads(response_line.strip())

        if "error" not in response:
            print("OK: Server initialization successful")
        else:
            print(f"ERROR: Initialization failed: {response['error']}")
            return False

        # 計算テスト
        calc_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "calculate",
                "arguments": {
                    "expression": "2 + 3"
                }
            }
        }

        request_json = json.dumps(calc_request) + "\n"
        process.stdin.write(request_json)
        process.stdin.flush()

        response_line = process.stdout.readline()
        response = json.loads(response_line.strip())

        if "content" in response:
            content = response["content"][0]["text"]
            result_data = json.loads(content)
            if result_data.get("success") and result_data.get("result") == 5:
                print("OK: Calculation test passed (2 + 3 = 5)")
            else:
                print(f"ERROR: Calculation failed: {result_data}")
                return False
        else:
            print(f"ERROR: No content in response: {response}")
            return False

        # クリーンアップ
        process.terminate()
        process.wait(timeout=5)
        print("OK: Server terminated")
        print("ALL TESTS PASSED!")
        return True

    except Exception as e:
        print(f"ERROR: Test failed: {e}")
        if 'process' in locals():
            process.terminate()
        return False


if __name__ == "__main__":
    success = test_calculator()
    sys.exit(0 if success else 1)
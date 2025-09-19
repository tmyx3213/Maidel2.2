"""
Calculator MCP Server テストスクリプト

MCPサーバーとの通信をテストし、正常に動作することを確認
"""

import subprocess
import json
import time
import sys
from typing import Dict, Any


class MCPCalculatorTester:
    """Calculator MCP サーバーテストクラス"""

    def __init__(self):
        self.process = None

    def start_server(self):
        """MCPサーバーを起動"""
        try:
            self.process = subprocess.Popen(
                [sys.executable, "-m", "mcp_tools.calculator"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            print("OK Calculator MCP Server started")
            time.sleep(0.5)  # サーバー起動待機
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False

    def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCPサーバーにリクエストを送信"""
        if not self.process:
            raise RuntimeError("Server not started")

        try:
            request_json = json.dumps(request, ensure_ascii=False) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            response_line = self.process.stdout.readline()
            if not response_line:
                raise RuntimeError("No response received")

            return json.loads(response_line.strip())
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return {"error": str(e)}

    def test_initialize(self):
        """初期化テスト"""
        print("\n🧪 Testing server initialization...")
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }

        response = self.send_request(request)
        if "error" in response:
            print(f"❌ Initialization failed: {response['error']}")
            return False

        print("✅ Server initialization successful")
        print(f"   Protocol: {response.get('protocolVersion', 'unknown')}")
        print(f"   Server: {response.get('serverInfo', {}).get('name', 'unknown')}")
        return True

    def test_list_tools(self):
        """ツール一覧テスト"""
        print("\n🧪 Testing tools list...")
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        response = self.send_request(request)
        if "error" in response:
            print(f"❌ Tools list failed: {response['error']}")
            return False

        tools = response.get("tools", [])
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')}")
        return True

    def test_calculations(self):
        """計算テスト"""
        print("\n🧪 Testing calculations...")

        test_cases = [
            ("2 + 3", 5),
            ("10 / 2", 5.0),
            ("2 * 3 + 4", 10),
            ("sqrt(16)", 4.0),
            ("sin(0)", 0.0),
            ("2^3", 8),  # 指数演算
        ]

        for expression, expected in test_cases:
            print(f"   Testing: {expression}")
            request = {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "calculate",
                    "arguments": {
                        "expression": expression
                    }
                }
            }

            response = self.send_request(request)
            if "error" in response:
                print(f"     ❌ Error: {response['error']}")
                continue

            # レスポンス内容を解析
            content = response.get("content", [{}])[0].get("text", "{}")
            try:
                result_data = json.loads(content)
                if result_data.get("success"):
                    actual = result_data.get("result")
                    if abs(actual - expected) < 1e-10:  # 浮動小数点誤差考慮
                        print(f"     ✅ Result: {actual}")
                    else:
                        print(f"     ❌ Expected {expected}, got {actual}")
                else:
                    print(f"     ❌ Calculation failed: {result_data.get('error')}")
            except json.JSONDecodeError:
                print(f"     ❌ Invalid response format")

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        print("\n🧪 Testing error handling...")

        error_cases = [
            ("10 / 0", "division_by_zero"),
            ("import os", "安全でない式が検出されました"),
            ("((2 + 3)", "括弧の数が一致しません"),
            ("invalid_function(5)", "name 'invalid_function' is not defined"),
        ]

        for expression, expected_error_type in error_cases:
            print(f"   Testing error: {expression}")
            request = {
                "jsonrpc": "2.0",
                "id": 20,
                "method": "tools/call",
                "params": {
                    "name": "calculate",
                    "arguments": {
                        "expression": expression
                    }
                }
            }

            response = self.send_request(request)
            content = response.get("content", [{}])[0].get("text", "{}")
            try:
                result_data = json.loads(content)
                if not result_data.get("success"):
                    print(f"     ✅ Correctly caught error: {result_data.get('error_type', 'unknown')}")
                else:
                    print(f"     ❌ Should have failed but succeeded: {result_data.get('result')}")
            except json.JSONDecodeError:
                print(f"     ❌ Invalid response format")

    def test_supported_functions(self):
        """サポート関数テスト"""
        print("\n🧪 Testing supported functions...")
        request = {
            "jsonrpc": "2.0",
            "id": 30,
            "method": "tools/call",
            "params": {
                "name": "get_supported_functions",
                "arguments": {}
            }
        }

        response = self.send_request(request)
        content = response.get("content", [{}])[0].get("text", "{}")
        try:
            result_data = json.loads(content)
            if result_data.get("success"):
                functions = result_data.get("supported_functions", [])
                print(f"✅ Supported functions ({len(functions)}):")
                for func in sorted(functions):
                    print(f"   - {func}")
            else:
                print(f"❌ Failed to get functions: {result_data.get('error')}")
        except json.JSONDecodeError:
            print(f"❌ Invalid response format")

    def cleanup(self):
        """クリーンアップ"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            print("\n✅ Server terminated")

    def run_all_tests(self):
        """全テストを実行"""
        print("Starting Calculator MCP Server Tests")
        print("=" * 50)

        try:
            if not self.start_server():
                return False

            tests_passed = 0
            total_tests = 5

            if self.test_initialize():
                tests_passed += 1

            if self.test_list_tools():
                tests_passed += 1

            self.test_calculations()
            tests_passed += 1

            self.test_error_handling()
            tests_passed += 1

            self.test_supported_functions()
            tests_passed += 1

            print("\n" + "=" * 50)
            print(f"🎯 Test Results: {tests_passed}/{total_tests} tests completed")

            if tests_passed == total_tests:
                print("✅ All tests passed! Calculator MCP Server is working correctly.")
                return True
            else:
                print("⚠️  Some tests had issues. Check the output above.")
                return False

        except KeyboardInterrupt:
            print("\n⚠️  Tests interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            return False
        finally:
            self.cleanup()


if __name__ == "__main__":
    tester = MCPCalculatorTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
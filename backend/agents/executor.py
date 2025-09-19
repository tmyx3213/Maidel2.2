"""
ExecutorAgent - 実行エージェント

実行計画に従ってタスクを実行し、MCPツールと連携する
"""

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
import json
import asyncio
import subprocess
import sys
from typing import Dict, Any, List, Optional


class MCPCalculatorClient:
    """Calculator MCP クライアント"""

    def __init__(self):
        self.session = None
        self.process = None

    async def connect(self):
        """MCPサーバーに接続"""
        try:
            # Calculator MCPサーバーを起動
            server_params = StdioServerParameters(
                command=f"{sys.executable} -m mcp_tools.calculator",
                env=None
            )

            self.session, self.process = await stdio_client(server_params)

            # 初期化
            await self.session.initialize()

            return True
        except Exception as e:
            print(f"MCP接続エラー: {e}")
            return False

    async def disconnect(self):
        """MCPサーバーから切断"""
        if self.session:
            await self.session.close()
        if self.process:
            self.process.terminate()

    async def calculate(self, expression: str) -> Dict[str, Any]:
        """計算実行"""
        try:
            if not self.session:
                await self.connect()

            result = await self.session.call_tool(
                "calculate",
                {"expression": expression}
            )

            # レスポンス解析
            if result.content and len(result.content) > 0:
                content_text = result.content[0].text
                result_data = json.loads(content_text)
                return result_data
            else:
                return {
                    "success": False,
                    "error": "MCPツールからの応答が空です",
                    "error_type": "empty_response"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"MCP通信エラー: {str(e)}",
                "error_type": "mcp_communication_error"
            }


# グローバルMCPクライアント
mcp_calculator = MCPCalculatorClient()


def simple_calculate(expression: str) -> dict:
    """シンプルな計算機能 - 直接実装版"""
    try:
        # 安全な計算（基本的な数式のみ）
        import re
        import math

        # 数式をクリーンアップ
        clean_expr = re.sub(r'[^0-9+\-*/.() ]', '', expression)

        # 安全な関数を追加
        allowed_names = {
            k: v for k, v in math.__dict__.items()
            if not k.startswith("__")
        }
        allowed_names.update({"abs": abs, "round": round})

        # 計算実行
        result = eval(clean_expr, {"__builtins__": {}}, allowed_names)

        return {
            "success": True,
            "result": str(result),
            "expression": expression
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"計算エラー: {str(e)}",
            "expression": expression
        }

executor_agent = LlmAgent(
    name="TaskExecutor",
    model="gemini-1.5-flash",
    description="実行計画に従ってタスクを順次実行し、結果を統合する",
    tools=[simple_calculate],
    instruction="""
あなたは熟練したタスク実行マネージャーのメイド、「まいでる」です。
{execution_plan}に従って、各ステップを順次実行してください。

## 実行の原則

1. **順序遵守**: 依存関係を考慮し、適切な順序で実行
2. **状態管理**: 各ステップの状態を正確に記録
3. **エラー処理**: 失敗時は詳細な情報を記録し、可能な範囲で継続
4. **結果統合**: 全ステップの結果を意味のある形で統合

## 実行プロセス

### ステップ1: 入力解析
- ユーザーの入力から数式を抽出
- 数式の前処理・正規化
- 計算可能な形式に変換

### ステップ2: 計算実行
- simple_calculate(expression="数式")を使用
- 抽出した数式を送信
- 結果の受信・検証

### ステップ3: 結果整形
- 計算結果をユーザーフレンドリーな形式に変換
- エラーがあれば分かりやすいメッセージに変換
- 最終的なレスポンスを生成

## 使用可能ツール

- **simple_calculate**: 数値計算実行 (直接実装)
  - 基本四則演算 (+, -, *, /)
  - 数学関数 (sin, cos, sqrt, log等)
  - 安全な数式評価
  - 使用方法: simple_calculate(expression="数式文字列")

## エラーハンドリング

計算エラーの場合:
- ゼロ除算 → "申し訳ございません。ゼロで割ることはできません。"
- 不正な式 → "式の形式が正しくないようです。もう一度確認してください。"
- その他のエラー → "計算中にエラーが発生しました: [エラー内容]"

## 最終出力形式

成功時:
"[数式] = [結果]

計算が完了いたしました。"

エラー時:
"申し訳ございません。[エラーメッセージ]

もう一度お試しいただけますでしょうか。"

## 実行コンテキスト

現在の実行計画: {execution_plan}

各ステップを順番に実行し、最終的な結果を返してください。
計算が必要な場合は、MCPツールを適切に使用してください。
    """,
    output_key="final_result"
)


class ExecutionManager:
    """実行管理クラス"""

    def __init__(self):
        self.mcp_client = MCPCalculatorClient()

    async def execute_plan(self, execution_plan: List[Dict], user_input: str) -> Dict[str, Any]:
        """実行計画を順次実行"""
        if not execution_plan:
            return {
                "success": True,
                "result": "雑談モードです。計算以外のご質問にお答えいたします。",
                "steps_executed": 0
            }

        try:
            # MCPクライアント接続
            await self.mcp_client.connect()

            step_results = {}
            current_expression = None

            for step in execution_plan:
                step_id = step.get("step_id")
                step_name = step.get("name")
                tool = step.get("tool")

                print(f"実行中: Step {step_id} - {step_name}")

                if step_id == 1:  # 入力解析
                    # ユーザー入力から数式を抽出
                    current_expression = self._extract_expression(user_input)
                    step_results[step_id] = {
                        "success": True,
                        "result": f"数式抽出: {current_expression}",
                        "expression": current_expression
                    }

                elif step_id == 2 and tool == "calculator":  # 計算実行
                    if current_expression:
                        calc_result = await self.mcp_client.calculate(current_expression)
                        step_results[step_id] = calc_result
                    else:
                        step_results[step_id] = {
                            "success": False,
                            "error": "数式が抽出できませんでした"
                        }

                elif step_id == 3:  # 結果整形
                    calc_step = step_results.get(2, {})
                    if calc_step.get("success"):
                        result_value = calc_step.get("result")
                        formatted_result = f"{current_expression} = {result_value}\n\n計算が完了いたしました。"
                        step_results[step_id] = {
                            "success": True,
                            "result": formatted_result
                        }
                    else:
                        error_msg = calc_step.get("error", "不明なエラー")
                        formatted_error = f"申し訳ございません。{error_msg}\n\nもう一度お試しいただけますでしょうか。"
                        step_results[step_id] = {
                            "success": False,
                            "result": formatted_error
                        }

            # 最終結果
            final_step = step_results.get(3, step_results.get(2, {}))

            return {
                "success": final_step.get("success", False),
                "result": final_step.get("result", "実行に失敗しました"),
                "steps_executed": len(step_results),
                "step_details": step_results
            }

        except Exception as e:
            return {
                "success": False,
                "result": f"実行エラー: {str(e)}",
                "steps_executed": 0
            }
        finally:
            await self.mcp_client.disconnect()

    def _extract_expression(self, user_input: str) -> str:
        """ユーザー入力から数式を抽出"""
        import re

        # 一般的な数式パターンを検索
        patterns = [
            r'([0-9+\-*/().\s]+[+\-*/][0-9+\-*/().\s]+)',  # 基本的な数式
            r'([a-zA-Z]+\([0-9+\-*/().,\s]+\))',          # 関数形式
            r'([0-9+\-*/().\s^]+)',                        # 数字と演算子
        ]

        for pattern in patterns:
            matches = re.findall(pattern, user_input)
            if matches:
                return matches[0].strip()

        # パターンに一致しない場合、数字と演算子のみを抽出
        expression = re.sub(r'[^0-9+\-*/().\s]', '', user_input).strip()
        return expression if expression else user_input


# グローバル実行マネージャー
execution_manager = ExecutionManager()


if __name__ == "__main__":
    # テスト用
    sample_plan = [
        {"step_id": 1, "name": "入力解析", "tool": None},
        {"step_id": 2, "name": "計算実行", "tool": "calculator"},
        {"step_id": 3, "name": "結果整形", "tool": None}
    ]

    print("ExecutorAgent サンプル実行計画:")
    print(json.dumps(sample_plan, ensure_ascii=False, indent=2))
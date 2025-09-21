"""
Executor: Deterministic task execution without MCP dependency.

Provides:
- simple_calculate: safe local math evaluator
- executor_agent: LLM agent exposing simple_calculate as a tool
- execution_manager: runs a 3-step plan (parse -> calculate -> format)
"""

from typing import Dict, Any, List
import os
from backend.tools.mcp_client import SimpleMCPClient
import sys

# Prefer official ADK MCPToolset if available
try:
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from mcp import StdioServerParameters
    _HAVE_ADK_MCP = True
except Exception:
    _HAVE_ADK_MCP = False
from google.adk.agents import LlmAgent


def simple_calculate(expression: str) -> dict:
    try:
        import re
        import math
        # sanitize
        clean_expr = re.sub(r"[^0-9+\-*/.() ]", "", expression)
        # safe env
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        allowed_names.update({"abs": abs, "round": round})
        result = eval(clean_expr, {"__builtins__": {}}, allowed_names)
        return {"success": True, "result": str(result), "expression": expression}
    except Exception as e:
        return {"success": False, "error": f"計算エラー: {e}", "expression": expression}


def mcp_calculate(expression: str) -> dict:
    try:
        client = SimpleMCPClient()
        result = client.calculate(expression)
        return result
    except Exception as e:
        return {"success": False, "error": f"MCP計算エラー: {e}"}


USE_ADK_MCP_TOOLSET = os.getenv("USE_ADK_MCP_TOOLSET", "false").lower() in ("1", "true", "yes")

executor_agent = LlmAgent(
    name="TaskExecutor",
    model="gemini-1.5-flash",
    description="Execute steps and integrate results",
    tools=([
        # Expose MCP toolset directly to the agent (discover remote tools like "calculate")
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=["-m", "mcp_tools.calculator"],
                    env={
                        "PYTHONIOENCODING": "utf-8",
                        # Ensure module resolution regardless of current working dir
                        "PYTHONPATH": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
                    }
                )
            )
        )
    ] if (_HAVE_ADK_MCP and USE_ADK_MCP_TOOLSET) else []) + [
        # Also expose explicit functions for robustness and local fallback
        mcp_calculate,
        simple_calculate,
    ],
    instruction="""
与えられた execution_plan を順に実行し、必要に応じてツールを使って結果を取りまとめてください。

ツールの使い方（厳守）:
- 関数名: mcp_calculate または simple_calculate
- 引数: {"expression": "<数式文字列>"} 以外は渡さない
- 例: mcp_calculate(expression="2+3")
出力は最終的に「[数式] = [結果]」の形式でまとめてください。
""",
    output_key="final_result",
)


class ExecutionManager:
    def __init__(self) -> None:
        pass

    async def execute_plan(self, execution_plan: List[Dict[str, Any]], user_input: str) -> Dict[str, Any]:
        if not execution_plan:
            return {"success": True, "result": "", "steps_executed": 0}

        step_results: Dict[int, Dict[str, Any]] = {}
        current_expression = None

        use_mcp = os.getenv("USE_MCP", "true").lower() in ("1", "true", "yes")

        for step in execution_plan:
            step_id = step.get("step_id")
            tool = step.get("tool")

            if step_id == 1:
                current_expression = self._extract_expression(user_input)
                step_results[step_id] = {"success": True, "expression": current_expression}

            elif step_id == 2 and tool == "calculator":
                if current_expression:
                    calc_result = mcp_calculate(current_expression) if use_mcp else simple_calculate(current_expression)
                    step_results[step_id] = calc_result
                else:
                    step_results[step_id] = {"success": False, "error": "数式が抽出できませんでした"}

            elif step_id == 3:
                calc_step = step_results.get(2, {})
                if calc_step.get("success"):
                    result_value = calc_step.get("result")
                    formatted = f"{current_expression} = {result_value}\n\n計算が完了しました"
                    step_results[step_id] = {"success": True, "result": formatted}
                else:
                    error_msg = calc_step.get("error", "不明なエラー")
                    formatted = f"申し訳ございません、{error_msg}\n\nもう一度お試しください"
                    step_results[step_id] = {"success": False, "result": formatted}

        final_step = step_results.get(3, step_results.get(2, {}))
        return {
            "success": bool(final_step.get("success")),
            "result": final_step.get("result", "実行に失敗しました"),
            "steps_executed": len(step_results),
            "step_details": step_results,
        }

    def _extract_expression(self, user_input: str) -> str:
        import re

        # 日本語での数学表現を英語記号に変換
        converted = user_input
        converted = re.sub(r"足し|足す|加え|プラス|たす", "+", converted)
        converted = re.sub(r"引き|引く|減らし|マイナス|ひく", "-", converted)
        converted = re.sub(r"掛け|掛ける|乗じ|乗ずる|かける", "*", converted)
        converted = re.sub(r"割り|割る|除す|わる", "/", converted)
        converted = re.sub(r"と", "+", converted)
        converted = re.sub(r"を", "", converted)

        # 数式パターンマッチング
        patterns = [
            r"([0-9]+\s*[+\-*/]\s*[0-9]+(?:\s*[+\-*/]\s*[0-9]+)*)",
            r"([0-9+\-*/().\s]+[+\-*/][0-9+\-*/().\s]+)",
            r"([a-zA-Z]+\([0-9+\-*/().,\s]+\))",
        ]

        for p in patterns:
            m = re.findall(p, converted)
            if m:
                return m[0].strip()

        # 数字を抽出してデフォルト演算
        numbers = re.findall(r"\d+", user_input)
        if len(numbers) >= 2:
            if "足" in user_input or "たし" in user_input or "と" in user_input:
                return f"{numbers[0]}+{numbers[1]}"
            elif "引" in user_input or "ひき" in user_input:
                return f"{numbers[0]}-{numbers[1]}"
            elif "掛" in user_input or "かけ" in user_input:
                return f"{numbers[0]}*{numbers[1]}"
            elif "割" in user_input or "わり" in user_input:
                return f"{numbers[0]}/{numbers[1]}"
            else:
                return f"{numbers[0]}+{numbers[1]}"  # デフォルトは足し算

        return user_input


execution_manager = ExecutionManager()


# Rebuild executor_agent with dynamic tools/instruction based on env flags.
try:
    _use_toolset = os.getenv("USE_ADK_MCP_TOOLSET", "false").lower() in ("1", "true", "yes")
    _dyn_tools: list = []
    if _HAVE_ADK_MCP and _use_toolset:
        _dyn_tools.append(
            MCPToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command=sys.executable,
                        args=["-m", "mcp_tools.calculator"],
                        env={
                            "PYTHONIOENCODING": "utf-8",
                            "PYTHONPATH": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
                        },
                    )
                )
            )
        )
        _dyn_instr = (
            """
与えられた execution_plan を順に実行し、必要に応じてツールを使って結果を取りまとめてください。

ツールの使い方（厳守）:
- ツール名: calculate（MCP）
- 引数: {"expression": "<数式>"}

最終出力は「[数式] = [結果]」形式でまとめ、**テキストのみで回答してください**。
"""
        )
    else:
        _dyn_tools.extend([mcp_calculate, simple_calculate])
        _dyn_instr = (
            """
与えられた execution_plan を順に実行し、必要に応じてツールを使って結果を取りまとめてください。

フォールバックの関数ツールを使う場合（厳守）:
- 関数: mcp_calculate または simple_calculate
- 引数: {"expression": "<数式>"}

最終出力は「[数式] = [結果]」形式でまとめ、**テキストのみで回答してください**。
"""
        )

    executor_agent = LlmAgent(
        name="TaskExecutor",
        model="gemini-2.0-flash-exp",
        description="Execute steps and integrate results",
        tools=_dyn_tools,
        instruction=_dyn_instr,
        output_key="final_result",
    )
except Exception:
    pass

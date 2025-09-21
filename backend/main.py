"""
Maidel 2.2 Backend Main

SequentialAgent pipeline (Conversation -> Planner -> Executor) with a
deterministic fallback executor to ensure results are produced for tasks.
All logs go to stderr; stdout is reserved for JSON responses (JSONL).
"""

import asyncio
import json
import sys
import os
from dotenv import load_dotenv
from google.adk.agents import SequentialAgent
from google.adk.sessions import InMemorySessionService
from google.adk import Runner

# Windows文字エンコーディング対応
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from backend.agents.conversation import conversation_agent
from backend.agents.planner import planner_agent
from backend.agents.executor import executor_agent, execution_manager


# Load environment from .env
load_dotenv()


class MaidelSystem:
    """Maidel 2.2 multi‑agent system wrapper."""

    def __init__(self) -> None:
        # Compose SequentialAgent
        self.maidel_system = SequentialAgent(
            name="MaidelSystem",
            description="Character dialog AI with planning and execution",
            sub_agents=[
                conversation_agent,  # 1. classify chat vs task
                planner_agent,       # 2. build execution plan
                executor_agent       # 3. LLM executor (may be bypassed)
            ],
        )

        # Session service and runner
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            app_name="Maidel2.2",
            agent=self.maidel_system,
            session_service=self.session_service,
        )

    async def process_message(self, message: str) -> dict:
        """Run the pipeline and deterministically execute planned tasks."""
        try:
            print(f"[Maidel] Received: {message}", file=sys.stderr)

            # Create a fresh session
            user_id = "user_001"
            session = await self.session_service.create_session(
                app_name="Maidel2.2", user_id=user_id, state={}
            )
            session_id = session.id

            # Run SequentialAgent with Content message
            from google.genai import types

            user_content = types.Content(role="user", parts=[types.Part(text=message)])
            result_generator = self.runner.run(
                user_id=user_id, session_id=session_id, new_message=user_content
            )

            final_event = None
            session_state: dict = {}
            for event in result_generator:
                final_event = event
                # Merge incremental state deltas if present
                try:
                    actions = getattr(event, "actions", None)
                    state_delta = getattr(actions, "state_delta", None) if actions else None
                    if isinstance(state_delta, dict):
                        session_state.update(state_delta)
                except Exception:
                    pass
                # Merge full session snapshot if provided
                if hasattr(event, "session") and getattr(event, "session"):
                    try:
                        session_state.update(dict(event.session.state))
                    except Exception:
                        pass

            # Extract outputs from LLM agents
            task_type = str(session_state.get("task_type", "unknown")).strip()
            execution_plan_raw = session_state.get("execution_plan", [])

            # Parse execution_plan if it's a JSON string
            execution_plan = []
            if isinstance(execution_plan_raw, str):
                try:
                    # Extract JSON from markdown code block if present
                    import re
                    json_match = re.search(r'```json\s*(\[.*?\])\s*```', execution_plan_raw, re.DOTALL)
                    if json_match:
                        execution_plan = json.loads(json_match.group(1))
                    else:
                        execution_plan = json.loads(execution_plan_raw)
                except (json.JSONDecodeError, AttributeError):
                    execution_plan = []
            elif isinstance(execution_plan_raw, list):
                execution_plan = execution_plan_raw

            final_result = session_state.get("final_result")

            # ExecutionManager disabled - ExecutorAgent handles all execution
            # Determine success based on whether we got a meaningful result
            success = bool(final_result and final_result.strip())
            # Note: ExecutorAgent already executed the plan via SequentialAgent

            # Fallback disabled - SequentialAgent with ExecutorAgent handles all cases
            # All task classification and execution is now handled by the 3-layer agent system

            response = {
                "success": success,
                "message": message,
                "task_type": task_type,
                "execution_plan": execution_plan,
                "result": final_result,
                "session_state": session_state,
                "agent_result": str(final_event),
            }

            print(f"[Maidel] Type: {task_type}", file=sys.stderr)
            return response

        except Exception as e:
            print(f"[Maidel] Error: {e}", file=sys.stderr)
            return {
                "success": False,
                "message": message,
                "error": str(e),
                "error_type": "system_error",
            }

    async def run_interactive(self) -> None:
        """Interactive CLI loop (manual testing)."""
        print("=" * 60)
        print("Maidel 2.2 interactive mode")
        print("'quit' or 'exit' to end")
        print("Try: '2 + 3 を計算して'")
        print("-" * 60)

        while True:
            try:
                user_input = input("あなた: ").strip()
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("Bye.")
                    break
                if not user_input:
                    continue

                response = await self.process_message(user_input)
                if response.get("success"):
                    print(response.get("result") or "処理が完了しました")
                else:
                    print(f"エラー: {response.get('error')}")

            except KeyboardInterrupt:
                print("\nInterrupted. Bye.")
                break
            except Exception as e:
                print(f"System error: {e}")

    async def run_stdio(self) -> None:
        """JSONL stdio mode for Electron bridge."""
        print("Maidel 2.2 stdio mode ready", file=sys.stderr)
        try:
            loop = asyncio.get_event_loop()
            while True:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break  # EOF
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    message = request.get("message", "")
                    if message:
                        response = await self.process_message(message)
                        print(json.dumps(response, ensure_ascii=False), flush=True)
                    else:
                        print(json.dumps({
                            "success": False,
                            "error": "メッセージが空です",
                            "error_type": "empty_message"
                        }, ensure_ascii=False), flush=True)
                except json.JSONDecodeError as e:
                    print(json.dumps({
                        "success": False,
                        "error": f"JSON解析エラー: {e}",
                        "error_type": "json_parse_error",
                    }, ensure_ascii=False), flush=True)

        except Exception as e:
            print(f"stdio通信エラー: {e}", file=sys.stderr)


async def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        maidel = MaidelSystem()
        await maidel.run_stdio()
    else:
        maidel = MaidelSystem()
        await maidel.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())

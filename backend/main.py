"""
Maidel 2.2 メインサーバー

Google ADK SequentialAgent によるマルチエージェントシステム
"""

import asyncio
import json
import sys
from google.adk.agents import SequentialAgent
from google.adk.sessions import Session, InMemorySessionService
from google.adk import Runner
from agents.conversation import conversation_agent
from agents.planner import planner_agent
from agents.executor import executor_agent


class MaidelSystem:
    """Maidel 2.2 マルチエージェントシステム"""

    def __init__(self):
        # SequentialAgent による統合システム
        self.maidel_system = SequentialAgent(
            name="MaidelSystem",
            description="キャラクター対話型AIエージェントシステム - まいでる",
            sub_agents=[
                conversation_agent,  # 1. 意図理解
                planner_agent,       # 2. 計画策定
                executor_agent       # 3. 実行制御
            ]
        )

        # セッションサービス
        self.session_service = InMemorySessionService()

        # Runner作成
        self.runner = Runner(
            app_name="Maidel2.2",
            agent=self.maidel_system,
            session_service=self.session_service
        )

    async def process_message(self, message: str) -> dict:
        """メッセージ処理"""
        try:
            # 新しいセッション作成
            session = Session(
                id="maidel_session_001",
                appName="Maidel2.2",
                userId="user_001"
            )

            # ユーザー入力をセッションに設定
            session.state["user_input"] = message

            print(f"[Maidel] 受信: {message}")

            # SequentialAgent 実行
            result_generator = self.runner.run(
                user_id="user_001",
                session_id=session.id,
                new_message=message
            )

            # 最終結果を取得
            final_event = None
            for event in result_generator:
                final_event = event

            # セッション状態を取得
            current_session = self.session_service.get_session(session.id)

            # 結果の取得
            if current_session:
                task_type = current_session.state.get("task_type", "unknown")
                execution_plan = current_session.state.get("execution_plan", [])
                final_result = current_session.state.get("final_result", "処理に失敗しました")
                session_state = dict(current_session.state)
            else:
                task_type = "unknown"
                execution_plan = []
                final_result = "セッション取得に失敗しました"
                session_state = {}

            response = {
                "success": True,
                "message": message,
                "task_type": task_type,
                "execution_plan": execution_plan,
                "result": final_result,
                "session_state": session_state,
                "agent_result": str(final_event)
            }

            print(f"[Maidel] 処理完了: {task_type}")
            return response

        except Exception as e:
            error_response = {
                "success": False,
                "message": message,
                "error": str(e),
                "error_type": "system_error"
            }
            print(f"[Maidel] エラー: {e}")
            return error_response

    async def run_interactive(self):
        """対話モード実行"""
        print("=" * 60)
        print("🏠 Maidel 2.2 マルチエージェントシステム 起動")
        print("=" * 60)
        print("💬 対話モードを開始します")
        print("📝 'quit' または 'exit' で終了")
        print("🧮 計算例: '2 + 3 を計算して'")
        print("💭 雑談例: 'こんにちは'")
        print("-" * 60)

        while True:
            try:
                # ユーザー入力
                user_input = input("\n👤 あなた: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("🏠 Maidel 2.2 を終了します。お疲れ様でした！")
                    break

                if not user_input:
                    continue

                # メッセージ処理
                response = await self.process_message(user_input)

                # 結果表示
                if response["success"]:
                    print(f"🤖 まいでる: {response['result']}")

                    # デバッグ情報（詳細表示）
                    if input("\n🔍 詳細情報を表示しますか？ (y/N): ").lower() == 'y':
                        print("\n📊 処理詳細:")
                        print(f"   タスク種別: {response['task_type']}")
                        if response['execution_plan']:
                            print(f"   実行ステップ数: {len(response['execution_plan'])}")
                            for i, step in enumerate(response['execution_plan'], 1):
                                print(f"     {i}. {step.get('name', 'Unknown')}")
                else:
                    print(f"❌ エラー: {response['error']}")

            except KeyboardInterrupt:
                print("\n\n🏠 Maidel 2.2 を終了します。")
                break
            except Exception as e:
                print(f"❌ システムエラー: {e}")

    async def run_stdio(self):
        """stdio通信モード（Electron連携用）"""
        print("🔗 Maidel 2.2 stdio通信モード開始", file=sys.stderr)

        try:
            while True:
                # 標準入力から1行読み取り
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:  # EOF
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    # JSON解析
                    request = json.loads(line)
                    message = request.get("message", "")

                    if message:
                        # メッセージ処理
                        response = await self.process_message(message)

                        # JSON応答
                        print(json.dumps(response, ensure_ascii=False), flush=True)
                    else:
                        error_response = {
                            "success": False,
                            "error": "メッセージが空です",
                            "error_type": "empty_message"
                        }
                        print(json.dumps(error_response, ensure_ascii=False), flush=True)

                except json.JSONDecodeError as e:
                    error_response = {
                        "success": False,
                        "error": f"JSON解析エラー: {str(e)}",
                        "error_type": "json_parse_error"
                    }
                    print(json.dumps(error_response, ensure_ascii=False), flush=True)

        except Exception as e:
            print(f"stdio通信エラー: {e}", file=sys.stderr)


async def main():
    """メイン実行関数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        # stdio通信モード
        maidel = MaidelSystem()
        await maidel.run_stdio()
    else:
        # 対話モード
        maidel = MaidelSystem()
        await maidel.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
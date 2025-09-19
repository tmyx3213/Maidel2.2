"""
Direct ADK Agent Test

個別エージェントを直接テストして動作確認
"""

import asyncio
from google.adk.sessions import Session, InMemorySessionService
from google.adk import Runner
from agents.conversation import conversation_agent


async def test_conversation_agent():
    """ConversationAgent 単体テスト"""
    print("Testing ConversationAgent...")

    # セッションサービス作成
    session_service = InMemorySessionService()

    # Runner作成
    runner = Runner(
        app_name="MaidelTest",
        agent=conversation_agent,
        session_service=session_service
    )

    # テストメッセージ
    test_messages = [
        "こんにちは",
        "2 + 3 を計算して",
        "今日はいい天気ですね",
        "10 * 5 はいくつ？"
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Test {i}: {message} ---")

        try:
            # 実行
            result_generator = runner.run(
                user_id="test_user",
                session_id=f"test_session_{i}",
                new_message=message
            )

            # 結果収集
            events = list(result_generator)
            print(f"Events generated: {len(events)}")

            if events:
                final_event = events[-1]
                print(f"Final event: {type(final_event).__name__}")

        except Exception as e:
            print(f"Error: {e}")

    print("\nConversationAgent test completed!")


if __name__ == "__main__":
    asyncio.run(test_conversation_agent())
#!/usr/bin/env python3
"""
ADK 実際のAPI確認テスト
"""
import asyncio
from google.adk.sessions import InMemorySessionService

async def test_real_adk_api():
    """実際のADK APIテスト"""
    print("=== ADK 実際のAPIテスト ===")

    try:
        # セッションサービス作成
        session_service = InMemorySessionService()
        print("[OK] InMemorySessionService作成成功")

        # セッション作成（公式API通り）
        session = await session_service.create_session(
            app_name="TestApp",
            user_id="test_user",
            state={"initial": "value"}
        )
        print(f"[OK] セッション作成成功: {session.id}")

        # セッション取得
        retrieved = await session_service.get_session(
            app_name="TestApp",
            user_id="test_user",
            session_id=session.id
        )
        print(f"[OK] セッション取得成功: {retrieved.id}")

        print("=== 全テスト成功 ===")
        return True

    except Exception as e:
        print(f"[ERROR] エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_real_adk_api())
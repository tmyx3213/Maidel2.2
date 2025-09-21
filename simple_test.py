"""
最小限テスト - セッション作成確認
"""
from google.adk.sessions import Session, InMemorySessionService

def test_session_creation():
    """セッション作成テスト"""
    print("=== セッション作成テスト ===")

    try:
        # セッションサービス作成
        session_service = InMemorySessionService()
        print("[OK] SessionService作成成功")

        # セッション作成
        session_id = "test_session"
        user_id = "test_user"

        session = Session(
            id=session_id,
            userId=user_id,
            appName="TestApp",
            state={}
        )
        print("[OK] Session作成成功")

        # セッション登録
        session_service.create_session(session)
        print("[OK] セッション登録成功")

        # セッション取得
        retrieved = session_service.get_session(user_id, session_id)
        print(f"[OK] セッション取得成功: {retrieved.id}")

        print("=== 全テスト成功 ===")
        return True

    except Exception as e:
        print(f"[ERROR] エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_session_creation()
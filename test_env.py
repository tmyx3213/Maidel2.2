#!/usr/bin/env python3
"""
環境変数テスト
"""
import os
from dotenv import load_dotenv

def test_env():
    print("=== 環境変数テスト ===")

    # .env読み込み前
    api_key_before = os.getenv('GOOGLE_API_KEY')
    print(f"読み込み前: {api_key_before[:10] if api_key_before else 'None'}...")

    # .env読み込み
    load_dotenv()

    # .env読み込み後
    api_key_after = os.getenv('GOOGLE_API_KEY')
    print(f"読み込み後: {api_key_after[:10] if api_key_after else 'None'}...")

    if api_key_after:
        print("[OK] APIキーが正常に読み込まれました")
        return True
    else:
        print("[ERROR] APIキーが読み込まれませんでした")
        return False

if __name__ == "__main__":
    test_env()
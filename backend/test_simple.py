"""
Maidel 2.2 簡易テストスクリプト

Unicode文字を使わない簡単なテスト
"""

import asyncio
from main import MaidelSystem


async def test_maidel():
    """Maidel システムの簡易テスト"""
    print("Starting Maidel 2.2 Multi-Agent System Test...")

    maidel = MaidelSystem()

    # テストケース
    test_cases = [
        "こんにちは",           # 雑談
        "2 + 3 を計算して",     # 計算タスク
        "10 * 5 はいくつ？",    # 計算タスク
        "ありがとう",           # 雑談
    ]

    for i, message in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {message} ---")

        try:
            response = await maidel.process_message(message)

            if response["success"]:
                print(f"Task Type: {response['task_type']}")
                print(f"Result: {response['result']}")
                if response['execution_plan']:
                    print(f"Steps: {len(response['execution_plan'])}")
            else:
                print(f"Error: {response['error']}")

        except Exception as e:
            print(f"Test failed: {e}")

    print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(test_maidel())
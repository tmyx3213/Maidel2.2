#!/usr/bin/env python3
"""
ADK クイックテスト - エラーがすぐわかる
"""
import subprocess
import time

def quick_test():
    """5秒で結果がわかるクイックテスト"""
    print("=== ADK クイックテスト（5秒） ===")

    try:
        # プロセス起動
        process = subprocess.Popen(
            ['py', '-m', 'backend.main', '--stdio'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

        print("プロセス起動中...")
        time.sleep(2)  # 少し待機

        # 生存確認
        if process.poll() is not None:
            print("[ERROR] プロセスが即座に終了")
            stdout, stderr = process.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False

        print("[OK] プロセス起動成功")
        return True

    except Exception as e:
        print(f"[ERROR] 起動エラー: {e}")
        return False
    finally:
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    quick_test()
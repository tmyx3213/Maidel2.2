#!/usr/bin/env python3
"""
Maidel 2.2 stdio通信テスト

修正されたセッション管理をテストします
"""
import subprocess
import json
import time

def test_stdio_communication():
    """stdio通信テスト"""
    print("=== Maidel 2.2 stdio通信テスト ===")

    # ADKプロセス起動
    process = subprocess.Popen(
        ['py', '-m', 'backend.main', '--stdio'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )

    try:
        # テストメッセージ
        test_message = "2+3を計算して"
        request = {"message": test_message}

        print(f"送信: {test_message}")

        # JSONリクエスト送信
        request_line = json.dumps(request, ensure_ascii=False) + '\n'
        process.stdin.write(request_line)
        process.stdin.flush()

        # レスポンス受信（タイムアウト付き）
        print("レスポンス待機中...")

        # 10秒でタイムアウト（短縮）
        start_time = time.time()
        while time.time() - start_time < 10:
            if process.poll() is not None:
                print("プロセス終了")
                break

            # 出力チェック
            try:
                response_line = process.stdout.readline()
                if response_line:
                    print(f"受信: {response_line.strip()}")

                    # JSON解析
                    try:
                        response = json.loads(response_line)
                        print("=== レスポンス解析 ===")
                        print(f"成功: {response.get('success')}")
                        print(f"タスク種別: {response.get('task_type')}")
                        print(f"結果: {response.get('result')}")

                        if response.get('success'):
                            print("[OK] テスト成功！セッション管理が修正されました")
                        else:
                            print(f"[ERROR] エラー: {response.get('error')}")
                        break
                    except json.JSONDecodeError as e:
                        print(f"JSON解析エラー: {e}")
                        break
            except:
                time.sleep(0.1)
        else:
            print("[TIMEOUT] タイムアウト")

    except Exception as e:
        print(f"テストエラー: {e}")

    finally:
        # エラー出力も確認
        if process.stderr:
            stderr_output = process.stderr.read()
            if stderr_output:
                print(f"[STDERR] {stderr_output}")

        # プロセス終了
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
        print("プロセス終了")

if __name__ == "__main__":
    test_stdio_communication()
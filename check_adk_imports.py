"""
ADK の利用可能なインポートを確認
"""

try:
    import google.adk
    print("[OK] google.adk")

    # 利用可能なモジュールを確認
    import pkgutil
    print("\n=== google.adk 内のモジュール ===")
    for importer, modname, ispkg in pkgutil.iter_modules(google.adk.__path__, 'google.adk.'):
        print(f"  {modname}")

    # よくありそうなインポートを試す
    imports_to_test = [
        'google.adk.core',
        'google.adk.core.UserContent',
        'google.adk.types',
        'google.adk.types.UserContent',
        'google.adk.content',
        'google.adk.content.UserContent',
        'google.adk.messages',
        'google.adk.messages.UserContent'
    ]

    print("\n=== インポートテスト ===")
    for imp in imports_to_test:
        try:
            exec(f"from {imp} import *")
            print(f"[OK] {imp}")
        except ImportError as e:
            print(f"[FAIL] {imp}: {e}")

except Exception as e:
    print(f"エラー: {e}")
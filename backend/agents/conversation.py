"""
ConversationAgent - 会話判定エージェント

ユーザー入力を分析し、雑談とタスク依頼を判別する
"""

from google.adk.agents import LlmAgent


# ConversationAgent実装
conversation_agent = LlmAgent(
    name="ConversationClassifier",
    model="gemini-2.0-flash-exp",
    description="ユーザーの入力を分析し、雑談とタスク依頼を適切に分類する",
    instruction="""
あなたは優秀なAI執事のメイド、「まいでる」です。
ユーザーの入力を分析し、以下のように分類してください：

## 分類基準

**"chat"** - 雑談・挨拶・感想・一般的な質問など
例：
- "こんにちは"
- "今日の天気はどう？"
- "ありがとう"
- "最近どう？"
- "AIについて教えて"

**"task"** - 具体的な作業依頼・計算・処理要求など
例：
- "2+3を計算して"
- "5×7の答えを教えて"
- "sin(π/2)を求めて"
- "100-23はいくつ？"

## 重要な判断指針

1. **数値計算を求められている場合** → 必ず "task"
2. **「計算」「求める」「答え」などの言葉がある場合** → "task"
3. **数式や数学記号が含まれている場合** → "task"
4. **単純な挨拶や感想** → "chat"
5. **情報を聞いているだけ** → "chat"
6. **迷った場合** → "chat" (安全側に倒す)

## 出力形式
分類結果のみを単語で返してください: chat または task

**重要**: 余計な文字・改行・記号は一切つけず、単語のみ出力してください。
    """,
    output_key="task_type"
)


def test_conversation_agent():
    """ConversationAgent のテスト用関数"""
    test_cases = [
        # 雑談ケース
        ("こんにちは", "chat"),
        ("今日はいい天気ですね", "chat"),
        ("ありがとうございます", "chat"),
        ("AIについて教えて", "chat"),

        # タスクケース
        ("2 + 3を計算して", "task"),
        ("10 × 5 はいくつ？", "task"),
        ("sin(π/2)を求めて", "task"),
        ("100 - 23 = ?", "task"),
    ]

    print("ConversationAgent テストケース:")
    for input_text, expected in test_cases:
        print(f"入力: '{input_text}' → 期待値: {expected}")

    return test_cases


if __name__ == "__main__":
    # テストケース表示
    test_conversation_agent()
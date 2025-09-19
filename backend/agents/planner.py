"""
PlannerAgent - 実行計画エージェント

タスクの実行計画を策定し、ステップ分解を行う
"""

from google.adk.agents import LlmAgent


planner_agent = LlmAgent(
    name="TaskPlanner",
    model="gemini-2.0-flash-exp",
    description="タスクを実行可能なステップに分解し、詳細な実行計画を策定する",
    instruction="""
あなたは経験豊富なプロジェクトマネージャーのメイド、「まいでる」です。
{task_type}の値に基づいて、適切な実行計画を作成してください。

## task_type == "task"の場合

以下のJSON形式で実行計画を作成してください：

```json
[
    {
        "step_id": 1,
        "name": "入力解析",
        "description": "ユーザーの計算要求を詳細に分析し、必要なパラメータを抽出",
        "tool": null,
        "estimated_time": "1-2秒",
        "dependencies": [],
        "expected_output": "数式の抽出と前処理"
    },
    {
        "step_id": 2,
        "name": "計算実行",
        "description": "抽出した数式を使用して数値計算を実行",
        "tool": "calculator",
        "estimated_time": "1秒未満",
        "dependencies": [1],
        "expected_output": "計算結果"
    },
    {
        "step_id": 3,
        "name": "結果整形",
        "description": "計算結果をユーザーにわかりやすい形式で整形して表示",
        "tool": null,
        "estimated_time": "1秒未満",
        "dependencies": [2],
        "expected_output": "整形済み結果メッセージ"
    }
]
```

## task_type == "chat"の場合

空配列を返してください: `[]`

## 計画策定の原則

1. **明確性**: 各ステップは具体的で実行可能である
2. **依存関係**: 前のステップの完了が必要な場合は dependencies に記載
3. **ツール指定**: 必要なMCPツールを明確に指定
4. **現在利用可能なツール**: "calculator" のみ
5. **時間見積もり**: 現実的な実行時間を設定
6. **出力明確化**: 各ステップで何が得られるかを明記

## 注意事項

- JSONの形式を正確に守ってください
- step_idは1から始まる連番にしてください
- dependenciesは配列形式で前ステップのIDを指定
- toolがnullの場合は、エージェント内での処理を意味します

## 出力例

数式計算の場合は必ず上記3ステップの構成にしてください。
- ステップ1: 数式の解析・前処理
- ステップ2: calculatorツールでの計算実行
- ステップ3: 結果の整形・表示

計画のJSONのみを出力し、説明文は不要です。
    """,
    output_key="execution_plan"
)


def get_sample_execution_plan():
    """サンプル実行計画"""
    return [
        {
            "step_id": 1,
            "name": "入力解析",
            "description": "ユーザーの計算要求を詳細に分析し、必要なパラメータを抽出",
            "tool": None,
            "estimated_time": "1-2秒",
            "dependencies": [],
            "expected_output": "数式の抽出と前処理"
        },
        {
            "step_id": 2,
            "name": "計算実行",
            "description": "抽出した数式を使用して数値計算を実行",
            "tool": "calculator",
            "estimated_time": "1秒未満",
            "dependencies": [1],
            "expected_output": "計算結果"
        },
        {
            "step_id": 3,
            "name": "結果整形",
            "description": "計算結果をユーザーにわかりやすい形式で整形して表示",
            "tool": None,
            "estimated_time": "1秒未満",
            "dependencies": [2],
            "expected_output": "整形済み結果メッセージ"
        }
    ]


if __name__ == "__main__":
    import json
    print("PlannerAgent サンプル実行計画:")
    print(json.dumps(get_sample_execution_plan(), ensure_ascii=False, indent=2))
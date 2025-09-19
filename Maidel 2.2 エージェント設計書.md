# Maidel 2.2 エージェント設計書

## 1. エージェントアーキテクチャ概要

### 1.1 階層構造
```
Maidel2.2System (SequentialAgent)
├── ConversationAgent (LlmAgent)     # Layer 1: 意図理解
├── PlannerAgent (LlmAgent)          # Layer 2: 計画策定  
└── ExecutorAgent (LlmAgent)         # Layer 3: 実行制御
    └── MCP Tools                    # Layer 4: 実際の処理
        ├── Calculator Tool
        └── Memory Tool
```

### 1.2 設計原則
- **単一責任**: 各エージェントは明確に定義された単一の責任を持つ
- **疎結合**: エージェント間はShared Session Stateのみで通信
- **拡張性**: 新しいエージェントやツールを容易に追加可能
- **可視性**: 各処理ステップが外部から観測可能

### 1.3 通信プロトコル
```python
# ADK Shared Session State構造
{
    "user_input": str,              # ユーザー入力
    "task_type": str,               # ConversationAgent → PlannerAgent
    "execution_plan": List[dict],   # PlannerAgent → ExecutorAgent
    "current_step": int,            # 実行中ステップ番号
    "step_results": dict,           # 各ステップの結果
    "final_result": any,            # ExecutorAgent → UI
    "error_info": dict,             # エラー情報
    "metadata": dict                # メタ情報（タイムスタンプ等）
}
```

## 2. Layer 1: ConversationAgent (意図理解層)

### 2.1 役割・責務
- ユーザー入力の意図分類（雑談 vs タスク依頼）
- コンテキスト理解と前処理
- 次層エージェントへの適切な情報伝達

### 2.2 実装仕様
```python
from google.adk.agents import LlmAgent

conversation_agent = LlmAgent(
    name="ConversationClassifier",
    model="gemini-2.0-flash-exp",
    description="ユーザー入力を分析し、適切な処理フローに振り分ける",
    instruction="""
あなたは優秀なAI執事です。ユーザーの入力を分析し、以下のように分類してください：

## 分類基準
1. **"chat"** - 雑談・挨拶・感想・質問など
   例: "こんにちは", "調子はどう？", "天気について教えて"
   
2. **"task"** - 具体的な作業依頼・計算・処理要求など
   例: "2+3を計算して", "データを分析して", "ファイルを整理して"

## 出力形式
分類結果のみを返してください: "chat" または "task"

## 判断に迷う場合
- 具体的なアクションを求めている → "task"
- 情報収集や雑談目的 → "chat"
- 明確でない場合 → "chat" (安全側に倒す)
    """,
    output_key="task_type"
)
```

### 2.3 入出力仕様
```python
# 入力
{
    "user_input": "2 + 3 を計算してください"
}

# 処理後のState更新
{
    "user_input": "2 + 3 を計算してください",
    "task_type": "task",
    "metadata": {
        "conversation_agent_timestamp": "2025-09-19T10:30:00Z",
        "classification_confidence": 0.95
    }
}
```

### 2.4 エラーハンドリング
```python
# 分類不能な場合のフォールバック
if classification_result not in ["chat", "task"]:
    fallback_classification = "chat"  # 安全側へフォールバック
    error_info = {
        "agent": "ConversationAgent",
        "error_type": "classification_failed",
        "original_result": classification_result,
        "fallback_applied": True
    }
```

## 3. Layer 2: PlannerAgent (計画策定層)

### 3.1 役割・責務
- タスクの実行計画策定
- 必要なツール・リソースの特定
- 実行可能な形でのステップ分解

### 3.2 実装仕様
```python
planner_agent = LlmAgent(
    name="TaskPlanner",
    model="gemini-2.0-flash-exp", 
    description="タスクを実行可能なステップに分解し、詳細な実行計画を策定する",
    instruction="""
あなたは経験豊富なプロジェクトマネージャーです。
{task_type}の値に基づいて、適切な実行計画を作成してください。

## task_type == "task"の場合

以下のJSON形式で実行計画を作成してください：

```json
[
    {
        "step_id": 1,
        "name": "入力解析",
        "description": "ユーザーの要求を詳細に分析し、必要なパラメータを抽出",
        "tool": null,
        "estimated_time": "1-2秒",
        "dependencies": [],
        "expected_output": "解析結果"
    },
    {
        "step_id": 2,
        "name": "計算実行", 
        "description": "抽出したパラメータを使用して数値計算を実行",
        "tool": "calculator",
        "estimated_time": "1秒未満",
        "dependencies": [1],
        "expected_output": "計算結果"
    },
    {
        "step_id": 3,
        "name": "結果整形",
        "description": "計算結果をユーザーにわかりやすい形式で整形",
        "tool": null,
        "estimated_time": "1秒未満", 
        "dependencies": [2],
        "expected_output": "整形済み結果"
    }
]
```

## task_type == "chat"の場合

空配列を返してください: `[]`

## 計画策定の原則
- 各ステップは明確で実行可能である
- 依存関係を適切に設定する
- 必要なツールを明確に指定する
- 現在利用可能なツール: "calculator"のみ
    """,
    output_key="execution_plan"
)
```

### 3.3 実行計画データ構造
```python
# ExecutionPlan型定義
from typing import List, Optional, Dict, Any

class PlanStep:
    step_id: int
    name: str
    description: str
    tool: Optional[str]           # 使用するMCPツール名
    estimated_time: str
    dependencies: List[int]       # 依存する前ステップのID
    expected_output: str
    status: str = "pending"       # pending/running/completed/error
    actual_output: Any = None
    error_message: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

ExecutionPlan = List[PlanStep]
```

### 3.4 計画策定アルゴリズム
```python
def validate_execution_plan(plan: ExecutionPlan) -> Dict[str, Any]:
    """実行計画の妥当性検証"""
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    # 循環依存チェック
    # ツール可用性チェック
    # ステップID重複チェック
    
    return validation_result
```

## 4. Layer 3: ExecutorAgent (実行制御層)

### 4.1 役割・責務
- 実行計画に従ったステップ実行
- MCPツールとの連携制御
- 実行状態の管理・監視
- エラー時の例外処理

### 4.2 実装仕様
```python
from google.adk.tools import MCPToolset

# MCPツール統合
calculator_mcp = MCPToolset(
    name="calculator",
    connect_params={
        "type": "stdio",
        "command": ["python", "-m", "mcp_tools.calculator"],
        "timeout": 30
    }
)

executor_agent = LlmAgent(
    name="TaskExecutor",
    model="gemini-2.0-flash-exp",
    description="実行計画に従ってタスクを順次実行し、結果を統合する",
    instruction="""
あなたは熟練したタスク実行マネージャーです。
{execution_plan}に従って、各ステップを順次実行してください。

## 実行の原則
1. **順序遵守**: 依存関係を考慮し、適切な順序で実行
2. **状態管理**: 各ステップの状態を正確に記録
3. **エラー処理**: 失敗時は詳細な情報を記録し、可能な範囲で継続
4. **結果統合**: 全ステップの結果を意味のある形で統合

## 実行プロセス
各ステップについて：
1. 依存関係を確認
2. 必要なツールを呼び出し
3. 結果を記録
4. 次ステップに進む

## 使用可能ツール
- calculator: 数値計算実行

## 最終出力
全ステップ完了後、統合された結果を返してください。
    """,
    tools=[calculator_mcp],
    output_key="final_result"
)
```

### 4.3 実行状態管理
```python
class ExecutionState:
    def __init__(self, plan: ExecutionPlan):
        self.plan = plan
        self.current_step_index = 0
        self.completed_steps = []
        self.failed_steps = []
        self.start_time = None
        self.end_time = None
        
    def get_next_executable_step(self) -> Optional[PlanStep]:
        """依存関係を満たす次の実行可能ステップを取得"""
        for step in self.plan:
            if step.status == "pending" and self._dependencies_satisfied(step):
                return step
        return None
    
    def _dependencies_satisfied(self, step: PlanStep) -> bool:
        """ステップの依存関係が満たされているかチェック"""
        for dep_id in step.dependencies:
            dep_step = self.find_step_by_id(dep_id)
            if not dep_step or dep_step.status != "completed":
                return False
        return True
    
    def update_step_status(self, step_id: int, status: str, result: Any = None):
        """ステップ状態の更新"""
        step = self.find_step_by_id(step_id)
        if step:
            step.status = status
            step.actual_output = result
            if status == "running":
                step.start_time = datetime.now().isoformat()
            elif status in ["completed", "error"]:
                step.end_time = datetime.now().isoformat()
```

### 4.4 MCPツール連携制御
```python
async def execute_step_with_tool(self, step: PlanStep, tool_name: str, params: dict):
    """MCPツールを使用したステップ実行"""
    try:
        # ツール呼び出し
        tool_result = await self.call_mcp_tool(tool_name, params)
        
        # 結果の検証・整形
        processed_result = self.process_tool_result(tool_result, step)
        
        return {
            "success": True,
            "result": processed_result,
            "tool_used": tool_name,
            "execution_time": self.calculate_execution_time(step)
        }
        
    except MCPToolException as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "mcp_tool_error",
            "step_id": step.step_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "unexpected_error", 
            "step_id": step.step_id
        }
```

## 5. Layer 4: MCPツール層

### 5.1 Calculator Tool仕様

#### 5.1.1 機能要件
- 基本四則演算 (+, -, *, /)
- 括弧を含む複雑な式の計算
- 数学関数 (sin, cos, sqrt, log等)
- エラーハンドリング (ゼロ除算、不正な式等)

#### 5.1.2 実装仕様
```python
# mcp_tools/calculator/server.py
import json
import math
import re
from typing import Dict, Any, Union

class CalculatorMCPServer:
    def __init__(self):
        self.supported_functions = {
            'sin', 'cos', 'tan', 'sqrt', 'log', 'log10',
            'abs', 'ceil', 'floor', 'round'
        }
    
    def list_tools(self) -> Dict[str, Any]:
        return {
            "tools": [
                {
                    "name": "calculate",
                    "description": "数学的な計算式を評価し、結果を返す",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "計算する数式 (例: '2 + 3 * 4', 'sqrt(16)', 'sin(3.14/2)')"
                            }
                        },
                        "required": ["expression"]
                    }
                },
                {
                    "name": "validate_expression",
                    "description": "数式の妥当性を事前チェック",
                    "inputSchema": {
                        "type": "object", 
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "検証する数式"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            ]
        }
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "calculate":
            return self._calculate(arguments.get("expression", ""))
        elif name == "validate_expression":
            return self._validate_expression(arguments.get("expression", ""))
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {name}"
            }
    
    def _calculate(self, expression: str) -> Dict[str, Any]:
        try:
            # 式の前処理・サニタイゼーション
            sanitized_expr = self._sanitize_expression(expression)
            
            # 安全な評価実行
            result = self._safe_eval(sanitized_expr)
            
            return {
                "success": True,
                "result": result,
                "expression": expression,
                "sanitized_expression": sanitized_expr,
                "result_type": type(result).__name__
            }
            
        except ZeroDivisionError:
            return {
                "success": False,
                "error": "ゼロで除算しようとしました",
                "error_type": "division_by_zero"
            }
        except ValueError as e:
            return {
                "success": False,
                "error": f"数値変換エラー: {str(e)}",
                "error_type": "value_error"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"計算エラー: {str(e)}",
                "error_type": "calculation_error"
            }
    
    def _sanitize_expression(self, expr: str) -> str:
        """数式のサニタイゼーション"""
        # 危険な文字列を除去
        dangerous_patterns = [
            r'__.*__',  # dunder methods
            r'import',  # import statements
            r'exec',    # exec function
            r'eval',    # eval function
            r'open',    # file operations
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expr, re.IGNORECASE):
                raise ValueError(f"不正な式が検出されました: {pattern}")
        
        # 数学関数の置換
        expr = expr.replace('^', '**')  # 指数演算子
        
        # 数学関数のプレフィックス追加
        for func in self.supported_functions:
            expr = re.sub(rf'\b{func}\b', f'math.{func}', expr)
            
        return expr
    
    def _safe_eval(self, expr: str) -> Union[int, float]:
        """制限された環境での式評価"""
        allowed_names = {
            "__builtins__": {},
            "math": math,
        }
        
        return eval(expr, allowed_names, {})
```

### 5.2 Memory Tool仕様

#### 5.2.1 機能要件
- セッション内キー・バリューストレージ
- 一時的なコンテキスト情報の保存・取得
- データ型の自動判定・変換

#### 5.2.2 実装仕様
```python
# mcp_tools/memory/server.py
class MemoryMCPServer:
    def __init__(self):
        self.session_storage = {}
        self.metadata = {}
    
    def list_tools(self) -> Dict[str, Any]:
        return {
            "tools": [
                {
                    "name": "store",
                    "description": "キー・バリュー形式でデータを保存",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "保存キー"},
                            "value": {"type": "string", "description": "保存する値"},
                            "data_type": {"type": "string", "enum": ["string", "number", "json"], "description": "データ型"}
                        },
                        "required": ["key", "value"]
                    }
                },
                {
                    "name": "retrieve",
                    "description": "キーに対応する値を取得",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "取得キー"}
                        },
                        "required": ["key"]
                    }
                },
                {
                    "name": "list_keys",
                    "description": "保存されているキーの一覧を取得",
                    "inputSchema": {"type": "object", "properties": {}}
                }
            ]
        }
```

## 6. エージェント間連携シーケンス

### 6.1 正常処理フロー
```
User Input: "2 + 3 * 4 を計算して"
     ↓
┌─────────────────────────────────────────────────────────────┐
│ ConversationAgent                                           │
│ ├─ Input: "2 + 3 * 4 を計算して"                            │
│ ├─ Analysis: タスク依頼と判定                                │
│ └─ State Update: {task_type: "task"}                       │
└─────────────────────────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────────────────────┐
│ PlannerAgent                                               │
│ ├─ Input: {task_type: "task"}                             │
│ ├─ Planning: 計算タスクの実行計画策定                        │
│ └─ State Update: {execution_plan: [                       │
│     {step_id: 1, name: "式解析", tool: null},             │
│     {step_id: 2, name: "計算実行", tool: "calculator"},    │
│     {step_id: 3, name: "結果整形", tool: null}            │
│   ]}                                                       │
└─────────────────────────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────────────────────┐
│ ExecutorAgent                                              │
│ ├─ Input: {execution_plan: [...]}                         │
│ ├─ Step 1: 式解析 ("2 + 3 * 4" → パラメータ抽出)            │
│ ├─ Step 2: MCP Calculator Tool Call                       │
│ │   ├─ Tool: calculator                                   │
│ │   ├─ Params: {expression: "2 + 3 * 4"}                 │
│ │   └─ Result: {success: true, result: 14}               │
│ ├─ Step 3: 結果整形 ("計算結果: 14")                        │
│ └─ State Update: {final_result: "2 + 3 * 4 = 14"}        │
└─────────────────────────────────────────────────────────────┘
     ↓
UI Display: "2 + 3 * 4 = 14"
```

### 6.2 エラー処理フロー
```
User Input: "10 / 0 を計算して"
     ↓
ConversationAgent → task_type: "task" ✅
     ↓
PlannerAgent → execution_plan: [...] ✅
     ↓
ExecutorAgent → Step 2: Calculator Tool Call
     ↓
┌─────────────────────────────────────────┐
│ Calculator MCP Tool                     │
│ ├─ Input: {expression: "10 / 0"}       │
│ ├─ Error: ZeroDivisionError            │
│ └─ Response: {                         │
│     success: false,                    │
│     error: "ゼロで除算しようとしました",     │
│     error_type: "division_by_zero"     │
│   }                                    │
└─────────────────────────────────────────┘
     ↓
ExecutorAgent → エラーハンドリング
     ↓
State Update: {
  final_result: "エラーが発生しました: ゼロで除算しようとしました",
  error_info: {
    step_id: 2,
    error_type: "division_by_zero",
    recoverable: false
  }
}
     ↓
UI Display: "申し訳ございません。計算中にエラーが発生しました: ゼロで除算しようとしました"
```

## 7. 状態管理・監視仕様

### 7.1 リアルタイム状態追跡
```python
class StateManager:
    def __init__(self):
        self.current_state = {}
        self.state_history = []
        self.observers = []  # UI更新用コールバック
    
    def update_state(self, key: str, value: Any, agent_name: str):
        """状態更新とオブザーバー通知"""
        old_value = self.current_state.get(key)
        self.current_state[key] = value
        
        # 履歴記録
        self.state_history.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "key": key,
            "old_value": old_value,
            "new_value": value
        })
        
        # オブザーバー通知（UI更新用）
        self.notify_observers(key, value)
    
    def notify_observers(self, key: str, value: Any):
        for observer in self.observers:
            try:
                observer(key, value)
            except Exception as e:
                print(f"Observer notification error: {e}")
    
    def get_execution_progress(self) -> Dict[str, Any]:
        """実行進捗の詳細情報を取得"""
        plan = self.current_state.get("execution_plan", [])
        current_step = self.current_state.get("current_step", 0)
        
        if not plan:
            return {"progress": 0, "status": "no_plan"}
        
        completed_steps = sum(1 for step in plan if step.get("status") == "completed")
        total_steps = len(plan)
        
        return {
            "progress": completed_steps / total_steps * 100,
            "current_step": current_step,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "status": self._determine_overall_status(plan),
            "current_step_name": plan[current_step].get("name") if current_step < len(plan) else None
        }
```

### 7.2 パフォーマンス監視
```python
class PerformanceMonitor:
    def __init__(self):
        self.agent_metrics = {}
        self.tool_metrics = {}
    
    def record_agent_execution(self, agent_name: str, execution_time: float, success: bool):
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = {
                "total_executions": 0,
                "total_time": 0,
                "success_count": 0,
                "error_count": 0,
                "avg_time": 0
            }
        
        metrics = self.agent_metrics[agent_name]
        metrics["total_executions"] += 1
        metrics["total_time"] += execution_time
        
        if success:
            metrics["success_count"] += 1
        else:
            metrics["error_count"] += 1
            
        metrics["avg_time"] = metrics["total_time"] / metrics["total_executions"]
    
    def get_performance_report(self) -> Dict[str, Any]:
        return {
            "agents": self.agent_metrics,
            "tools": self.tool_metrics,
            "overall": {
                "total_requests": sum(m["total_executions"] for m in self.agent_metrics.values()),
                "avg_response_time": self._calculate_overall_avg_time(),
                "success_rate": self._calculate_success_rate()
            }
        }
```

## 8. 拡張性・保守性設計

### 8.1 新エージェント追加パターン
```python
# 新エージェントの実装例
class DataAnalysisAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="DataAnalysisAgent",
            model="gemini-2.0-flash-exp",
            description="データ分析とレポート生成を行う",
            instruction="""
            データ分析専門のエージェントです。
            {data_source}から{analysis_type}を実行し、
            結果をレポート形式で出力してください。
            """,
            tools=[data_processing_mcp, visualization_mcp],
            output_key="analysis_result"
        )

# メインシステムへの組み込み
enhanced_maidel_system = SequentialAgent(
    name="EnhancedMaidel2.2System",
    sub_agents=[
        conversation_agent,
        planner_agent,
        data_analysis_agent,  # 新エージェント追加
        executor_agent
    ]
)
```

### 8.2 新MCPツール追加パターン
```python
# 新ツールの実装
class FileOperationMCPServer:
    def __init__(self):
        self.tools = {
            "read_file": {"description": "ファイル読み込み"},
            "write_file": {"description": "ファイル書き込み"},
            "list_directory": {"description": "ディレクトリ一覧"}
        }
    # 実装...

# エージェントへの組み込み
file_ops_mcp = MCPToolset(
    name="file_operations",
    connect_params={
        "type": "stdio",
        "command": ["python", "-m", "mcp_tools.file_operations"]
    }
)

executor_agent.tools.append(file_ops_mcp)
```

### 8.3 設定・コンフィグ管理
```python
# config/agents_config.yaml
agents:
  conversation:
    model: "gemini-2.0-flash-exp"
    temperature: 0.1
    max_tokens: 1000
    
  planner:
    model: "gemini-2.0-flash-exp"
    temperature: 0.3
    max_tokens: 2000
    enable_step_validation: true
    
  executor:
    model: "gemini-2.0-flash-exp"
    temperature: 0.1
    max_retries: 3
    timeout_seconds: 30
    
mcp_tools:
  calculator:
    enabled: true
    timeout: 10
    max_expression_length: 500
    
  memory:
    enabled: true
    max_storage_size: 1000
    auto_cleanup: true
```

## 9. テスト戦略

### 9.1 単体テスト
```python
import pytest
from unittest.mock import Mock, patch

class TestConversationAgent:
    def test_task_classification(self):
        agent = conversation_agent
        
        # タスク依頼のテスト
        result = await agent.run(create_session("2+3を計算して"))
        assert result.state["task_type"] == "task"
        
        # 雑談のテスト  
        result = await agent.run(create_session("こんにちは"))
        assert result.state["task_type"] == "chat"
    
    def test_edge_cases(self):
        # 曖昧な入力のテスト
        result = await agent.run(create_session("計算について教えて"))
        assert result.state["task_type"] == "chat"  # 安全側に分類
```

### 9.2 統合テスト
```python
class TestMultiAgentIntegration:
    @pytest.mark.asyncio
    async def test_full_calculation_flow(self):
        system = maidel_system
        session = create_session()
        
        result = await system.run(session, "5 + 7 を計算して")
        
        # 各エージェントの状態確認
        assert session.state["task_type"] == "task"
        assert len(session.state["execution_plan"]) > 0
        assert "12" in str(session.state["final_result"])
```

### 9.3 パフォーマンステスト
```python
class TestPerformance:
    def test_response_time_requirement(self):
        """10秒以内のレスポンス時間要件テスト"""
        start_time = time.time()
        result = await maidel_system.run(session, "複雑な計算を実行")
        execution_time = time.time() - start_time
        
        assert execution_time < 10.0, f"Response time {execution_time}s exceeds 10s limit"
```

## 10. デバッグ・ログ戦略

### 10.1 構造化ログ
```python
import logging
import json

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def log_agent_start(self, agent_name: str, input_data: dict):
        self.logger.info(json.dumps({
            "event": "agent_start",
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "input": input_data
        }))
    
    def log_state_change(self, key: str, old_value: Any, new_value: Any, agent_name: str):
        self.logger.info(json.dumps({
            "event": "state_change",
            "agent": agent_name,
            "key": key,
            "old_value": str(old_value),
            "new_value": str(new_value),
            "timestamp": datetime.now().isoformat()
        }))
```

### 10.2 デバッグUI向けデータ出力
```python
def get_debug_info() -> Dict[str, Any]:
    """デバッグUI用の詳細情報を取得"""
    return {
        "current_state": state_manager.current_state,
        "state_history": state_manager.state_history[-10:],  # 最新10件
        "performance_metrics": performance_monitor.get_performance_report(),
        "active_agents": [agent.name for agent in active_agents],
        "mcp_tool_status": {
            tool_name: tool.is_connected() 
            for tool_name, tool in mcp_tools.items()
        }
    }
```

---

**作成日**: 2025年9月19日  
**作成者**: クロコ（執事AI）  
**対象読者**: 開発チーム & Claude Code  
**バージョン**: 1.0  

**注記**: このエージェント設計書は、Google ADKの最新仕様に基づいて作成されています。実装時にはADKのドキュメントと照合し、必要に応じて調整を行ってください。
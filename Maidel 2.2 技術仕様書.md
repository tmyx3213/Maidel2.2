# Maidel 2.2 技術仕様書

## 1. システム アーキテクチャ

### 1.1 全体構成
```
┌─────────────────────────────────────────────────────────────┐
│                    Electron Main Process                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐  │
│  │  React Renderer │    │     ADK Python Process         │  │
│  │                 │    │                                 │  │
│  │  ┌─────────────┐│    │  ┌─────────────────────────────┐│  │
│  │  │Character UI ││<──>│  │    Sequential Agent        ││  │
│  │  └─────────────┘│    │  │                             ││  │
│  │  ┌─────────────┐│    │  │ ┌──────────────────────────┐││  │
│  │  │PlanVisualiz ││<──>│  │ │  ConversationAgent       │││  │
│  │  │er Component ││    │  │ │  (LlmAgent)              │││  │
│  │  └─────────────┘│    │  │ │  output_key: task_type   │││  │
│  │  ┌─────────────┐│    │  │ └──────────────────────────┘││  │
│  │  │Chat History ││    │  │ ┌──────────────────────────┐││  │
│  │  │Component    ││    │  │ │  PlannerAgent            │││  │
│  │  └─────────────┘│    │  │ │  (LlmAgent)              │││  │
│  └─────────────────┘    │  │ │  output_key: exec_plan   │││  │
│                         │  │ └──────────────────────────┘││  │
│                         │  │ ┌──────────────────────────┐││  │
│                         │  │ │  ExecutorAgent           │││  │
│                         │  │ │  (LlmAgent + MCP Tools)  │││  │
│                         │  │ │  output_key: result      │││  │
│                         │  │ └──────────────────────────┘││  │
│                         │  └─────────────────────────────┘│  │
│                         │                                 │  │
│                         │  ┌─────────────────────────────┐│  │
│                         │  │     MCP Tools               ││  │
│                         │  │  ┌─────────────────────────┐││  │
│                         │  │  │  calculator.py          │││  │
│                         │  │  │  (Basic Math)           │││  │
│                         │  │  └─────────────────────────┘││  │
│                         │  │  ┌─────────────────────────┐││  │
│                         │  │  │  memory.py              │││  │
│                         │  │  │  (Session State)        │││  │
│                         │  │  └─────────────────────────┘││  │
│                         │  └─────────────────────────────┘│  │
│                         └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技術スタック

#### 1.2.1 フロントエンド
- **Electron**: v32.x以降
- **React**: v18.x
- **TypeScript**: v5.x
- **CSS Framework**: CSS Modules または Styled Components

#### 1.2.2 バックエンド
- **Google ADK**: 最新版（Python）
- **Python**: 3.9+
- **MCP SDK**: Python実装

#### 1.2.3 通信・連携
- **IPC通信**: Electron Main ↔ Renderer
- **プロセス間通信**: stdio/http による ADK ↔ MCP
- **状態管理**: ADK Shared Session State

## 2. データフロー設計

### 2.1 メッセージフロー
```
User Input → React UI → Electron Main → ADK Python Process
                ↓
    ┌─────────────────────────────────────────────────┐
    │           ADK Sequential Agent                  │
    │                                                 │
    │  1. ConversationAgent                           │
    │     Input: user_message                         │
    │     Output: task_type (chat|task)              │
    │     State: {task_type: "task"}                  │
    │                                                 │
    │  2. PlannerAgent                                │
    │     Input: {task_type} from state               │
    │     Output: execution_plan                      │
    │     State: {task_type: "task",                  │
    │            execution_plan: [step1, step2...]}   │
    │                                                 │
    │  3. ExecutorAgent                               │
    │     Input: {execution_plan} from state          │
    │     Action: Call MCP Tools                      │
    │     Output: result                              │
    │     State: {task_type: "task",                  │
    │            execution_plan: [...],               │
    │            result: "42"}                        │
    └─────────────────────────────────────────────────┘
                ↓
Result → Electron Main → React UI → User Display
```

### 2.2 状態管理

#### 2.2.1 ADK Session State構造
```python
{
    "user_input": str,           # ユーザー入力
    "task_type": str,            # "chat" | "task"
    "execution_plan": list,      # 実行計画ステップ
    "current_step": int,         # 現在実行中ステップ
    "step_status": dict,         # 各ステップの状態
    "result": any,               # 最終結果
    "error": str,                # エラー情報
    "timestamp": str             # 処理開始時刻
}
```

#### 2.2.2 React State構造
```typescript
interface AppState {
  messages: ChatMessage[];
  currentPlan: ExecutionPlan | null;
  isProcessing: boolean;
  character: {
    image: string;
    expression: string;
  };
}

interface ExecutionPlan {
  steps: PlanStep[];
  currentStepIndex: number;
  status: 'pending' | 'running' | 'completed' | 'error';
}

interface PlanStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  result?: any;
}
```

## 3. ADKエージェント実装設計

### 3.1 ConversationAgent（会話判定）
```python
from google.adk.agents import LlmAgent

conversation_agent = LlmAgent(
    name="ConversationClassifier",
    model="gemini-2.0-flash-exp",
    instruction="""
    ユーザーの入力を分析し、以下のいずれかに分類してください：
    
    1. "chat" - 雑談、挨拶、感想など
    2. "task" - 具体的なタスク依頼（計算、処理要求など）
    
    分類結果のみを返してください。
    """,
    output_key="task_type"
)
```

### 3.2 PlannerAgent（実行計画）
```python
planner_agent = LlmAgent(
    name="TaskPlanner",
    model="gemini-2.0-flash-exp", 
    instruction="""
    {task_type}がtaskの場合、以下の形式で実行計画を作成してください：
    
    [
        {
            "step": 1,
            "name": "入力解析",
            "description": "ユーザー要求の詳細分析",
            "tool": null
        },
        {
            "step": 2, 
            "name": "計算実行",
            "description": "数値計算の実行",
            "tool": "calculator"
        },
        {
            "step": 3,
            "name": "結果整形", 
            "description": "結果の整形と表示",
            "tool": null
        }
    ]
    
    chatの場合は空配列[]を返してください。
    """,
    output_key="execution_plan"
)
```

### 3.3 ExecutorAgent（実行）
```python
from google.adk.tools import MCPToolset

# MCPツール定義
mcp_tools = MCPToolset(
    connect_params={
        "type": "stdio",
        "command": ["python", "-m", "mcp_tools.calculator"]
    }
)

executor_agent = LlmAgent(
    name="TaskExecutor",
    model="gemini-2.0-flash-exp",
    instruction="""
    {execution_plan}に従ってタスクを実行してください。
    
    各ステップを順次実行し、必要に応じてツールを使用してください。
    実行結果を詳細に記録し、最終結果を返してください。
    """,
    tools=[mcp_tools],
    output_key="result"
)
```

### 3.4 メインエージェント（統合）
```python
from google.adk.agents import SequentialAgent

maidel_system = SequentialAgent(
    name="Maidel2.2System",
    description="キャラクター対話型AIエージェントシステム",
    sub_agents=[
        conversation_agent,
        planner_agent, 
        executor_agent
    ]
)
```

## 4. MCP実装設計

### 4.1 Calculator MCP Tool
```python
# mcp_tools/calculator.py
import json
from typing import Any, Dict

class CalculatorMCPServer:
    def __init__(self):
        self.tools = {
            "calculate": {
                "description": "基本的な数学計算を実行",
                "parameters": {
                    "expression": {"type": "string", "description": "計算式"}
                }
            }
        }
    
    def list_tools(self) -> Dict[str, Any]:
        return {"tools": self.tools}
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "calculate":
            try:
                expression = arguments.get("expression", "")
                # 安全な計算実行（eval使用時は制限付き）
                result = self._safe_calculate(expression)
                return {
                    "success": True,
                    "result": result
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    def _safe_calculate(self, expression: str) -> float:
        # 安全な数式評価実装
        # （制限付きeval or math parser使用）
        pass
```

### 4.2 Memory MCP Tool
```python
# mcp_tools/memory.py
class MemoryMCPServer:
    def __init__(self):
        self.session_memory = {}
        self.tools = {
            "store_memory": {
                "description": "セッション内情報の保存", 
                "parameters": {
                    "key": {"type": "string"},
                    "value": {"type": "string"}
                }
            },
            "retrieve_memory": {
                "description": "セッション内情報の取得",
                "parameters": {
                    "key": {"type": "string"}
                }
            }
        }
```

## 5. React UI実装設計

### 5.1 メインコンポーネント構成
```
App.tsx
├── CharacterDisplay.tsx      # キャラクター立ち絵表示
├── ChatInterface.tsx         # チャット画面
│   ├── MessageList.tsx       # メッセージ履歴
│   ├── MessageInput.tsx      # 入力欄
│   └── TypingIndicator.tsx   # 処理中表示
├── PlanVisualizer.tsx        # 実行計画可視化
│   ├── PlanFlow.tsx          # フロー表示
│   ├── StepCard.tsx          # ステップカード
│   └── ProgressBar.tsx       # 進捗バー
└── StatusBar.tsx             # ステータス表示
```

### 5.2 PlanVisualizerコンポーネント
```typescript
interface PlanVisualizerProps {
  plan: ExecutionPlan | null;
  onStepClick?: (stepId: string) => void;
}

const PlanVisualizer: React.FC<PlanVisualizerProps> = ({ plan }) => {
  return (
    <div className="plan-visualizer">
      <h3>実行計画</h3>
      {plan && (
        <div className="plan-flow">
          {plan.steps.map((step, index) => (
            <StepCard
              key={step.id}
              step={step}
              isActive={index === plan.currentStepIndex}
              isConnected={index < plan.steps.length - 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};
```

### 5.3 Electron-ADK通信
```typescript
// Electron Main Process
import { spawn } from 'child_process';

class ADKProcessManager {
  private process: any;
  
  async startADKProcess() {
    this.process = spawn('python', ['-m', 'adk_server']);
    
    this.process.stdout.on('data', (data: Buffer) => {
      const message = JSON.parse(data.toString());
      // Rendererに結果送信
      mainWindow.webContents.send('adk-response', message);
    });
  }
  
  async sendToADK(message: string) {
    const input = JSON.stringify({ message });
    this.process.stdin.write(input + '\n');
  }
}
```

## 6. デプロイメント設計

### 6.1 ビルド構成
```json
{
  "scripts": {
    "build": "npm run build:react && npm run build:electron",
    "build:react": "react-scripts build",
    "build:electron": "electron-builder",
    "pack": "electron-builder --dir",
    "dist": "electron-builder"
  },
  "build": {
    "appId": "com.maidel.app",
    "productName": "Maidel 2.2",
    "directories": {
      "output": "dist"
    },
    "files": [
      "build/**/*",
      "public/electron.js",
      "adk_server/**/*"
    ]
  }
}
```

### 6.2 Python環境同梱
```
app/
├── resources/
│   ├── python/          # Pythonランタイム
│   ├── adk_server/      # ADKサーバーコード
│   └── mcp_tools/       # MCPツール群
├── build/               # Reactビルド結果
└── electron.js          # Electronメインプロセス
```

## 7. パフォーマンス考慮事項

### 7.1 レスポンス時間最適化
- ADKエージェント処理: 並列化可能部分の検討
- MCP通信: 接続プール使用
- UI更新: 必要な部分のみ再描画

### 7.2 メモリ管理
- セッション状態の適切なクリーンアップ
- 大きなデータのストリーミング処理
- Electronプロセス分離による安定性確保

## 8. エラーハンドリング

### 8.1 ADKエージェントエラー
```python
try:
    result = await agent.run(session)
except ADKException as e:
    error_response = {
        "error": True,
        "message": f"エージェント処理エラー: {e}",
        "type": "agent_error"
    }
```

### 8.2 UI エラー表示
```typescript
const ErrorBoundary: React.FC = ({ children }) => {
  // エラー境界実装
  // ADKエラー、通信エラーなどのハンドリング
};
```

---

**作成日**: 2025年9月19日  
**作成者**: クロコ（執事AI）  
**バージョン**: 1.0
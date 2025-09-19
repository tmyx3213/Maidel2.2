# Maidel 2.2 実装計画書

## 1. 開発フェーズ概要

### Phase 0: 環境構築・準備 (1-2日)
### Phase 1: MCPツール基盤 (2-3日)  
### Phase 2: ADKエージェント実装 (3-4日)
### Phase 3: Electron+React統合 (2-3日)
### Phase 4: 可視化機能実装 (2日)
### Phase 5: 統合テスト・調整 (1-2日)

**総開発期間**: 約11-16日

## 2. Phase 0: 環境構築・準備

### 2.1 Claude Codeでの作業開始
```bash
# プロジェクトディレクトリ作成
mkdir maidel-2.2
cd maidel-2.2

# 基本構成作成
mkdir -p {frontend,backend,mcp_tools,docs}
```

### 2.2 必要なツール・ライブラリ調査
**Claude Codeとの対話内容例:**
```
「Maidel 2.2プロジェクトを開始します。まず、Google ADK の最新インストール方法と、
Electron + React の基本セットアップを教えてください。Windowsでの開発を想定しています。」
```

### 2.3 プロジェクト構造設計
```
maidel-2.2/
├── frontend/                 # Electron + React
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── electron.js
├── backend/                  # ADK Python
│   ├── agents/
│   │   ├── conversation.py
│   │   ├── planner.py
│   │   └── executor.py
│   ├── main.py
│   └── requirements.txt
├── mcp_tools/               # MCP実装
│   ├── calculator/
│   └── memory/
├── docs/                    # ドキュメント
└── README.md
```

### 2.4 開発環境セットアップ
- [ ] Python 3.9+ インストール確認
- [ ] Node.js 18+ インストール確認
- [ ] Google ADK インストール
- [ ] Electron開発環境構築

## 3. Phase 1: MCPツール基盤

### 3.1 基本MCPサーバー実装

#### 3.1.1 Calculator MCP Tool
**Claude Codeへの依頼:**
```
「MCPプロトコルに従った計算機能を実装してください。
- 基本四則演算対応
- 安全な数式評価（eval使用時は制限付き）
- JSON-RPC 2.0形式での通信
- stdio transport対応

参考: Model Context Protocol仕様」
```

**期待される成果物:**
```
mcp_tools/calculator/
├── __init__.py
├── server.py              # MCPサーバーメイン
├── calculator.py          # 計算ロジック
└── requirements.txt
```

#### 3.1.2 Memory MCP Tool (オプション)
**実装内容:**
- セッション内メモリ管理
- key-value形式でのデータ保存・取得
- 一時的なコンテキスト保持

### 3.2 MCP通信テスト
```python
# テスト用スクリプト
import subprocess
import json

def test_mcp_calculator():
    # MCPサーバーとの通信テスト
    proc = subprocess.Popen(['python', '-m', 'mcp_tools.calculator'], 
                          stdin=subprocess.PIPE, 
                          stdout=subprocess.PIPE)
    
    # list_tools テスト
    request = {"method": "list_tools", "params": {}}
    # call_tool テスト
    # ...
```

### 3.3 Claude Codeでのデバッグ戦略
- MCPプロトコル準拠の確認
- 計算精度テスト
- エラーハンドリング検証

## 4. Phase 2: ADKエージェント実装

### 4.1 個別エージェント作成

#### 4.1.1 ConversationAgent
**Claude Codeへの依頼:**
```
「Google ADKを使用して会話判定エージェントを作成してください。

要件:
- 入力: ユーザーメッセージ
- 出力: "chat" または "task" の分類
- モデル: gemini-2.0-flash-exp
- output_key: "task_type"

サンプル実装とテストコードも含めてください。」
```

#### 4.1.2 PlannerAgent
**実装ポイント:**
- JSON形式での実行計画出力
- ステップごとの詳細情報
- 計算タスクに特化した計画策定

#### 4.1.3 ExecutorAgent  
**実装ポイント:**
- MCPツールセット統合
- ステップ実行管理
- 結果の構造化

### 4.2 SequentialAgent統合
**Claude Codeへの依頼:**
```
「作成した3つのエージェントをSequentialAgentで統合してください。

構成:
1. ConversationAgent → PlannerAgent → ExecutorAgent
2. Shared Session Stateでの状態管理
3. エラー時の適切なハンドリング

統合テストも含めて実装してください。」
```

### 4.3 ADK サーバー実装
```python
# backend/main.py
from google.adk import Agent, Runner, SessionService
from agents.conversation import conversation_agent
from agents.planner import planner_agent  
from agents.executor import executor_agent
from google.adk.agents import SequentialAgent

class MaidelServer:
    def __init__(self):
        self.maidel_system = SequentialAgent(
            name="Maidel2.2System",
            sub_agents=[
                conversation_agent,
                planner_agent,
                executor_agent
            ]
        )
        self.session_service = SessionService()
    
    async def process_message(self, message: str) -> dict:
        session = self.session_service.create_session()
        runner = Runner(session=session)
        
        try:
            result = await runner.run(self.maidel_system, message)
            return {
                "success": True,
                "result": result.final_output,
                "state": session.state
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    server = MaidelServer()
    # stdio通信ループ実装
```

### 4.4 ADK単体テスト
- 各エージェントの個別動作確認
- 状態遷移テスト
- エラーケーステスト

## 5. Phase 3: Electron+React統合

### 5.1 Electronアプリ基盤構築

#### 5.1.1 基本Electronセットアップ
**Claude Codeへの依頼:**
```
「Electron + React + TypeScriptの基本構成を作成してください。

要件:
- React 18.x使用
- TypeScript対応
- ホットリロード対応
- Python subprocess起動機能

package.jsonとセットアップスクリプトも含めてください。」
```

#### 5.1.2 IPC通信実装
```typescript
// frontend/src/services/adkService.ts
import { ipcRenderer } from 'electron';

export class ADKService {
    static async sendMessage(message: string): Promise<any> {
        return await ipcRenderer.invoke('adk-process', message);
    }
    
    static onStateUpdate(callback: (state: any) => void) {
        ipcRenderer.on('adk-state-update', (event, state) => {
            callback(state);
        });
    }
}
```

### 5.2 React UI基盤実装

#### 5.2.1 基本コンポーネント作成
**優先順序:**
1. **App.tsx** - メインアプリケーション
2. **ChatInterface.tsx** - チャット基本機能
3. **CharacterDisplay.tsx** - キャラクター表示
4. **MessageList.tsx** - メッセージ履歴

#### 5.2.2 状態管理実装
```typescript
// frontend/src/hooks/useAppState.ts
import { useState, useCallback } from 'react';
import { ADKService } from '../services/adkService';

export const useAppState = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [currentPlan, setCurrentPlan] = useState<ExecutionPlan | null>(null);
    
    const sendMessage = useCallback(async (content: string) => {
        setIsProcessing(true);
        try {
            const response = await ADKService.sendMessage(content);
            // 状態更新処理
        } finally {
            setIsProcessing(false);
        }
    }, []);
    
    return { messages, isProcessing, currentPlan, sendMessage };
};
```

### 5.3 Electron-ADK プロセス連携
```javascript
// frontend/public/electron.js
const { spawn } = require('child_process');

class ADKProcessManager {
    constructor() {
        this.adkProcess = null;
    }
    
    async startADK() {
        this.adkProcess = spawn('python', ['-m', 'backend.main'], {
            stdio: ['pipe', 'pipe', 'pipe']
        });
        
        this.setupADKCommunication();
    }
    
    setupADKCommunication() {
        this.adkProcess.stdout.on('data', (data) => {
            const response = JSON.parse(data.toString());
            this.sendToRenderer('adk-response', response);
        });
    }
}
```

## 6. Phase 4: 可視化機能実装

### 6.1 PlanVisualizerコンポーネント

#### 6.1.1 基本UI実装
**Claude Codeへの依頼:**
```
「実行計画を可視化するReactコンポーネントを作成してください。

要件:
- フローチャート風のステップ表示
- 各ステップの状態表示（完了✅/実行中🔄/待機⏸️）
- リアルタイム更新対応
- レスポンシブデザイン

CSS ModulesまたはStyled Componentsを使用してください。」
```

#### 6.1.2 リアルタイム更新実装
```typescript
// frontend/src/components/PlanVisualizer.tsx
import React, { useEffect, useState } from 'react';
import { ADKService } from '../services/adkService';

interface PlanVisualizerProps {
    plan: ExecutionPlan | null;
}

const PlanVisualizer: React.FC<PlanVisualizerProps> = ({ plan }) => {
    const [currentStep, setCurrentStep] = useState(0);
    
    useEffect(() => {
        const unsubscribe = ADKService.onStateUpdate((state) => {
            if (state.execution_plan) {
                // 計画更新処理
                updatePlanDisplay(state);
            }
        });
        
        return unsubscribe;
    }, []);
    
    const renderStepFlow = () => {
        if (!plan) return null;
        
        return (
            <div className="plan-flow">
                {plan.steps.map((step, index) => (
                    <div key={step.id} className="step-container">
                        <StepCard 
                            step={step}
                            isActive={index === currentStep}
                            isCompleted={step.status === 'completed'}
                        />
                        {index < plan.steps.length - 1 && (
                            <div className="step-connector">→</div>
                        )}
                    </div>
                ))}
            </div>
        );
    };
    
    return (
        <div className="plan-visualizer">
            <h3>実行計画</h3>
            {renderStepFlow()}
            {plan && (
                <div className="plan-progress">
                    進捗: {currentStep + 1} / {plan.steps.length}
                </div>
            )}
        </div>
    );
};
```

### 6.2 StepCardコンポーネント
```typescript
interface StepCardProps {
    step: PlanStep;
    isActive: boolean;
    isCompleted: boolean;
}

const StepCard: React.FC<StepCardProps> = ({ step, isActive, isCompleted }) => {
    const getStatusIcon = () => {
        if (isCompleted) return '✅';
        if (isActive) return '🔄';
        return '⏸️';
    };
    
    return (
        <div className={`step-card ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
            <div className="step-header">
                <span className="step-icon">{getStatusIcon()}</span>
                <h4>{step.name}</h4>
            </div>
            <p className="step-description">{step.description}</p>
            {step.result && (
                <div className="step-result">
                    結果: {JSON.stringify(step.result)}
                </div>
            )}
        </div>
    );
};
```

### 6.3 CSS実装
```css
/* frontend/src/components/PlanVisualizer.module.css */
.plan-visualizer {
    background: #f5f5f5;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
}

.plan-flow {
    display: flex;
    align-items: center;
    overflow-x: auto;
    padding: 16px 0;
}

.step-container {
    display: flex;
    align-items: center;
    white-space: nowrap;
}

.step-card {
    background: white;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    padding: 12px;
    min-width: 200px;
    margin: 0 8px;
    transition: all 0.3s ease;
}

.step-card.active {
    border-color: #2196F3;
    box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);
}

.step-card.completed {
    border-color: #4CAF50;
    background: #f8fff8;
}

.step-connector {
    font-size: 18px;
    color: #666;
    margin: 0 8px;
}
```

## 7. Phase 5: 統合テスト・調整

### 7.1 統合テストシナリオ

#### 7.1.1 基本動作テスト
```
テストケース1: 雑談処理
入力: "こんにちは"
期待結果: 
- task_type: "chat"
- 雑談レスポンス返却
- 実行計画なし

テストケース2: 計算タスク
入力: "2 + 3 を計算して"
期待結果:
- task_type: "task" 
- 実行計画表示
- 計算結果: 5
```

#### 7.1.2 UI統合テスト
- キャラクター表示確認
- チャット入力・表示動作
- 実行計画可視化動作
- リアルタイム更新確認

### 7.2 パフォーマンス調整
- ADKエージェント応答時間測定
- UI更新頻度最適化
- メモリ使用量確認

### 7.3 エラーハンドリング改善
- ADK処理エラー時のUI表示
- 通信エラー時の再試行機能
- 異常終了時の復旧処理

## 8. Claude Codeとの効果的な協働戦略

### 8.1 フェーズ別アプローチ

#### Phase 1-2: 技術調査・基盤実装
**対話スタイル:**
```
「Google ADK の SequentialAgent について、具体的なコード例と
エージェント間通信の仕組みを教えてください。
特に、Shared Session State の使い方に注目しています。」
```

#### Phase 3-4: 実装・デバッグ
**対話スタイル:**
```
「以下のコードでエラーが発生しています。
[エラーメッセージ]
[該当コード]

ADKとElectronの統合における一般的な問題と解決策を教えてください。」
```

#### Phase 5: 最適化・改善
**対話スタイル:**
```
「現在の実装で、レスポンス時間が遅い問題があります。
ADKエージェントの並列処理や、UI更新の最適化について
アドバイスをお願いします。」
```

### 8.2 学習目標達成のためのチェックポイント

- [ ] **マルチエージェント理解**: SequentialAgent の動作原理
- [ ] **MCP連携実装**: プロトコル準拠と通信実装
- [ ] **状態管理**: ADK State ↔ React State 同期
- [ ] **リアルタイム処理**: 可視化更新の仕組み
- [ ] **エラーハンドリング**: 分散システムでの例外処理

### 8.3 トラブルシューティング戦略

#### よくある問題と対処法
1. **ADK-Electron通信エラー**
   - stdio通信の確立確認
   - JSON形式の正確性チェック
   
2. **MCPツール認識失敗**
   - MCPプロトコル仕様準拠確認
   - ツール定義の構文チェック

3. **UI更新遅延**
   - ポーリング間隔調整
   - 状態更新の最適化

## 9. 成果物・ドキュメント

### 9.1 最終成果物
- [ ] 動作するMaidel 2.2アプリケーション
- [ ] MCPツール実装一式
- [ ] ADKエージェントシステム
- [ ] 実行計画可視化機能

### 9.2 学習記録
- [ ] ADKマルチエージェント実装ノート
- [ ] MCPプロトコル実装経験記録
- [ ] Electron統合での知見まとめ
- [ ] 性能改善・デバッグログ

---

**作成日**: 2025年9月19日  
**作成者**: クロコ（執事AI）  
**対象読者**: マスター & Claude Code  
**バージョン**: 1.0
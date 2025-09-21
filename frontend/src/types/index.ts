/**
 * Maidel 2.2 Type Definitions
 */

// チャットメッセージ
export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'maidel' | 'system';
  timestamp: Date;
  taskType?: string;
  executionPlan?: any[];
  isError?: boolean;
}

// 実行ステップ
export interface PlanStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  result?: any;
  error?: string;
  tool?: string;
  estimatedTime?: string;
  dependencies?: number[];
}

// 実行計画
export interface ExecutionPlan {
  steps: PlanStep[];
  currentStepIndex: number;
  status: 'pending' | 'running' | 'completed' | 'error';
}

// ADKレスポンス
export interface ADKResponse {
  success: boolean;
  message?: string;
  task_type?: string;
  execution_plan?: any[];
  result?: string;
  error?: string;
  error_type?: string;
  session_state?: Record<string, any>;
  agent_result?: string;
}

// ADK状態
export interface ADKStatus {
  isRunning: boolean;
  pid?: number;
}

// キャラクター状態
export interface CharacterState {
  expression: 'normal' | 'happy' | 'thinking' | 'surprised' | 'error';
  isProcessing: boolean;
}

// アプリケーション設定
export interface AppConfig {
  theme: 'light' | 'dark' | 'auto';
  characterImage: string;
  debugMode: boolean;
}
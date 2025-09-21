import React, { useState, useEffect } from 'react';
import './App.css';
import CharacterDisplay from './components/CharacterDisplay.tsx';
import ChatInterface from './components/ChatInterface.tsx';
import PlanVisualizer from './components/PlanVisualizer.tsx';
import StatusBar from './components/StatusBar.tsx';
import { ChatMessage, ExecutionPlan, ADKResponse } from './types';

// Electron API の型定義
declare global {
  interface Window {
    electronAPI: {
      sendToADK: (message: string) => Promise<{ success: boolean; error?: string }>;
      getADKStatus: () => Promise<{ isRunning: boolean; pid?: number }>;
      restartADK: () => Promise<{ success: boolean }>;
      onADKResponse: (callback: (response: ADKResponse) => void) => void;
      onADKError: (callback: (error: any) => void) => void;
      removeAllListeners: (channel: string) => void;
    };
  }
}

const App: React.FC = () => {
  // 状態管理
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentPlan, setCurrentPlan] = useState<ExecutionPlan | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [adkStatus, setAdkStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | undefined>(undefined);

  // 初期化
  useEffect(() => {
    // ADK応答の監視
    if (window.electronAPI) {
      window.electronAPI.onADKResponse((response: ADKResponse) => {
        console.log('ADK Response received:', response);

        if (response.success) {
          // 成功レスポンス処理
          const newMessage: ChatMessage = {
            id: Date.now().toString(),
            content: response.result || '処理が完了しました',
            sender: 'maidel',
            timestamp: new Date(),
            taskType: response.task_type,
            executionPlan: response.execution_plan
          };

          setMessages(prev => [...prev, newMessage]);
          setAdkStatus('connected');
          setLastUpdate(new Date());

          // 実行計画の更新
          if (response.execution_plan && Array.isArray(response.execution_plan)) {
            const plan: ExecutionPlan = {
              steps: response.execution_plan.map((step, index) => ({
                id: step.step_id?.toString() || index.toString(),
                name: step.name || `ステップ ${index + 1}`,
                description: step.description || '',
                status: 'completed',
                result: step.result
              })),
              currentStepIndex: response.execution_plan.length - 1,
              status: 'completed'
            };
            setCurrentPlan(plan);
          }
        } else {
          // エラーレスポンス処理
          const errorMessage: ChatMessage = {
            id: Date.now().toString(),
            content: `エラーが発生しました: ${response.error || '不明なエラー'}`,
            sender: 'system',
            timestamp: new Date(),
            isError: true
          };
          setMessages(prev => [...prev, errorMessage]);
          setAdkStatus('error');
        }

        setIsProcessing(false);
      });

      // ADKエラーの監視
      window.electronAPI.onADKError((error) => {
        console.error('ADK Error:', error);
        setConnectionError(error.error || 'ADK接続エラー');
        setAdkStatus('error');
        setIsProcessing(false);
      });

      // ADK状態チェック
      checkADKStatus();
    } else {
      // Electron環境でない場合（開発中のブラウザ表示等）
      setConnectionError('Electron環境が必要です');
    }

    // 初期メッセージ
    const welcomeMessage: ChatMessage = {
      id: 'welcome',
      content: 'こんにちは！私はまいでるです。計算や雑談、何でもお気軽にお話しくださいね！',
      sender: 'maidel',
      timestamp: new Date()
    };
    setMessages([welcomeMessage]);

    // クリーンアップ
    return () => {
      if (window.electronAPI) {
        window.electronAPI.removeAllListeners('adk-response');
        window.electronAPI.removeAllListeners('adk-error');
      }
    };
  }, []);

  // ADK状態チェック
  const checkADKStatus = async () => {
    if (window.electronAPI) {
      try {
        setAdkStatus('connecting');
        const status = await window.electronAPI.getADKStatus();
        if (status.isRunning) {
          setAdkStatus('connected');
          setConnectionError(null);
          setLastUpdate(new Date());
        } else {
          setAdkStatus('disconnected');
        }
      } catch (error) {
        console.error('ADK status check failed:', error);
        setAdkStatus('error');
      }
    }
  };

  // メッセージ送信
  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isProcessing) return;

    // ユーザーメッセージを追加
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: content.trim(),
      sender: 'user',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    // 処理開始
    setIsProcessing(true);
    setCurrentPlan(null);

    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.sendToADK(content);
        if (!result.success) {
          throw new Error(result.error || 'メッセージ送信に失敗しました');
        }
      } else {
        throw new Error('Electron API が利用できません');
      }
    } catch (error) {
      console.error('Send message error:', error);

      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        content: `送信エラー: ${error instanceof Error ? error.message : '不明なエラー'}`,
        sender: 'system',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsProcessing(false);
    }
  };

  // ADK再起動
  const handleRestartADK = async () => {
    if (window.electronAPI) {
      try {
        setAdkStatus('connecting');
        setConnectionError('ADKを再起動中...');
        await window.electronAPI.restartADK();
        setTimeout(checkADKStatus, 2000);
      } catch (error) {
        console.error('ADK restart failed:', error);
        setAdkStatus('error');
        setConnectionError('ADK再起動に失敗しました');
      }
    }
  };

  return (
    <div className="maidel-container">
      {/* ステータスバー */}
      <StatusBar
        adkStatus={adkStatus}
        lastUpdate={lastUpdate}
      />

      {/* メインコンテンツエリア */}
      <div className="app-main">
        {/* キャラクター表示エリア */}
        <div className="app-character">
          <CharacterDisplay isProcessing={isProcessing} />
        </div>

        {/* チャット・可視化エリア */}
        <div className="app-content">
          {/* 実行計画可視化 */}
          {currentPlan && (
            <div className="app-visualizer">
              <PlanVisualizer plan={currentPlan} />
            </div>
          )}

          {/* チャットインターフェース */}
          <div className="app-chat">
            <ChatInterface
              messages={messages}
              onSendMessage={handleSendMessage}
              isProcessing={isProcessing}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
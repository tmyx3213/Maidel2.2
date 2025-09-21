import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';
import { ChatMessage } from '../types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isProcessing: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  onSendMessage,
  isProcessing
}) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 新しいメッセージが追加されたときに自動スクロール
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 入力フィールドにフォーカスを維持
  useEffect(() => {
    if (!isProcessing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isProcessing]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isProcessing) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSenderIcon = (sender: ChatMessage['sender']) => {
    switch (sender) {
      case 'user':
        return '👤';
      case 'maidel':
        return '🤖';
      case 'system':
        return '⚙️';
      default:
        return '💬';
    }
  };

  const getSenderName = (sender: ChatMessage['sender']) => {
    switch (sender) {
      case 'user':
        return 'あなた';
      case 'maidel':
        return 'まいでる';
      case 'system':
        return 'システム';
      default:
        return '不明';
    }
  };

  return (
    <div className="chat-interface">
      {/* メッセージリスト */}
      <div className="chat-messages maidel-scrollbar">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.sender} ${message.isError ? 'error' : ''} fade-in`}
          >
            <div className="message-header">
              <span className="message-sender">
                <span className="sender-icon">{getSenderIcon(message.sender)}</span>
                <span className="sender-name">{getSenderName(message.sender)}</span>
              </span>
              <span className="message-timestamp">
                {formatTimestamp(message.timestamp)}
              </span>
            </div>
            <div className="message-content">
              {message.content}
            </div>
            {/* タスク種別表示 */}
            {message.taskType && (
              <div className="message-metadata">
                <span className="task-type">
                  {message.taskType === 'task' ? '🧮 タスク' : '💭 雑談'}
                </span>
              </div>
            )}
          </div>
        ))}

        {/* 処理中インジケーター */}
        {isProcessing && (
          <div className="message maidel processing fade-in">
            <div className="message-header">
              <span className="message-sender">
                <span className="sender-icon">🤖</span>
                <span className="sender-name">まいでる</span>
              </span>
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 入力エリア */}
      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="chat-input-form">
          <div className="input-wrapper">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isProcessing ? '処理中です...' : 'メッセージを入力してください（例: 2+3を計算して）'}
              disabled={isProcessing}
              className="maidel-input"
              maxLength={500}
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isProcessing}
              className="send-button maidel-button"
            >
              {isProcessing ? '⏳' : '📤'}
            </button>
          </div>
          <div className="input-help">
            <span className="char-count">
              {inputValue.length}/500
            </span>
            <span className="input-hint">
              Enter で送信 | Shift+Enter で改行
            </span>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
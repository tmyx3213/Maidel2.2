import React from 'react';
import './StatusBar.css';

interface StatusBarProps {
  adkStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastUpdate?: Date;
  version?: string;
}

const StatusBar: React.FC<StatusBarProps> = ({
  adkStatus,
  lastUpdate,
  version = '2.2.0'
}) => {
  const getStatusIcon = (status: typeof adkStatus) => {
    switch (status) {
      case 'connected':
        return '🟢';
      case 'connecting':
        return '🟡';
      case 'disconnected':
        return '🔴';
      case 'error':
        return '⚠️';
      default:
        return '❓';
    }
  };

  const getStatusText = (status: typeof adkStatus) => {
    switch (status) {
      case 'connected':
        return 'ADK接続済み';
      case 'connecting':
        return 'ADK接続中...';
      case 'disconnected':
        return 'ADK未接続';
      case 'error':
        return 'ADK接続エラー';
      default:
        return '状態不明';
    }
  };

  const formatLastUpdate = (date?: Date) => {
    if (!date) return '未更新';
    return date.toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="status-bar">
      <div className="status-section">
        <div className="status-item adk-status">
          <span className={`status-indicator ${adkStatus}`}>
            {getStatusIcon(adkStatus)}
          </span>
          <span className="status-text">{getStatusText(adkStatus)}</span>
        </div>

        {lastUpdate && (
          <div className="status-item last-update">
            <span className="update-icon">🕐</span>
            <span className="update-text">
              最終更新: {formatLastUpdate(lastUpdate)}
            </span>
          </div>
        )}
      </div>

      <div className="info-section">
        <div className="status-item version">
          <span className="version-icon">📦</span>
          <span className="version-text">v{version}</span>
        </div>

        <div className="status-item app-name">
          <span className="app-icon">🤖</span>
          <span className="app-text">Maidel 2.2</span>
        </div>
      </div>
    </div>
  );
};

export default StatusBar;
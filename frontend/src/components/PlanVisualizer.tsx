import React from 'react';
import './PlanVisualizer.css';
import { ExecutionPlan, PlanStep } from '../types';

interface PlanVisualizerProps {
  plan: ExecutionPlan;
  onStepClick?: (stepId: string) => void;
}

const PlanVisualizer: React.FC<PlanVisualizerProps> = ({ plan, onStepClick }) => {
  const getStatusIcon = (status: PlanStep['status']) => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'running':
        return '🔄';
      case 'error':
        return '❌';
      case 'pending':
      default:
        return '⏸️';
    }
  };

  const getStatusColor = (status: PlanStep['status']) => {
    switch (status) {
      case 'completed':
        return '#27ae60';
      case 'running':
        return '#f39c12';
      case 'error':
        return '#e74c3c';
      case 'pending':
      default:
        return '#95a5a6';
    }
  };

  const getToolIcon = (tool?: string) => {
    switch (tool) {
      case 'calculator':
        return '🧮';
      case 'memory':
        return '💾';
      default:
        return '⚙️';
    }
  };

  const handleStepClick = (stepId: string) => {
    if (onStepClick) {
      onStepClick(stepId);
    }
  };

  return (
    <div className="plan-visualizer">
      {/* ヘッダー */}
      <div className="plan-header">
        <h3 className="plan-title">
          <span className="title-icon">📋</span>
          実行計画
        </h3>
        <div className="plan-status">
          <span className={`status-badge ${plan.status}`}>
            {getStatusIcon(plan.status)}
            {plan.status === 'completed' ? '完了' :
             plan.status === 'running' ? '実行中' :
             plan.status === 'error' ? 'エラー' : '待機中'}
          </span>
        </div>
      </div>

      {/* 進捗バー */}
      <div className="progress-container">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{
              width: `${(plan.steps.filter(s => s.status === 'completed').length / plan.steps.length) * 100}%`
            }}
          />
        </div>
        <div className="progress-text">
          {plan.steps.filter(s => s.status === 'completed').length} / {plan.steps.length} ステップ完了
        </div>
      </div>

      {/* ステップフロー */}
      <div className="steps-flow">
        {plan.steps.map((step, index) => (
          <React.Fragment key={step.id}>
            {/* ステップカード */}
            <div
              className={`step-card ${step.status} ${index === plan.currentStepIndex ? 'current' : ''}`}
              onClick={() => handleStepClick(step.id)}
              style={{ '--status-color': getStatusColor(step.status) } as React.CSSProperties}
            >
              <div className="step-header">
                <div className="step-number">{index + 1}</div>
                <div className="step-icons">
                  <span className="status-icon">{getStatusIcon(step.status)}</span>
                  {step.tool && (
                    <span className="tool-icon" title={`ツール: ${step.tool}`}>
                      {getToolIcon(step.tool)}
                    </span>
                  )}
                </div>
              </div>

              <div className="step-content">
                <h4 className="step-name">{step.name}</h4>
                <p className="step-description">{step.description}</p>

                {/* 実行時間表示 */}
                {step.estimatedTime && (
                  <div className="step-time">
                    <span className="time-icon">⏱️</span>
                    <span className="time-text">{step.estimatedTime}</span>
                  </div>
                )}

                {/* 結果表示 */}
                {step.result && (
                  <div className="step-result">
                    <span className="result-label">結果:</span>
                    <span className="result-value">
                      {typeof step.result === 'object'
                        ? JSON.stringify(step.result, null, 2)
                        : String(step.result)
                      }
                    </span>
                  </div>
                )}

                {/* エラー表示 */}
                {step.error && (
                  <div className="step-error">
                    <span className="error-icon">⚠️</span>
                    <span className="error-text">{step.error}</span>
                  </div>
                )}
              </div>

              {/* 依存関係インジケーター */}
              {step.dependencies && step.dependencies.length > 0 && (
                <div className="step-dependencies">
                  <span className="dependencies-label">依存:</span>
                  {step.dependencies.map(depId => (
                    <span key={depId} className="dependency-badge">
                      {depId}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* コネクター */}
            {index < plan.steps.length - 1 && (
              <div className="step-connector">
                <div className="connector-line"></div>
                <div className="connector-arrow">▶</div>
              </div>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* サマリー */}
      <div className="plan-summary">
        <div className="summary-stats">
          <div className="stat-item">
            <span className="stat-icon">⏱️</span>
            <span className="stat-value">
              {plan.steps.reduce((total, step) => {
                if (step.estimatedTime) {
                  const match = step.estimatedTime.match(/(\d+)/);
                  return total + (match ? parseInt(match[1], 10) : 0);
                }
                return total;
              }, 0)}秒
            </span>
            <span className="stat-label">予想時間</span>
          </div>
          <div className="stat-item">
            <span className="stat-icon">🛠️</span>
            <span className="stat-value">
              {plan.steps.filter(step => step.tool).length}
            </span>
            <span className="stat-label">ツール使用</span>
          </div>
          <div className="stat-item">
            <span className="stat-icon">✅</span>
            <span className="stat-value">
              {Math.round((plan.steps.filter(s => s.status === 'completed').length / plan.steps.length) * 100)}%
            </span>
            <span className="stat-label">完了率</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlanVisualizer;
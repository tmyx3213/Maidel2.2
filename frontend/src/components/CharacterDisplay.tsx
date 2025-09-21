import React from 'react';
import './CharacterDisplay.css';

interface CharacterDisplayProps {
  isProcessing: boolean;
}

const CharacterDisplay: React.FC<CharacterDisplayProps> = ({ isProcessing }) => {
  return (
    <div className="character-display">
      {/* キャラクター画像エリア */}
      <div className="character-image-container">
        <div className={`character-image ${isProcessing ? 'processing' : ''}`}>
          {/* 実際のキャラクター画像がない場合のプレースホルダー */}
          <div className="character-placeholder">
            <div className="character-avatar">
              <div className="character-face">
                <div className="character-eyes">
                  <div className={`eye left ${isProcessing ? 'blinking' : ''}`}></div>
                  <div className={`eye right ${isProcessing ? 'blinking' : ''}`}></div>
                </div>
                <div className="character-mouth">
                  <div className={`mouth ${isProcessing ? 'talking' : ''}`}></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 処理中インジケーター */}
        {isProcessing && (
          <div className="processing-indicator">
            <div className="processing-dots">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
            <span className="processing-text">考え中...</span>
          </div>
        )}
      </div>

      {/* キャラクター情報 */}
      <div className="character-info">
        <h2 className="character-name">まいでる</h2>
        <p className="character-title">AI デスクトップアシスタント</p>
        <div className="character-status">
          <div className={`status-indicator ${isProcessing ? 'active' : 'idle'}`}></div>
          <span className="status-text">
            {isProcessing ? '処理中' : '待機中'}
          </span>
        </div>
      </div>

      {/* デコレーション */}
      <div className="character-decoration">
        <div className="floating-particle particle-1"></div>
        <div className="floating-particle particle-2"></div>
        <div className="floating-particle particle-3"></div>
      </div>
    </div>
  );
};

export default CharacterDisplay;
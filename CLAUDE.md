# CLAUDE.md

このファイルはMaidel 2.2プロジェクトでのClaude Code作業時の設定とガイダンスを提供します。

## プロジェクト概要

**Maidel 2.2** - ADKマルチエージェント学習用AIデスクトップアプリケーション
- 目的: Google ADK + MCP による階層的エージェント構成の習得
- UI: Electron + React (ギャルゲー風キャラクター対話)
- Backend: Python ADK + MCPツール
- 対象OS: Windows

## プロジェクト構造

```
maidel-2.2/
├── frontend/             # Electron + React UI
│   ├── src/components/   # React コンポーネント
│   ├── src/services/     # ADK通信サービス
│   └── public/          # Electron メインプロセス
├── backend/             # ADK Python エージェント
│   ├── agents/          # 各エージェント実装
│   └── main.py         # ADKサーバーメイン
├── mcp_tools/          # MCPツール実装
│   ├── calculator/     # 計算機能
│   └── memory/        # メモリ管理
└── docs/              # 設計ドキュメント
```

## コア実装コマンド

### 開発環境
- `npm install`: フロントエンド依存関係インストール
- `pip install -r requirements.txt`: Python依存関係インストール
- `npm run dev`: 開発サーバー起動
- `python -m backend.main`: ADKサーバー起動

### Electron
- `npm run build`: プロダクションビルド
- `npm run pack`: パッケージ化
- `npm run dist`: 配布用ビルド

### テスト
- `npm test`: Reactテスト実行
- `pytest`: Python テスト実行

## 技術制約・ルール

### ADKエージェント実装
- **階層構造必須**: SequentialAgent > ConversationAgent > PlannerAgent > ExecutorAgent
- **状態管理**: Shared Session State で output_key 使用
- **通信方式**: ADK標準の状態ベース通信のみ
- **モデル**: gemini-2.0-flash-exp 使用
- **MCPツール**: MCPToolset でラップして tools 配列に追加

### MCP実装
- **プロトコル準拠**: JSON-RPC 2.0 必須
- **通信方式**: stdio transport 使用
- **セキュリティ**: 計算式のサニタイゼーション必須
- **エラーハンドリング**: 全ツールで統一フォーマット

### React/Electron
- **TypeScript**: 全ファイルでTypeScript使用
- **状態管理**: React hooks (useState, useEffect)
- **通信**: IPC経由でADKプロセス連携
- **UI**: CSS Modules または Styled Components
- **ファイル構成**: コンポーネント単位での分割

## 実装優先度

### Phase 1: 基盤 (最優先)
1. MCPCalculatorツール実装・テスト
2. ADK各エージェント個別実装
3. SequentialAgent統合

### Phase 2: UI統合
1. Electron基本構成
2. React基本コンポーネント
3. ADK通信インターフェース

### Phase 3: 可視化
1. PlanVisualizerコンポーネント
2. リアルタイム状態更新
3. エラー表示機能

## コーディング規約

### Python
- **型ヒント**: 全関数で必須
- **docstring**: 全クラス・関数に記述
- **命名**: snake_case, クラスはPascalCase
- **エラー**: 具体的な例外クラス使用
- **インポート**: typing モジュール活用

### TypeScript/React
- **インターフェース**: 全Props・Stateで定義
- **命名**: camelCase, コンポーネントはPascalCase
- **分割**: 1ファイル1コンポーネント原則
- **hooks**: カスタムフック で共通ロジック分離

### 共通
- **コメント**: 実装理由を重視、Whatではなく Why
- **テスト**: 新機能は必ずテストコード追加
- **Git**: 機能単位でのコミット、明確なメッセージ

## 禁止事項

### セキュリティ
- MCPツールでの eval() 直接使用禁止
- 外部API呼び出し（MVP範囲外）
- ファイルシステム操作（MVP範囲外）

### アーキテクチャ
- エージェント間の直接通信禁止（State経由必須）
- localStorage/sessionStorage使用禁止
- Electron外での実行を想定した実装禁止

### スコープ
- UI装飾・アニメーション（MVP範囲外）
- 永続化機能（MVP範囲外）
- 複雑な計算以外のタスク（MVP範囲外）

## 学習目標達成確認

各実装で以下を確認：
- [ ] ADK SequentialAgent動作理解
- [ ] エージェント間Shared State通信理解
- [ ] MCPプロトコル準拠実装理解
- [ ] Electron-Python プロセス間通信理解
- [ ] リアルタイムUI更新実装理解

## デバッグ・トラブルシューティング

### よくある問題
1. **ADK通信エラー**: stdio パイプ確認、JSON形式チェック
2. **MCPツール認識失敗**: list_tools(), call_tool() 実装確認
3. **React状態更新遅延**: useEffect依存配列、ポーリング間隔確認
4. **Electron起動失敗**: Pythonパス、権限設定確認

### デバッグ手順
1. 個別コンポーネント単体テスト
2. ADKエージェント単独動作確認
3. MCP通信ログ確認
4. 統合テスト実行

## 重要な設計決定

- **エージェント階層**: 意図理解 > 計画策定 > 実行制御
- **状態キー**: task_type, execution_plan, final_result
- **可視化方式**: フローチャート + ステータス表示
- **エラー処理**: 各層での適切なフォールバック

## 成功基準

MVP完成の定義：
1. 自然言語での計算依頼受付
2. 3階層エージェント による処理実行
3. 実行計画のリアルタイム可視化
4. 計算結果の正確な表示

---
**注記**: このファイルはClaude Codeが参照する設定ファイルです。プロジェクト進行に応じて更新してください。
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
- [x] ADK SequentialAgent動作理解 ✅ **完全達成**
- [x] エージェント間Shared State通信理解 ✅ **完全達成**
- [x] MCPプロトコル準拠実装理解 ✅ **完全達成**
- [ ] Electron-Python プロセス間通信理解 ⏳ **基盤準備済み**
- [ ] リアルタイムUI更新実装理解 ❌ **未着手**

## デバッグ・トラブルシューティング

### よくある問題
1. **ADK通信エラー**: stdio パイプ確認、JSON形式チェック
2. **MCPツール認識失敗**: list_tools(), call_tool() 実装確認
   - **重要**: MCPToolset統合はWindows環境で失敗する可能性が高い
   - Unicode/async問題により直接実装での回避が必要
3. **ADK仕様不明**: 公式ドキュメント不足のため、Web検索でGitHub調査が必要
4. **React状態更新遅延**: useEffect依存配列、ポーリング間隔確認
5. **Electron起動失敗**: Pythonパス、権限設定確認

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

## 📄 セッション引き継ぎ情報

### 🎯 **現在の実装状況** (2025年9月19日時点)

**実装完了度: 約 60%** - バックエンドコアシステム完全動作達成 ✅

**✅ 完全実装済み (Phase 0-2.5):**
- ADK マルチエージェントシステム (3階層)
  - ConversationAgent: 意図理解・タスク分類
  - PlannerAgent: 実行計画策定
  - ExecutorAgent: タスク実行制御
- Google ADK v1.14.1 + SequentialAgent 統合
- セッション管理 (正しいADK API使用)
- 基本計算機能 (四則演算・数学関数)
- stdio通信基盤 (Electron連携準備)
- エラーハンドリング・状態管理

**⚠️ 既知の技術課題:**
1. **MCPToolset統合** - Windows環境Unicode/async問題により `simple_calculate` で回避中
2. **フロントエンド未実装** - Electron + React 完全未着手

### 🚀 **次セッション開始時の作業指針**

**即座に開始可能な状態:**
```bash
# 動作確認コマンド (必要に応じて実行)
cd C:\Maidel2.2
py -m backend.main --stdio
# テスト入力: {"message": "2+3を計算して"}
# 期待出力: 2+3 = 5 計算が完了いたしました。
```

**次の実装ターゲット: Phase 3**
1. Electron 基本構成作成
2. React UI コンポーネント実装
3. IPC通信システム (ADK-Electron連携)
4. PlanVisualizer コンポーネント

### 📁 **重要ファイル所在**

**コアシステム:**
- `backend/main.py` - ADK SequentialAgent統合メイン
- `backend/agents/` - 3層エージェント実装
- `mcp_tools/calculator/` - MCPツール実装

**設計ドキュメント:**
- `PROGRESS.md` - 詳細な実装進捗・技術メモ
- `要件定義書.md`, `技術仕様書.md` - プロジェクト仕様
- `実装計画書.md`, `エージェント設計書.md` - 設計詳細

### 💡 **実装時の重要なポイント**

**Google ADK 仕様理解について:**
- ADKは最近リリースされたGoogleのAIエージェント作成キット
- 公式ドキュメントが少ないため、**Web検索でGitHub等を調査する必要がある**
- `pip install google-adk` で導入可能
- SequentialAgent, LlmAgent の実装パターンをGitHubリポジトリから学習

**ADK実装で確立済みのパターン:**
- セッション作成: `InMemorySessionService` + 動的作成
- コンテンツ形式: `google.genai.types.Content` 必須
- 状態管理: `output_key` による状態共有 (task_type, execution_plan, final_result)

**回避済み問題・技術課題:**
- **MCPToolset統合失敗** - Windows環境でUnicode/async問題が発生
  - `from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset` でエラー
  - 回避策: `simple_calculate` による直接実装で代替
  - 今後の課題: 本格的なMCP連携の解決が必要
- Session API の正しい使用方法確立
- Windows環境での文字化け対応

### 🔧 **開発環境要件**
- Python 3.x + `pip install google-adk`
- Node.js (Electron用 - 未セットアップ)
- Windows 10/11 対応

---
**注記**: このファイルはClaude Codeが参照する設定ファイルです。セッション引き継ぎ時は上記情報を確認してください。
**最終更新**: 2025年9月19日 (セッション区切り)
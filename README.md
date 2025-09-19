# Maidel 2.2

ADK マルチエージェント学習用AIデスクトップアプリケーション

## 概要

Google ADK + MCP による階層的エージェント構成を学習するためのプロジェクト。
ギャルゲー風UIでキャラクターと対話しながら、マルチエージェントシステムによるタスク処理を体験できます。

## 技術スタック

- **フロントエンド**: Electron + React + TypeScript
- **バックエンド**: Python + Google ADK
- **ツール連携**: Model Context Protocol (MCP)
- **対象OS**: Windows

## エージェント構成

```
Maidel2.2System (SequentialAgent)
├── ConversationAgent  # 意図理解（雑談 vs タスク）
├── PlannerAgent       # 実行計画策定
└── ExecutorAgent      # MCP ツール実行
    ├── Calculator Tool
    └── Memory Tool
```

## プロジェクト構造

```
maidel-2.2/
├── frontend/           # Electron + React UI
├── backend/            # ADK Python エージェント
├── mcp_tools/          # MCPツール実装
├── docs/              # 設計ドキュメント
└── PROGRESS.md        # 開発進捗記録
```

## 開発状況

現在Phase 0（環境構築）完了、Phase 1（MCPツール実装）に向けて準備中

詳細は [PROGRESS.md](./PROGRESS.md) を参照

## セットアップ

### 必要環境
- Python 3.9+
- Node.js 18+
- Git

### インストール
```bash
# リポジトリクローン
git clone https://github.com/tmyx3213/Maidel2.2.git
cd Maidel2.2

# Python環境
pip install google-adk

# フロントエンド環境（Phase 3で実装予定）
# cd frontend && npm install
```

## 学習目標

- [ ] ADK SequentialAgent による階層的エージェント構成
- [ ] MCP プロトコルによるツール連携
- [ ] エージェント間状態管理
- [ ] Electron-Python プロセス間通信
- [ ] リアルタイム実行計画可視化

## ライセンス

MIT License

## 作成者

- 設計・実装: クロコ（執事AI）+ Claude Code
- プロジェクト監督: マスター
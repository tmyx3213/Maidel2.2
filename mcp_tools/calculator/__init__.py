"""
Calculator MCP Tool for Maidel 2.2

MCPプロトコルに準拠した数学計算ツール
安全な数式評価とエラーハンドリングを提供
"""

from .server import CalculatorMCPServer

__version__ = "1.0.0"
__all__ = ["CalculatorMCPServer"]
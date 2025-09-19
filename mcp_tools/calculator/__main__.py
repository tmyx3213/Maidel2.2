"""
Calculator MCP Server エントリーポイント

python -m mcp_tools.calculator でサーバーを起動
"""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())
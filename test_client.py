"""Мини MCP-клиент: поднимает server.py по stdio, перечисляет инструменты и
вызывает их. Доказывает, что сервер рабочий, без Claude Desktop.

Запуск:  python test_client.py
"""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Инструменты сервера:")
            for t in tools.tools:
                print(f"  • {t.name} — {(t.description or '').splitlines()[0]}")

            print("\nkb_info:")
            r = await session.call_tool("kb_info", {})
            print(" ", r.content[0].text)

            print("\nsearch_docs('How much does the Pro plan cost?', k=3):")
            r = await session.call_tool("search_docs",
                                        {"query": "How much does the Pro plan cost?", "k": 3})
            print(r.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())

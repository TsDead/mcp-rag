"""MCP-сервер поверх Qdrant-базы знаний.

Отдаёт инструменты, которые может вызвать любой MCP-клиент (Claude Desktop,
Claude Code, Cursor…): семантический поиск, индексация, статус БД. Плюс ресурс
kb://info. Рассуждает клиентская модель — сервер только предоставляет данные.

Запуск (stdio, для локальных клиентов):   python server.py
"""

from mcp.server.mcpserver import MCPServer

import kb

mcp = MCPServer("rag-qdrant-kb")


@mcp.tool()
def search_docs(query: str, k: int = 4) -> str:
    """Семантический поиск по базе знаний (Qdrant, HNSW).
    Возвращает top-k релевантных фрагментов со score близости.

    Args:
        query: поисковый запрос на естественном языке.
        k: сколько фрагментов вернуть (1–8).
    """
    hits = kb.search(query, max(1, min(k, 8)))
    if not hits:
        return "База знаний пуста. Сначала вызови ingest_text."
    return "\n\n".join(f"[{i+1}] (score {s:.3f}) {t}"
                       for i, (s, _, t) in enumerate(hits))


@mcp.tool()
def ingest_text(text: str) -> str:
    """Проиндексировать документ в базу знаний (векторная БД Qdrant).
    Заменяет прошлое содержимое. Возвращает число чанков.
    """
    n = kb.ingest(text)
    return f"Проиндексировано {n} чанков в Qdrant." if n else "Пустой документ."


@mcp.tool()
def kb_info() -> dict:
    """Статус векторной БД: режим, коллекция, число точек, индекс."""
    return kb.info()


@mcp.resource("kb://info")
def kb_resource() -> str:
    """Ресурс со статусом базы знаний (для клиентов, читающих resources)."""
    i = kb.info()
    return (f"Vector store: {i['mode']} · collection={i['collection']} · "
            f"points={i['points']} · index={i['index']}")


if __name__ == "__main__":
    kb.ensure_seeded()   # засеять демо-документом, если база пустая
    mcp.run()            # транспорт stdio по умолчанию

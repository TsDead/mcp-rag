# MCP · RAG over Qdrant

An **MCP server** (Model Context Protocol) that exposes a Qdrant-backed knowledge
base as tools any MCP client can call — Claude Desktop, Claude Code, Cursor, etc.
The client's model does the reasoning; this server just provides retrieval.

**Stack:** Python · MCP (official SDK) · Qdrant (vector DB, HNSW) · fastembed (local embeddings)

## Why MCP

Ordinary tool use lives *inside* one app. **MCP** standardizes tools behind a
server so any compatible client connects and uses them out of the box — write the
server once, and its tools show up in Claude Desktop/Code without extra glue. Few
candidates build MCP servers, so it's a strong differentiator.

## Tools exposed

| Tool | What it does |
|---|---|
| `search_docs(query, k)` | Semantic search over the KB (Qdrant · HNSW) → top-k passages with similarity scores |
| `ingest_text(text)` | Index a document into the vector DB (replaces prior content) |
| `kb_info()` | Vector-store status: mode, collection, points, index |

Also a resource `kb://info`. On startup the server seeds a demo document so search works immediately.

## How it works

```
document ─► chunk ─► embed (fastembed, 384-dim) ─► Qdrant (HNSW · Cosine)

MCP client (Claude) ──stdio──► server.py
   │  calls search_docs("...")                 │
   └──────────── passages + scores ◄───────────┘
```

`server.py` (MCPServer + tools) · `kb.py` (chunk/embed/ingest/search) · `store.py` (Qdrant wrapper).

## Run & test

```bash
pip install -r requirements.txt
python test_client.py     # spins up the server over stdio and calls the tools
python server.py          # run the server directly (stdio transport)
```

`test_client.py` prints the tool list, `kb_info`, and a `search_docs` result — proof the server works without any client app.

## Register with a client

**Claude Code:**
```bash
claude mcp add rag-qdrant-kb -- python /absolute/path/to/mcp-rag/server.py
```

**Claude Desktop** — add to `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`):
```json
{
  "mcpServers": {
    "rag-qdrant-kb": {
      "command": "python",
      "args": ["C:/absolute/path/to/mcp-rag/server.py"]
    }
  }
}
```
Restart the client; the three tools appear. Ask it to *"search the knowledge base for the Pro plan price"* and it will call `search_docs`.

### Transports
`server.py` uses **stdio** (local process — what Claude Desktop expects). For a networked server, run `mcp.run(transport="streamable-http")` instead.

## Note
Never `print()` to stdout in the server — stdout carries the MCP protocol over stdio. Log to stderr if needed.

---
© 2026 NOVACODE · [new-coder.ru](https://new-coder.ru)

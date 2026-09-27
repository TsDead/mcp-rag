"""База знаний за MCP-сервером: чанкинг + эмбеддинги (fastembed) + Qdrant.

Тот же ретривал, что в P6 (rag-qdrant), но без LLM: MCP-сервер только ОТДАЁТ
инструменты и данные, а рассуждает клиентская модель (Claude). Поэтому здесь
нет вызова Groq — только поиск по векторной БД.

ВАЖНО: ничего не печатать в stdout — по нему идёт MCP-протокол (stdio).
"""

from pathlib import Path

import numpy as np

import store

_model = None


def _embedder():
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        _model = TextEmbedding("BAAI/bge-small-en-v1.5")   # 384-мерные, локально
    return _model


def _embed(texts):
    vecs = np.array(list(_embedder().embed(texts)), dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / np.clip(norms, 1e-9, None)


def _chunk(text, size=90, overlap=20):
    words = text.split()
    if not words:
        return []
    out, i, step = [], 0, max(1, size - overlap)
    while i < len(words):
        out.append(" ".join(words[i:i + size]))
        i += step
    return out


def ingest(text: str) -> int:
    """Проиндексировать документ в Qdrant. Возвращает число чанков."""
    chunks = _chunk(text)
    if not chunks:
        return 0
    vecs = _embed(chunks)
    store.reset(vecs.shape[1])
    store.upsert(chunks, vecs)
    return len(chunks)


def search(query: str, k: int = 4):
    """Топ-k чанков по близости через HNSW. Возвращает [(score, id, text)]."""
    if not store.count():
        return []
    return store.search(_embed([query])[0], k)


def info() -> dict:
    return store.info()


def ensure_seeded():
    """Если база пустая — засеять демо-документом, чтобы поиск сразу работал."""
    if store.count() == 0:
        sample = Path(__file__).parent / "eval" / "sample_doc.txt"
        if sample.exists():
            ingest(sample.read_text(encoding="utf-8"))

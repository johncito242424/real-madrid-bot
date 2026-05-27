"""
rag.py — Pipeline de recuperación y generación para el RAG del Real Madrid.

Flujo:
    1. retrieve  — embed query + búsqueda Qdrant + reranking híbrido + filtro
    2. generate  — construye prompt con contexto e invoca el LLM
    3. ask       — orquesta ambas fases y devuelve la respuesta final
"""

import re
import time

from ollama import Client
from qdrant_client import QdrantClient

import config

ollama = Client(host="http://localhost:11434")

# RETRIEVAL


def embed_query(query: str) -> list[float]:
    """
    Vectoriza la pregunta con el prefijo instructivo de nomic-embed-text.
    'search_query' es para consultas; 'search_document' es para ingesta.
    Usar el prefijo correcto mejora significativamente la similitud.
    """
    resp = ollama.embeddings(
        model=config.EMBED_MODEL,
        prompt=f"search_query: {query}"
    )
    return resp["embedding"]


def search_qdrant(vector: list[float]) -> list:
    """Búsqueda semántica: devuelve los N chunks más similares de Qdrant."""
    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    result = client.query_points(
        collection_name=config.COLLECTION_NAME,
        query=vector,
        limit=config.RETRIEVAL_LIMIT
    )
    return result.points


def hybrid_rerank(hits: list, query: str) -> list[dict]:
    """
    Reranking híbrido = score semántico (Qdrant) + bonus lexical.
    El bonus premia chunks que contienen los mismos términos de la pregunta,
    compensando casos donde la similitud semántica no captura palabras clave exactas.
    El filtro por SCORE_THRESHOLD elimina resultados poco relevantes.
    """
    terms = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 3]

    scored = []
    for hit in hits:
        content = hit.payload.get("content", "")
        bonus   = sum(config.LEXICAL_BONUS for t in terms if t in content.lower())
        scored.append({
            "source":     hit.payload.get("source", "?"),
            "page":       hit.payload.get("page"),
            "content":    content,
            "similarity": hit.score + bonus,
        })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return [c for c in scored if c["similarity"] >= config.SCORE_THRESHOLD]


def retrieve(query: str) -> list[dict]:
    """
    Orquesta el proceso completo de recuperación:
    embed → search → rerank → filter
    """
    t0     = time.perf_counter()
    vector = embed_query(query)
    hits   = search_qdrant(vector)
    chunks = hybrid_rerank(hits, query)
    print(f"[RETRIEVAL] {len(chunks)} chunks relevantes ({time.perf_counter() - t0:.2f}s)")
    return chunks


# Generacion


def build_context(chunks: list[dict]) -> str:
    """Ensambla los chunks recuperados en un bloque de texto para el prompt."""
    lines = []
    for i, c in enumerate(chunks, 1):
        lines.append(f"--- Fragmento {i} (fuente: {c['source']}, p.{c['page']}) ---")
        lines.append(c["content"])
    return "\n".join(lines)


def generate(query: str, chunks: list[dict]) -> str:
    """
    Construye el prompt RAG e invoca el LLM.
    El sistema instruve al modelo a responder SOLO con el contexto recuperado,
    evitando que invente información no presente en los documentos.
    """
    system = (
        "Eres un asistente experto en el Real Madrid Club de Fútbol. "
        "Responde EXCLUSIVAMENTE con la información presente en el contexto. "
        "Responde siempre en español, de forma clara y directa. "
        "Si la respuesta no aparece en el contexto, di: "
        "'No encontré esa información en los documentos.'"
    )
    user = (
        f"Contexto recuperado:\n{build_context(chunks)}\n\n"
        f"Pregunta: {query}\n\nRespuesta:"
    )

    t0   = time.perf_counter()
    resp = ollama.chat(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ]
    )
    print(f"[GENERATION] LLM respondió en {time.perf_counter() - t0:.2f}s")
    return resp["message"]["content"]



# PIPELINE COMPLETO

def ask(query: str) -> str:
    """
    Función principal del RAG. Recibe una pregunta y devuelve la respuesta.
    Es la única función que bot.py necesita importar.
    """
    chunks = retrieve(query)
    if not chunks:
        return "No encontré información relevante sobre esa pregunta en los documentos."
    return generate(query, chunks)
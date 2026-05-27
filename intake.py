"""
intake.py — Pipeline de ingesta de documentos PDF para el RAG del Real Madrid.

Flujo:
    1. extract_pages  — extrae texto página a página con PyMuPDF
    2. chunk_pages    — fragmenta el texto con solapamiento semántico
    3. ingest         — genera embeddings y los sube a Qdrant en lotes
    4. ingest_all     — recorre la carpeta /data e ingesta todos los PDFs
"""

import os
import uuid
import hashlib

import fitz
import ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

import config

# EXTRACCIÓN

def extract_pages(pdf_path: str) -> list[dict]:
    """Extrae el texto de cada página del PDF. Retorna lista de {page, text}."""
    doc = fitz.open(pdf_path)
    return [
        {"page": i + 1, "text": page.get_text()}
        for i, page in enumerate(doc)
    ]


def pdf_hash(pdf_path: str) -> str:
    """SHA-256 del archivo binario. Sirve como ID estable del documento."""
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

# CHUNKING

def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Divide cada página en fragmentos de tamaño controlado.
    El solapamiento preserva contexto entre chunks consecutivos.
    Retorna lista de {page, chunk_index, content}.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = []
    for page in pages:
        for idx, text in enumerate(splitter.split_text(page["text"])):
            chunks.append({
                "page":        page["page"],
                "chunk_index": idx,
                "content":     text,
            })
    return chunks


# QDRANT

def ensure_collection(client: QdrantClient) -> None:
    """Crea la colección en Qdrant si no existe todavía."""
    if not client.collection_exists(config.COLLECTION_NAME):
        print(f"  → Creando colección '{config.COLLECTION_NAME}'...")
        client.create_collection(
            collection_name=config.COLLECTION_NAME,
            vectors_config=VectorParams(
                size=config.VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )

# PIPELINE DE INGESTA


def ingest(pdf_path: str, batch_size: int = 50) -> None:
    """
    Ingesta completa de un PDF: extrae → fragmenta → embeddings → upsert.
    El upsert en lotes evita timeouts en documentos grandes.
    Los IDs son determinísticos (uuid5) para permitir re-ingesta segura.
    """
    filename = os.path.basename(pdf_path)
    doc_hash = pdf_hash(pdf_path)
    print(f"\n[INGEST] {filename}  (hash: {doc_hash[:12]}...)")

    pages  = extract_pages(pdf_path)
    print(f"  → {len(pages)} páginas extraídas")

    chunks = chunk_pages(pages)
    print(f"  → {len(chunks)} chunks generados")

    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    ensure_collection(client)

    # El prefijo "search_document:" es el prompt instructivo de nomic-embed-text
    print(f"  → Generando embeddings con '{config.EMBED_MODEL}'...")
    points = []
    for chunk in chunks:
        resp = ollama.embeddings(
            model=config.EMBED_MODEL,
            prompt=f"search_document: {chunk['content']}"
        )
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, filename + chunk["content"]))
        points.append(PointStruct(
            id=point_id,
            vector=resp["embedding"],
            payload={
                "source":        filename,
                "document_hash": doc_hash,
                "page":          chunk["page"],
                "chunk_index":   chunk["chunk_index"],
                "content":       chunk["content"],
            }
        ))

    for start in range(0, len(points), batch_size):
        batch = points[start: start + batch_size]
        client.upsert(collection_name=config.COLLECTION_NAME, points=batch)
        print(f"  → Subidos puntos {start + 1}–{start + len(batch)}")

    print(f"[INGEST] ✓ {len(points)} puntos indexados\n")


def ingest_all(data_dir: str = config.DATA_DIR) -> None:
    """Recorre data_dir e ingesta todos los archivos .pdf encontrados."""
    pdfs = [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.lower().endswith(".pdf")
    ]
    if not pdfs:
        print(f"[!] No se encontraron PDFs en '{data_dir}'")
        return

    print(f"[INGEST ALL] {len(pdfs)} PDFs encontrados en '{data_dir}'")
    for pdf_path in pdfs:
        ingest(pdf_path)
    print("[INGEST ALL] ✓ Ingesta completa.")





# PUNTO DE ENTRADA

if __name__ == "__main__":
    ingest_all()
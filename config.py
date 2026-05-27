# Base de datos vectorial 
QDRANT_HOST     = "localhost"
QDRANT_PORT     = 6333
COLLECTION_NAME = "real_madrid"
VECTOR_SIZE     = 768

# Modelos Ollama 
EMBED_MODEL     = "nomic-embed-text"
LLM_MODEL = "llama3.2:3b"

# Chunking 
CHUNK_SIZE      = 900
CHUNK_OVERLAP   = 200

#Recuperación 
RETRIEVAL_LIMIT = 4
SCORE_THRESHOLD = 0.60
LEXICAL_BONUS   = 0.03

# Datos
DATA_DIR        = "./data"
# Real Madrid Bot 

Chatbot conversacional 100% local basado en arquitectura RAG que responde preguntas sobre el Real Madrid Club de Futbol. Este ChatBot funciona a traves de Telegram.

---

## Estructura del ChatBot

El flujo completo del ChatBot es:
1. El usuario envía una pregunta por Telegram
2. `bot.py` recibe el mensaje y llama a `rag.ask()`
3. `rag.py` convierte la pregunta en un vector con `nomic-embed-text`
4. Qdrant busca los chunks más similares en la colección
5. Se aplica reranking híbrido (semántico + lexical)
6. El LLM genera una respuesta basada únicamente en los chunks recuperados
7. La respuesta llega al usuario en Telegram


## Herramientas usadas

| Herramienta | Función |
|-------------|---------|
| **Docker** | Contenedores para Qdrant y Ollama |
| **Qdrant** | Base de datos vectorial para almacenar embeddings |
| **Ollama** | Servidor de modelos de IA local |
| **nomic-embed-text** | Modelo de embeddings (768 dimensiones) |
| **llama3.2:3b** | LLM para generación de respuestas |
| **ngrok** | Túnel seguro para el webhook de Telegram |
| **python-telegram-bot** | Librería para el bot de Telegram |
| **PyMuPDF (fitz)** | Extracción de texto de PDFs |
| **LangChain** | Chunking inteligente de texto |

## Estructura del proyecto
```
proyfinal/
├── bot.py              # Bot de Telegram (webhook)
├── rag.py              # Pipeline RAG (retrieve + generate)
├── intake.py           # Ingesta de PDFs a Qdrant
├── config.py           # Configuración centralizada
├── docker-compose.yml  # Contenedores Qdrant + Ollama
├── data/               # PDFs del Real Madrid (no incluidos en el repo)
└── README.md
```



## Requisitos

- Python 3.12
- Docker Desktop
- ngrok (cuenta gratuita)
- Telegram

### Librerias Python
```
pip install pymupdf langchain-text-splitters qdrant-client ollama python-telegram-bot[webhooks]
```

## Instalación y uso

### 1. Clonar el repositorio
```bash
git clone https://github.com/johncito242424/real-madrid-bot.git
cd real-madrid-bot
```

### 2. Agregar PDFs
Crea una carpeta `data/` y agrega PDFs sobre el Real Madrid.

### 3. Levantar los contenedores
```bash
docker-compose up -d
```

### 4. Descargar los modelos
```bash
docker exec ollama_server ollama pull nomic-embed-text
docker exec ollama_server ollama pull llama3.2:3b
```

### 5. Ingestar los documentos
```bash
py -3.12 intake.py
```

### 6. Iniciar ngrok
```bash
ngrok http 8443
```

### 7. Actualizar la URL de ngrok en bot.py
En `bot.py`, actualiza la variable `NGROK_URL` con la URL que te da ngrok.

### 8. Correr el bot
```bash
py -3.12 bot.py
```

---

## La Configuracion

Todos los parametros estan centralizados en `config.py`:

```python
COLLECTION_NAME = "real_madrid"   # Nombre de la coleccion en Qdrant
EMBED_MODEL     = "nomic-embed-text"  # Modelo de embeddings
LLM_MODEL       = "llama3.2:3b"   # Modelo de lenguaje
CHUNK_SIZE      = 900             # Tamaño de cada chunk
CHUNK_OVERLAP   = 200             # Solapamiento entre chunks
RETRIEVAL_LIMIT = 4               # Chunks a recuperar por consulta
SCORE_THRESHOLD = 0.60            # Umbral minimo de similitud
```

---

## Equipo
Juan Jose Restrepo-Juan Manuel Reyes 
Proyecto final — Programación III 
Universidad Tecnológica de Pereira (UTP)

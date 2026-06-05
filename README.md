# Real Madrid Bot 
<img width="503" height="551" alt="image" src="https://github.com/user-attachments/assets/2ffb0953-5d4c-49dd-8b94-f82a251e8778" />


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

¿Que hace cada archivo? 
config.py —  Es el archivo de configuración centralizada de todo el proyecto. Contiene las variables que todos los demás archivos necesitan: la dirección y puerto de Qdrant, el nombre de la colección donde se guardan los vectores, el tamaño del vector, los nombres de los modelos de embedding y LLM, los parámetros de chunking como tamaño y solapamiento, y los parámetros de recuperación como cuántos chunks buscar y cuál es el score mínimo aceptable. La ventaja de tenerlo centralizado es que si necesitas cambiar algo, lo cambias en un solo lugar y afecta todo el sistema.

Intake.py-Es el script que se corre una sola vez para preparar los datos. Su trabajo es tomar los PDFs del Real Madrid que están en la carpeta data/, extraer el texto página por página con PyMuPDF, dividir ese texto en fragmentos pequeños llamados chunks con solapamiento para no perder contexto, convertir cada chunk en un vector de 768 números usando nomic-embed-text via Ollama, y subir todos esos vectores a Qdrant en lotes. También tiene una función ingest_all() que procesa todos los PDFs de la carpeta automáticamente, y los IDs de los vectores son determinísticos para evitar duplicados si se re-ingesta el mismo archivo.

rag.py-Es el corazón del sistema. Implementa el pipeline completo de Retrieval-Augmented Generation. Cuando recibe una pregunta, primero la convierte en un vector usando nomic-embed-text con el prefijo search_query:, luego busca en Qdrant los chunks más similares usando similitud coseno, aplica un reranking híbrido que combina el score semántico de Qdrant con un bonus lexical por coincidencia exacta de palabras, filtra los resultados por un umbral mínimo de similitud, construye un prompt con el contexto recuperado y la pregunta, y finalmente llama al LLM llama3.2:3b para generar la respuesta. La función pública ask() orquesta todo este proceso.

bot.py-Es la interfaz del sistema con el usuario. Implementa el bot de Telegram usando webhook a través de ngrok. Tiene tres handlers: el comando /start que muestra el mensaje de bienvenida, el handler de texto que detecta saludos y responde con el menú de opciones o llama a rag.ask() para responder preguntas, y el handler de documentos que acepta PDFs enviados por el usuario, los descarga, los guarda en data/ y llama a intake.ingest() para indexarlos automáticamente en Qdrant sin necesidad de reiniciar nada.

docker-compose.yml Es el archivo que define la infraestructura del proyecto. Configura dos servicios: Qdrant, la base de datos vectorial que corre en el puerto 6333 y guarda sus datos en ./qdrant_storage para que persistan entre reinicios, y Ollama, el servidor de modelos de IA que corre en el puerto 11434 y guarda los modelos descargados en ./ollama_data. Ollama tiene configurada la GPU Nvidia para acelerar la inferencia. Con un solo comando docker-compose up -d levanta todo el sistema listo para usar.


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

Uso: ¿Como prender el bot?:
1. Abre Docker Desktop y espera a que la ballena deje de moverse.
<img width="1278" height="720" alt="image" src="https://github.com/user-attachments/assets/bd5ae11b-f93d-4108-9b97-67a4a85786f4" />

2. Abre CMD y navega a la carpeta: 
<img width="375" height="30" alt="image" src="https://github.com/user-attachments/assets/4132d865-fa9b-421f-abc7-5c90ddbbc915" />

3. Levanta los contenedores:
<img width="635" height="34" alt="image" src="https://github.com/user-attachments/assets/5072d42e-b321-4977-b731-77517dc564c9" />

4. Abre el CMD de ngrok y corre:
<img width="618" height="68" alt="image" src="https://github.com/user-attachments/assets/40997fc1-f594-4241-92d6-dac69c70dc27" />

5. Si la URL de ngrok cambió, actualiza NGROK_URL en bot.py, guarda y haz push.

6. En CMD dentro de proyfinal corre el bot:
<img width="543" height="32" alt="image" src="https://github.com/user-attachments/assets/35c98c83-5a08-4d1e-93c0-a0b5b4df554c" />

   

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

Fecha de entrega: 3 de Junio, 2026

"""
bot.py — Bot de Telegram para el chatbot RAG del Real Madrid.
Usa webhook a través de ngrok para recibir mensajes de Telegram.
Permite adjuntar PDFs directamente en el chat para ingesta automática.
"""

import os
import logging
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from rag import ask
from intake import ingest
import config

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────

TOKEN     = "8959811102:AAEhnCt8p4srBjvKhFQgoP4r2lA99UwB2zU"
NGROK_URL = "https://flanked-speculate-award.ngrok-free.dev"
PORT      = 8443
PATH      = "/webhook"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING
)


# ─────────────────────────────────────────────────────────────
# HANDLERS
# ─────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "¡Hala Madrid! 🤍\n\n"
        "Soy tu asistente del Real Madrid. Puedes preguntarme sobre:\n"
        "• Historia del club\n"
        "• Jugadores y leyendas\n"
        "• Títulos y estadísticas\n"
        "• Temporadas y partidos\n\n"
        "También puedes enviarme un PDF y lo agregaré a mi base de conocimiento. 📄\n\n"
        "¿Qué quieres saber?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.message.text
    await update.message.reply_text("Buscando en los documentos... ⚽")

    try:
        respuesta = ask(query)
    except Exception as e:
        respuesta = f"Ocurrió un error al procesar tu pregunta: {e}"

    await update.message.reply_text(respuesta)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recibe un PDF, lo guarda en data/ y lo ingesta automáticamente en Qdrant."""
    document = update.message.document

    if not document.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("Solo acepto archivos PDF. 📄")
        return

    await update.message.reply_text(f"Recibí '{document.file_name}'. Procesando... ⏳")

    try:
        # Descargar el archivo desde Telegram
        file = await context.bot.get_file(document.file_id)
        os.makedirs(config.DATA_DIR, exist_ok=True)
        pdf_path = os.path.join(config.DATA_DIR, document.file_name)

        # Guardar en disco
        await file.download_to_drive(pdf_path)

        # Ingestar en Qdrant
        ingest(pdf_path)

        await update.message.reply_text(
            f"✅ '{document.file_name}' indexado correctamente. "
            f"Ya puedes hacerme preguntas sobre su contenido."
        )

    except Exception as e:
        await update.message.reply_text(f"Error al procesar el PDF: {e}")


# ─────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=PATH,
        webhook_url=f"{NGROK_URL}/{TOKEN}"
    )
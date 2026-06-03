"""
bot.py — Este es el bot de Telegram para el chatbot RAG del Real Madrid.
Usa webhook a través de ngrok para recibir los mensajes de Telegram.
"""

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from rag import ask

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



# HANDLERS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "¡Hala Madrid y nada más! 🤍\n\n"
        "Soy tu asistente del Real Madrid. Puedes preguntarme sobre:\n"
        "• La historia del club\n"
        "• Los jugadores y las leyendas\n"
        "• Sus títulos y estadísticas\n"
        "• Temporadas y partidos\n\n"
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


# PUNTO DE ENTRADA

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=PATH,
        webhook_url=f"{NGROK_URL}{PATH}"
    )
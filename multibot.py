#!/usr/bin/env python3
import asyncio
import logging
import os
from threading import Thread

from flask import Flask
from groq import Groq
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from bot.config import GROQ_API_KEY, TOKEN
from bot.handlers.media import handle_media
from bot.utils.messaging import safe_edit

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """Eres un asistente de consultas informativas y enciclopédicas. Sigues estas normas AL PIE DE LA LETRA:

1. SOLO respondes preguntas sobre: personas, lugares, eventos históricos, tecnología, ciencia, conceptos, organizaciones, productos, fenómenos naturales y temas enciclopédicos.

2. RESPUESTAS CORTAS: máximo 4 líneas. Sin introducciones como "claro", "por supuesto", "con gusto". Ve directo al punto.

3. FORMATO FIJO — siempre responde exactamente así:
📌 [Tema]
[Respuesta en 2-3 líneas con los datos más importantes]

4. SI piden: código, bots, poemas, canciones, traducciones, recetas, consejos personales, tareas, redacciones o cualquier cosa que NO sea información enciclopédica — responde EXACTAMENTE esto:
⚠️ Este comando es solo para consultas informativas. Usa el chat normal para otras cosas.

5. SIN opiniones sobre política, religión, personas vivas controversiales. Solo hechos verificables.

6. IDIOMA: responde SIEMPRE en español sin importar el idioma de la pregunta.

7. SIN inventar: si no tienes información precisa responde: ❌ No tengo información precisa sobre ese tema.

8. SIN saludos, despedidas ni preguntas de seguimiento. Solo la respuesta y ya.

9. SIN formato markdown como **negrita** o _cursiva_. Solo texto plano con emojis.

10. NO respondas preguntas sobre ti mismo como qué IA eres, en qué te basas, quién te creó o cómo funcionas. Responde EXACTAMENTE: ⚠️ Este comando es solo para consultas informativas.

11. NO respondas sobre comandos de terminal, IPs, pings, código, configuraciones de red ni técnicas informáticas prácticas. Solo información enciclopédica sobre conceptos, no instrucciones de uso."""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola! Envíame un enlace de TikTok, Instagram o Facebook.\n"
        "Escribe find <cancion> para buscar en SoundCloud.\n"
        "Usa /wiki <consulta> para buscar información."
    )


async def cmd_wiki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not groq_client:
        await update.message.reply_text("❌ Servicio de consultas no disponible.")
        return

    consulta = " ".join(context.args).strip() if context.args else ""
    if not consulta:
        await update.message.reply_text(
            "📖 Uso: /wiki <consulta>\n"
            "Ejemplo: /wiki que es Linux\n"
            "Ejemplo: /wiki quien creo YouTube"
        )
        return

    msg = await update.message.reply_text("🔍 Consultando...")

    try:
        def llamar_groq():
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": consulta}
                ],
                temperature=0.3,
                max_completion_tokens=500,
                stream=False,
            )
            return completion.choices[0].message.content

        respuesta = await asyncio.to_thread(llamar_groq)
        await safe_edit(msg, respuesta[:4000])
        logger.info(f"Wiki consultado: {consulta[:50]}")

    except Exception as e:
        err = str(e)
        logger.error(f"Groq error: {e}")
        if "429" in err or "quota" in err.lower() or "rate" in err.lower():
            await safe_edit(msg, "⏳ Demasiadas consultas. Intenta en 30 segundos.")
        else:
            await safe_edit(msg, "❌ No se pudo procesar la consulta. Intenta de nuevo.")


def main():
    logger.info("Actualizando yt-dlp...")
    os.system("pip install -U yt-dlp --quiet")
    logger.info("yt-dlp actualizado.")

    Thread(target=lambda: Flask(__name__).run(host='0.0.0.0', port=7860), daemon=True).start()
    req = HTTPXRequest(connection_pool_size=8, read_timeout=300, write_timeout=300, connect_timeout=30, pool_timeout=30)
    app = Application.builder().token(TOKEN).base_url("https://multi-api-production.up.railway.app/bot").request(req).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wiki",  cmd_wiki))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_media))
    print("Bot corriendo...")
    app.run_polling(timeout=60)


if __name__ == '__main__':
    main()

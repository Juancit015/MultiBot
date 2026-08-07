import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.groq import GroqAPIError, GroqQuotaError, ask_groq, is_available
from bot.utils.messaging import safe_edit

logger = logging.getLogger(__name__)


async def cmd_wiki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_available():
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
        respuesta = await ask_groq(consulta)
        await safe_edit(msg, respuesta[:4000])
        logger.info(f"Wiki consultado: {consulta[:50]}")

    except GroqQuotaError:
        await safe_edit(msg, "⏳ Demasiadas consultas. Intenta en 30 segundos.")
    except GroqAPIError:
        await safe_edit(msg, "❌ No se pudo procesar la consulta. Intenta de nuevo.")
    except Exception as e:
        logger.error(f"Wiki error inesperado: {str(e)[:300]}")
        await safe_edit(msg, "❌ No se pudo procesar la consulta. Intenta de nuevo.")
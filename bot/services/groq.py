import asyncio
import logging

from groq import Groq

from bot.config import (
    GROQ_API_KEY,
    GROQ_MAX_TOKENS,
    GROQ_MODEL,
    GROQ_TEMPERATURE,
)

logger = logging.getLogger(__name__)

GROQ_TIMEOUT = 60

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


class GroqQuotaError(Exception):
    """Rate limit o cuota agotada en la API de Groq."""


class GroqAPIError(Exception):
    """Error genérico de la API de Groq (no relacionado con cuota)."""


_client = Groq(api_key=GROQ_API_KEY, timeout=GROQ_TIMEOUT) if GROQ_API_KEY else None


def is_available() -> bool:
    return _client is not None


async def ask_groq(query: str) -> str:
    """Consulta a Groq. Levanta GroqQuotaError o GroqAPIError si falla."""
    if _client is None:
        raise GroqAPIError("Groq no configurado")

    def llamar():
        completion = _client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=GROQ_TEMPERATURE,
            max_completion_tokens=GROQ_MAX_TOKENS,
            stream=False,
        )
        return completion.choices[0].message.content

    for attempt in range(1, 3):
        try:
            return await asyncio.to_thread(llamar)
        except Exception as e:
            err = str(e)
            logger.error(f"Groq error: {err[:300]}")
            if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                raise GroqQuotaError("Cuota o rate limit alcanzado") from e
            if attempt == 1:
                logger.warning("Reintentando Groq tras error no-cuota...")
                await asyncio.sleep(2)
                continue
            raise GroqAPIError(err[:500]) from e

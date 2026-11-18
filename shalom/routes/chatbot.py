"""Authenticated SHALOM assistant endpoint."""

from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required

bp = Blueprint("chatbot", __name__)

SYSTEM_INSTRUCTION = """
Eres el asistente virtual de SHALOM Beauty Salon. Responde en español, con tono amable,
profesional y conciso. Ayuda con dudas generales sobre servicios, citas y el uso de la
plataforma. No inventes precios, disponibilidad ni datos de clientes; indica que consulten
el panel o contacten al salón cuando necesiten información específica. No afirmes que
realizaste acciones en la cuenta ni solicites contraseñas, datos de pago o información sensible.
""".strip()


@bp.post("/api/chatbot")
@login_required
def chat():
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify(error="El asistente no está configurado todavía."), 503

    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "")
    history = payload.get("history", [])
    if not isinstance(message, str) or not message.strip() or len(message) > 1000:
        return jsonify(error="Escribe un mensaje de hasta 1000 caracteres."), 400
    if not isinstance(history, list):
        return jsonify(error="El historial del chat no es válido."), 400

    contents = []
    for item in history[-10:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        text = item.get("text")
        if role in ("user", "assistant") and isinstance(text, str) and text.strip():
            contents.append(
                {
                    "role": "user" if role == "user" else "model",
                    "parts": [{"text": text[:1000]}],
                }
            )
    contents.append({"role": "user", "parts": [{"text": message.strip()}]})

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=current_app.config["GEMINI_MODEL"],
            contents=contents,
            config={"system_instruction": SYSTEM_INSTRUCTION},
        )
        answer = (response.text or "").strip()
    except ImportError:
        return jsonify(error="Falta instalar el cliente de IA del proyecto."), 503
    except Exception:
        current_app.logger.exception("Gemini chatbot request failed")
        return jsonify(error="No pude responder ahora. Inténtalo de nuevo en un momento."), 502

    if not answer:
        return jsonify(error="No recibí una respuesta. Inténtalo de nuevo."), 502
    return jsonify(response=answer)
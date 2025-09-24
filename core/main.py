import os
from datetime import datetime

import environ
import requests
from flask import Flask, jsonify, make_response, request

env = environ.Env()
environ.Env.read_env()

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")


def send_message(to, text):
    """Enviar mensaje de texto con WhatsApp Cloud API"""
    print(f"🔥 INTENTANDO ENVIAR MENSAJE A: {to}")
    print(f"📝 MENSAJE: {text}")
    print(f"📞 PHONE_NUMBER_ID: {PHONE_NUMBER_ID}")
    print(f"🔑 TOKEN: {WHATSAPP_TOKEN[:20]}..." if WHATSAPP_TOKEN else "❌ NO TOKEN")

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"🚀 STATUS CODE: {response.status_code}")
        print(f"📡 RESPUESTA COMPLETA: {response.text}")

        if response.status_code == 200:
            print("✅ MENSAJE ENVIADO EXITOSAMENTE")
        else:
            print("❌ ERROR AL ENVIAR MENSAJE")

        return response.json()
    except Exception as e:
        print(f"💥 EXCEPCIÓN AL ENVIAR: {e}")
        return None


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        print(f"🔍 VERIFICACIÓN - Mode: {mode}, Token: {token}")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ WEBHOOK VERIFICADO")
            return make_response(str(challenge), 200)
        else:
            print("❌ TOKEN DE VERIFICACIÓN INCORRECTO")
            return make_response("Verification token mismatch", 403)

    elif request.method == "POST":
        data = request.get_json()
        print("=" * 50)
        print("🎯 MENSAJE RECIBIDO DESDE CELULAR:")
        print(f"📱 JSON COMPLETO: {data}")

        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]

            if "messages" not in value:
                print("⚠️ No hay mensajes en el webhook")
                return jsonify({"status": "EVENT_RECEIVED"}), 200

            message = value["messages"][0]
            from_number = message["from"]
            message_text = message["text"]["body"].strip().lower()

            print(f"👤 NÚMERO QUE ENVÍA: {from_number}")
            print(f"💬 MENSAJE: '{message_text}'")
            print(f"📊 TIPO: {message['type']}")

            # RESPUESTA INMEDIATA PARA CUALQUIER MENSAJE
            print("🤖 PROCESANDO RESPUESTA...")

            if message_text in ["hola", "menu", "start"]:
                respuesta = (
                    "🎉 ¡FUNCIONA! Tu bot está respondiendo\n\n"
                    "1️⃣ Un chiste\n"
                    "2️⃣ ¿Dónde queda Lima?\n"
                    "3️⃣ Hora actual\n"
                    "4️⃣ Adiós"
                )
            elif message_text == "1":
                respuesta = (
                    "😂 ¿Por qué la computadora fue al médico? ¡Porque tenía un virus!"
                )
            elif message_text == "2":
                respuesta = (
                    "📍 Lima está en Perú, en la costa central del Pacífico 🌊🇵🇪"
                )
            elif message_text == "3":
                hora = datetime.now().strftime("%H:%M:%S")
                respuesta = f"⏰ La hora actual es {hora}"
            elif message_text == "4":
                respuesta = "👋 ¡Adiós! Que tengas un buen día."
            else:
                respuesta = (
                    f"✅ RECIBIDO: '{message_text}'\n\nEscribe 'menu' para opciones"
                )

            print(f"📤 ENVIANDO RESPUESTA: {respuesta}")
            resultado = send_message(from_number, respuesta)
            print(f"🎯 RESULTADO ENVÍO: {resultado}")

            return jsonify({"status": "EVENT_RECEIVED"}), 200

        except Exception as e:
            print(f"💥 ERROR PROCESANDO: {e}")
            import traceback

            traceback.print_exc()
            return jsonify({"status": "EVENT_RECEIVED"}), 200


@app.route("/")
def home():
    return f"""
    <h1>WhatsApp Bot Debug 🤖</h1>
    <p>VERIFY_TOKEN: {'✅' if VERIFY_TOKEN else '❌'}</p>
    <p>WHATSAPP_TOKEN: {'✅' if WHATSAPP_TOKEN else '❌'}</p>
    <p>PHONE_NUMBER_ID: {'✅' if PHONE_NUMBER_ID else '❌'}</p>
    <p>Hora: {datetime.now()}</p>
    """


@app.route("/test-send/<phone>")
def test_send(phone):
    """Ruta para probar envío manual"""
    resultado = send_message(
        phone, "🧪 MENSAJE DE PRUEBA - Si recibes esto, el bot funciona!"
    )
    return jsonify(resultado)


if __name__ == "__main__":
    print("🚀 INICIANDO BOT CON DEBUG...")
    print(f"VERIFY_TOKEN: {'✅' if VERIFY_TOKEN else '❌ FALTA'}")
    print(f"WHATSAPP_TOKEN: {'✅' if WHATSAPP_TOKEN else '❌ FALTA'}")
    print(f"PHONE_NUMBER_ID: {'✅' if PHONE_NUMBER_ID else '❌ FALTA'}")
    app.run(debug=True, host="0.0.0.0", port=5000)

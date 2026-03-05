import logging
import os
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

router = APIRouter()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
LARAVEL_API = os.getenv("LARAVEL_API", "https://laravel-ecommerce-backend-main-wenjqg.laravel.cloud/api")

sessions: dict[str, str] = {}


async def send_message(to: str, text: str) -> dict[str, Any] | None:
    """Send text message via WhatsApp Cloud API"""
    logger.info(f"Sending message to {to}: {text[:50]}...")

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
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            logger.info(f"WhatsApp API response status: {response.status_code}")

            if response.status_code == 200:
                logger.info("Message sent successfully")
                return response.json()
            else:
                logger.error(f"Failed to send message: {response.text}")
                return response.json()
    except Exception as e:
        logger.exception(f"Exception sending message: {e}")
        return None


async def fetch_products(endpoint: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Fetch products from Laravel API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LARAVEL_API}/{endpoint}", params=params, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    return data["data"]
                return []
            logger.error(f"API error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.exception(f"Exception fetching products: {e}")
        return []


def get_main_menu() -> str:
    return """👋 ¡Bienvenido a iCase Store! 🛍️

¿Qué deseas hacer?

1️⃣ Ver catálogo de productos
2️⃣ Ver ofertas y descuentos
3️⃣ Productos mejor valorados
4️⃣ Salir"""


async def handle_catalog(from_number: str) -> str:
    products = await fetch_products("ecommerce/filter-advance-product", {"page": 1, "limit": 5})

    if not products:
        return "⚠️ No se pudieron cargar los productos. Intenta más tarde."

    message = "🛍️ Catálogo iCase Store\n\n"

    for product in products:
        name = product.get("name", "Producto sin nombre")
        price = product.get("price", 0)
        url = product.get("url", "https://icase-store-peru.netlify.app/catalog")
        message += f"• {name} - S/. {price:.2f} 🔗 {url}\n"

    message += "\n¿Te interesa alguno? Visita nuestro catálogo completo 👆\n\nEscribe menu para volver"
    return message


async def handle_offers(from_number: str) -> str:
    products = await fetch_products(
        "ecommerce/filter-advance-product",
        {"options_aditional[]": "campaing", "page": 1, "limit": 5}
    )

    if not products:
        return "⚠️ No se pudieron cargar las ofertas. Intenta más tarde."

    message = "🔥 Ofertas y Descuentos\n\n"

    for product in products:
        name = product.get("name", "Producto sin nombre")
        price = product.get("price", 0)
        discount = product.get("discount", 0)
        sale_price = price - (price * discount / 100) if discount else price
        url = product.get("url", "https://icase-store-peru.netlify.app/discount/69a08d6f2a9fd")

        if discount:
            message += f"• {name} - S/. {price:.2f} S/. {sale_price:.2f} ({discount}% off) 🔗 {url}\n"
        else:
            message += f"• {name} - S/. {sale_price:.2f} 🔗 {url}\n"

    message += "\nEscribe menu para volver"
    return message


async def handle_best_rated(from_number: str) -> str:
    products = await fetch_products(
        "ecommerce/filter-advance-product",
        {"options_aditional[]": "review", "page": 1, "limit": 5}
    )

    if not products:
        return "⚠️ No se pudieron cargar los productos. Intenta más tarde."

    message = "⭐ Productos Mejor Valorados\n\n"

    for product in products:
        name = product.get("name", "Producto sin nombre")
        price = product.get("price", 0)
        rating = product.get("rating", 0)
        url = product.get("url", "https://icase-store-peru.netlify.app/catalog")
        message += f"• {name} - S/. {price:.2f} ⭐ {rating}\n🔗 {url}\n\n"

    message += "Escribe menu para volver"
    return message


def handle_exit() -> str:
    return """👋 ¡Hasta luego! Visítanos en: 🌐 https://icase-store-peru.netlify.app/

Escribe hola cuando quieras volver 😊"""


async def process_message(from_number: str, message_text: str) -> str:
    """Process incoming message and return response"""
    message_lower = message_text.strip().lower()
    current_state = sessions.get(from_number, "main_menu")

    if message_lower in ["hola", "menu", "start", "inicio"]:
        sessions[from_number] = "main_menu"
        return get_main_menu()

    if current_state == "main_menu":
        if message_lower == "1":
            sessions[from_number] = "catalog"
            return await handle_catalog(from_number)
        elif message_lower == "2":
            sessions[from_number] = "offers"
            return await handle_offers(from_number)
        elif message_lower == "3":
            sessions[from_number] = "best_rated"
            return await handle_best_rated(from_number)
        elif message_lower == "4":
            sessions[from_number] = "exited"
            return handle_exit()
        else:
            sessions[from_number] = "main_menu"
            return get_main_menu()

    sessions[from_number] = "main_menu"
    return get_main_menu()


@router.get("/webhook")
async def webhook_verification(request: Request) -> PlainTextResponse:
    """Verify webhook with Meta"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logger.info(f"Webhook verification - mode: {mode}, token: {token}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(content=str(challenge), status_code=200)

    logger.warning("Verification token mismatch")
    return PlainTextResponse(content="Verification token mismatch", status_code=403)


@router.post("/webhook")
async def webhook_handler(request: Request) -> JSONResponse:
    """Handle incoming WhatsApp messages"""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"status": "EVENT_RECEIVED"}, status_code=200)

    if "entry" not in data:
        return JSONResponse({"status": "EVENT_RECEIVED"}, status_code=200)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" not in value:
            return JSONResponse({"status": "EVENT_RECEIVED"}, status_code=200)

        message = value["messages"][0]
        from_number = message["from"]
        message_text = message.get("text", {}).get("body", "").strip()

        logger.info(f"Received message from {from_number}: {message_text}")

        if not message_text:
            return JSONResponse({"status": "EVENT_RECEIVED"}, status_code=200)

        response_text = await process_message(from_number, message_text)
        await send_message(from_number, response_text)

        return JSONResponse({"status": "EVENT_RECEIVED"}, status_code=200)

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return JSONResponse({"status": "EVENT_RECEIVED"}, status_code=200)


@router.get("/test-send/{phone}")
async def test_send(phone: str) -> JSONResponse:
    """Test endpoint for sending messages manually"""
    result = await send_message(phone, "🧪 MENSAJE DE PRUEBA - Si recibes esto, el bot funciona!")
    return JSONResponse(result or {"error": "Failed to send message"})

import logging
import os
from datetime import datetime
import uvicorn

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from core.routers import webhook

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
LARAVEL_API = os.getenv("LARAVEL_API", "https://laravel-ecommerce-backend-main-wenjqg.laravel.cloud/api")

app = FastAPI(
    title="iCase Store WhatsApp Bot",
    description="WhatsApp Business API bot for iCase Store ecommerce",
    version="1.0.0",
)

app.include_router(webhook.router)


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    return f"""
    <h1>WhatsApp Bot - iCase Store 🤖</h1>
    <p>VERIFY_TOKEN: {'✅ Configurado' if VERIFY_TOKEN else '❌ No configurado'}</p>
    <p>WHATSAPP_TOKEN: {'✅ Configurado' if WHATSAPP_TOKEN else '❌ No configurado'}</p>
    <p>PHONE_NUMBER_ID: {'✅ Configurado' if PHONE_NUMBER_ID else '❌ No configurado'}</p>
    <p>LARAVEL_API: {LARAVEL_API}</p>
    <p>Hora: {datetime.now()}</p>
    <hr>
    <p><a href="/docs">📚 Documentación API (Swagger)</a></p>
    <p><a href="/webhook">🔗 Webhook Endpoint</a></p>
    """


if __name__ == "__main__":
    logger.info("Starting iCase Store WhatsApp Bot...")
    logger.info(f"VERIFY_TOKEN: {'✅' if VERIFY_TOKEN else '❌ FALTA'}")
    logger.info(f"WHATSAPP_TOKEN: {'✅' if WHATSAPP_TOKEN else '❌ FALTA'}")
    logger.info(f"PHONE_NUMBER_ID: {'✅' if PHONE_NUMBER_ID else '❌ FALTA'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)

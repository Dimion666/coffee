from fastapi import FastAPI

from app.api.routes import router as system_router
from app.core.config import settings
from app.core.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="Coffee", version="0.1.0")
app.include_router(system_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(
        "Coffee API starting",
        extra={
            "app_env": settings.APP_ENV,
            "host": settings.APP_HOST,
            "port": settings.APP_PORT,
        },
    )

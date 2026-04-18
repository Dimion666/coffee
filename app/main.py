from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse

from app.api.routes import router as system_router
from app.core.config import settings
from app.core.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="Coffee", version="0.1.0")
app.include_router(system_router)
WEB_DIR = Path(__file__).resolve().parent / "web"


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/mobile")


@app.get("/mobile", include_in_schema=False)
async def mobile_page() -> FileResponse:
    return FileResponse(WEB_DIR / "mobile.html")


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

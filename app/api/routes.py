from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/ping")
async def ping() -> dict[str, str]:
    return {"status": "ok"}

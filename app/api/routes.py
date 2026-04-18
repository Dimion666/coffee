from fastapi import APIRouter

from app.schemas.parse import ParseTextRequest, ParseTextResponse
from app.services.address_parser_service import AddressParserService

router = APIRouter()
address_parser_service = AddressParserService()


@router.get("/api/v1/system/ping", tags=["system"])
async def ping() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/parse/text", response_model=ParseTextResponse, tags=["parse"])
async def parse_text(payload: ParseTextRequest) -> ParseTextResponse:
    points = address_parser_service.parse_route_text(payload.text)
    return ParseTextResponse(points=points)

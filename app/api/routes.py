from fastapi import APIRouter

from app.schemas.normalize import NormalizeRequest, NormalizeResponse
from app.schemas.parse import ParseTextRequest, ParseTextResponse
from app.services.address_normalizer_service import AddressNormalizerService
from app.services.address_parser_service import AddressParserService

router = APIRouter()
address_parser_service = AddressParserService()
address_normalizer_service = AddressNormalizerService()


@router.get("/api/v1/system/ping", tags=["system"])
async def ping() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/parse/text", response_model=ParseTextResponse, tags=["parse"])
async def parse_text(payload: ParseTextRequest) -> ParseTextResponse:
    points = address_parser_service.parse_route_text(payload.text)
    return ParseTextResponse(points=points)


@router.post("/api/v1/normalize", response_model=NormalizeResponse, tags=["normalize"])
async def normalize(payload: NormalizeRequest) -> NormalizeResponse:
    points = address_normalizer_service.normalize_points(payload.points)
    return NormalizeResponse(points=points)

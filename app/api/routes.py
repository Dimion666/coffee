from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.geocode import GeocodeRequest, GeocodeResponse
from app.schemas.normalize import NormalizeRequest, NormalizeResponse
from app.schemas.parse import ParseTextRequest, ParseTextResponse
from app.services.geocoding_service import GeocodingService
from app.services.address_normalizer_service import AddressNormalizerService
from app.services.address_parser_service import AddressParserService

router = APIRouter()
address_parser_service = AddressParserService()
address_normalizer_service = AddressNormalizerService()
geocoding_service = GeocodingService()


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


@router.post("/api/v1/geocode", response_model=GeocodeResponse, tags=["geocode"])
async def geocode(payload: GeocodeRequest) -> GeocodeResponse:
    if not settings.GOOGLE_MAPS_API_KEY.strip():
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_MAPS_API_KEY is required for geocoding.",
        )

    points = geocoding_service.geocode_points(payload.points)
    return GeocodeResponse(points=points)

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.demo_scenarios import DEMO_SCENARIOS
from app.core.config import settings
from app.schemas.demo import DemoScenario, DemoScenariosResponse
from app.schemas.export import ExportRequest, ExportResponse
from app.schemas.geocode import GeocodeRequest, GeocodeResponse, StartPoint
from app.schemas.normalize import NormalizeRequest, NormalizeResponse
from app.schemas.optimize import OptimizeRequest, OptimizedRouteResult
from app.schemas.parse import ParseTextRequest, ParseTextResponse
from app.schemas.process_route import ProcessRouteRequest, ProcessRouteResponse
from app.schemas.process_route_photo import ProcessRoutePhotoResponse
from app.schemas.process_route_text import ProcessRouteTextResponse
from app.schemas.upload import RoutePhotoUploadResponse
from app.services.geocoding_service import GeocodingService, ROUTE_START_POINT_ADDRESS
from app.services.address_normalizer_service import AddressNormalizerService
from app.services.address_parser_service import AddressParserService
from app.services.ocr_service import OCRService
from app.services.process_route_photo_service import ProcessRoutePhotoService
from app.services.process_route_service import ProcessRouteService
from app.services.process_route_text_service import ProcessRouteTextService
from app.services.route_photo_service import RoutePhotoService, RoutePhotoUploadError
from app.services.route_optimizer_service import RouteOptimizerService
from app.services.sheets_service import SheetsService

router = APIRouter()
address_parser_service = AddressParserService()
address_normalizer_service = AddressNormalizerService()
geocoding_service = GeocodingService()
route_optimizer_service = RouteOptimizerService(geocoding_service=geocoding_service)
sheets_service = SheetsService()
ocr_service = OCRService()
process_route_service = ProcessRouteService(
    route_optimizer_service=route_optimizer_service,
    sheets_service=sheets_service,
)
process_route_text_service = ProcessRouteTextService(
    address_parser_service=address_parser_service,
    address_normalizer_service=address_normalizer_service,
    geocoding_service=geocoding_service,
    process_route_service=process_route_service,
)
route_photo_service = RoutePhotoService()
process_route_photo_service = ProcessRoutePhotoService(
    route_photo_service=route_photo_service,
    ocr_service=ocr_service,
    process_route_text_service=process_route_text_service,
)


@router.get("/api/v1/system/ping", tags=["system"])
async def ping() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/api/v1/upload-route-photo",
    response_model=RoutePhotoUploadResponse,
    tags=["upload"],
)
async def upload_route_photo(
    file: UploadFile | None = File(default=None),
) -> RoutePhotoUploadResponse:
    try:
        return await route_photo_service.inspect_upload(file)
    except RoutePhotoUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/api/v1/demo-scenarios", response_model=DemoScenariosResponse, tags=["demo"])
async def demo_scenarios() -> DemoScenariosResponse:
    return DemoScenariosResponse(
        scenarios=[DemoScenario(**scenario) for scenario in DEMO_SCENARIOS]
    )


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
    return GeocodeResponse(
        points=points,
        start_point=StartPoint(address=ROUTE_START_POINT_ADDRESS),
    )


@router.post("/api/v1/optimize", response_model=OptimizedRouteResult, tags=["optimize"])
async def optimize(payload: OptimizeRequest) -> OptimizedRouteResult:
    if not settings.GOOGLE_MAPS_API_KEY.strip():
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_MAPS_API_KEY is required for route optimization.",
        )

    return route_optimizer_service.optimize_route(payload.points)


@router.post("/api/v1/export-sheet", response_model=ExportResponse, tags=["export"])
async def export_sheet(payload: ExportRequest) -> ExportResponse:
    try:
        return sheets_service.export_points(payload.points)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/api/v1/process-route",
    response_model=ProcessRouteResponse,
    tags=["process"],
)
async def process_route(payload: ProcessRouteRequest) -> ProcessRouteResponse:
    if not settings.GOOGLE_MAPS_API_KEY.strip():
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_MAPS_API_KEY is required for route processing.",
        )

    return process_route_service.process_route(payload.points)


@router.post(
    "/api/v1/process-route-text",
    response_model=ProcessRouteTextResponse,
    tags=["process"],
)
async def process_route_text(payload: ParseTextRequest) -> ProcessRouteTextResponse:
    if not payload.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text payload must not be empty.",
        )

    if not settings.GOOGLE_MAPS_API_KEY.strip():
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_MAPS_API_KEY is required for route processing.",
        )

    try:
        return process_route_text_service.process_route_text(payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/api/v1/process-route-photo",
    response_model=ProcessRoutePhotoResponse,
    tags=["process"],
)
async def process_route_photo(
    file: UploadFile | None = File(default=None),
) -> ProcessRoutePhotoResponse:
    if not settings.GOOGLE_MAPS_API_KEY.strip():
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_MAPS_API_KEY is required for route processing.",
        )

    try:
        return await process_route_photo_service.process_route_photo(file)
    except RoutePhotoUploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

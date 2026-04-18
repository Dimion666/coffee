from app.core.logger import get_logger
from app.schemas.process_route_text import ProcessRouteTextResponse
from app.services.address_normalizer_service import AddressNormalizerService
from app.services.address_parser_service import AddressParserService
from app.services.geocoding_service import GeocodingService
from app.services.process_route_service import ProcessRouteService

logger = get_logger(__name__)


class ProcessRouteTextService:
    """Runs text parsing and then delegates to the existing route pipeline."""

    def __init__(
        self,
        address_parser_service: AddressParserService | None = None,
        address_normalizer_service: AddressNormalizerService | None = None,
        geocoding_service: GeocodingService | None = None,
        process_route_service: ProcessRouteService | None = None,
    ) -> None:
        self.address_parser_service = address_parser_service or AddressParserService()
        self.address_normalizer_service = (
            address_normalizer_service or AddressNormalizerService()
        )
        self.geocoding_service = geocoding_service or GeocodingService()
        self.process_route_service = process_route_service or ProcessRouteService()

    def process_route_text(self, text: str) -> ProcessRouteTextResponse:
        raw_text_lines = len([line for line in text.splitlines() if line.strip()])

        parsed_points = self.address_parser_service.parse_route_text(text)
        if not parsed_points:
            raise ValueError("No valid addresses were parsed from the provided text.")

        normalized_points = self.address_normalizer_service.normalize_points(parsed_points)
        geocoded_points = self.geocoding_service.geocode_points(normalized_points)
        pipeline_result = self.process_route_service.process_route(geocoded_points)

        logger.info(
            "Process route text completed | raw_text_lines=%s parsed_points=%s success=%s",
            raw_text_lines,
            len(parsed_points),
            pipeline_result.success,
        )

        return ProcessRouteTextResponse(
            success=pipeline_result.success,
            start_point=pipeline_result.start_point,
            points=pipeline_result.points,
            optimization=pipeline_result.optimization,
            export=pipeline_result.export,
            error_message=pipeline_result.error_message,
            parsed_points_count=len(parsed_points),
            raw_text_lines=raw_text_lines,
            parse_error_message=None,
        )

from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.export import ExportResponse
from app.schemas.geocode import GeocodedPoint
from app.schemas.process_route import ProcessRouteResponse
from app.services.route_optimizer_service import RouteOptimizerService
from app.services.sheets_service import SheetsService

logger = get_logger(__name__)


class ProcessRouteService:
    """Runs optimize and export as one pipeline using existing services."""

    def __init__(
        self,
        route_optimizer_service: RouteOptimizerService | None = None,
        sheets_service: SheetsService | None = None,
    ) -> None:
        self.route_optimizer_service = route_optimizer_service or RouteOptimizerService()
        self.sheets_service = sheets_service or SheetsService()

    def _build_export_stub(self, success: bool, error_message: str | None) -> ExportResponse:
        return ExportResponse(
            success=success,
            spreadsheet_id=settings.GOOGLE_SHEETS_SPREADSHEET_ID.strip(),
            worksheet_name=settings.GOOGLE_SHEETS_WORKSHEET_NAME.strip() or "routes",
            rows_written=0,
            error_message=error_message,
        )

    def process_route(self, points: list[GeocodedPoint]) -> ProcessRouteResponse:
        optimized_result = self.route_optimizer_service.optimize_route(points)

        if not optimized_result.optimization.success:
            export_result = self._build_export_stub(
                success=False,
                error_message="Export skipped because optimization failed.",
            )
            logger.warning("Process route aborted before export because optimization failed.")
            return ProcessRouteResponse(
                success=False,
                start_point=optimized_result.start_point,
                points=optimized_result.points,
                optimization=optimized_result.optimization,
                export=export_result,
                error_message=optimized_result.optimization.error_message,
            )

        try:
            export_result = self.sheets_service.export_points(optimized_result.points)
            return ProcessRouteResponse(
                success=export_result.success,
                start_point=optimized_result.start_point,
                points=optimized_result.points,
                optimization=optimized_result.optimization,
                export=export_result,
                error_message=None,
            )
        except Exception as exc:
            logger.exception("Process route export failed after successful optimization.")
            export_result = self._build_export_stub(
                success=False,
                error_message=str(exc),
            )
            return ProcessRouteResponse(
                success=False,
                start_point=optimized_result.start_point,
                points=optimized_result.points,
                optimization=optimized_result.optimization,
                export=export_result,
                error_message=str(exc),
            )

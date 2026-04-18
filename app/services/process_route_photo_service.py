from fastapi import UploadFile

from app.core.logger import get_logger
from app.schemas.process_route_photo import ProcessRoutePhotoResponse
from app.services.ocr_service import OCRService
from app.services.process_route_text_service import ProcessRouteTextService
from app.services.route_photo_service import RoutePhotoService

logger = get_logger(__name__)


class ProcessRoutePhotoService:
    """Runs OCR for a route photo and delegates the extracted text to the text pipeline."""

    def __init__(
        self,
        route_photo_service: RoutePhotoService | None = None,
        ocr_service: OCRService | None = None,
        process_route_text_service: ProcessRouteTextService | None = None,
    ) -> None:
        self.route_photo_service = route_photo_service or RoutePhotoService()
        self.ocr_service = ocr_service or OCRService()
        self.process_route_text_service = (
            process_route_text_service or ProcessRouteTextService()
        )

    async def process_route_photo(
        self,
        file: UploadFile | None,
    ) -> ProcessRoutePhotoResponse:
        route_photo = await self.route_photo_service.read_upload(file)
        extracted_text = self.ocr_service.extract_text(route_photo.content)
        pipeline_result = self.process_route_text_service.process_route_text(
            extracted_text
        )

        logger.info(
            "Process route photo completed | filename=%s size=%s parsed_points=%s success=%s",
            route_photo.filename,
            route_photo.file_size,
            pipeline_result.parsed_points_count,
            pipeline_result.success,
        )

        return ProcessRoutePhotoResponse(
            success=pipeline_result.success,
            extracted_text=extracted_text,
            filename=route_photo.filename,
            content_type=route_photo.content_type,
            file_size=route_photo.file_size,
            parsed_points_count=pipeline_result.parsed_points_count,
            raw_text_lines=pipeline_result.raw_text_lines,
            parse_error_message=pipeline_result.parse_error_message,
            start_point=pipeline_result.start_point,
            points=pipeline_result.points,
            optimization=pipeline_result.optimization,
            export=pipeline_result.export,
            error_message=pipeline_result.error_message,
        )

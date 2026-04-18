import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.schemas.export import ExportResponse
from app.schemas.optimize import (
    OptimizationSummary,
    OptimizedPoint,
    OptimizedStartPoint,
)
from app.schemas.process_route_photo import ProcessRoutePhotoResponse


class ProcessRoutePhotoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api_key_patcher = patch.object(routes.settings, "GOOGLE_MAPS_API_KEY", "test-key")
        self.api_key_patcher.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.api_key_patcher.stop()

    def _build_response(self) -> ProcessRoutePhotoResponse:
        return ProcessRoutePhotoResponse(
            success=True,
            extracted_text=(
                "Заказ № 1001\n"
                "Контактное лицо: КОССЕ ОЛЬГА ВЛАДИМИРОВНА, тел. 0660841846\n"
                "Адрес: м. Київ, вул. Антоновича 28"
            ),
            filename="route.png",
            content_type="image/png",
            file_size=12345,
            parsed_points_count=1,
            raw_text_lines=3,
            parse_error_message=None,
            start_point=OptimizedStartPoint(
                address="Киев, Индустриальный переулок, 23",
                lat=50.44,
                lng=30.44,
            ),
            points=[
                OptimizedPoint(
                    contact_name="КОССЕ ОЛЬГА ВЛАДИМИРОВНА",
                    phone="0660841846",
                    raw_address="м. Київ, вул. Антоновича 28",
                    clean_address="м. Київ, вул. Антоновича 28",
                    full_address="м. Київ, вул. Антоновича 28",
                    status="valid",
                    is_crossed=False,
                    formatted_address="вул. Антоновича, 28, Київ, Україна, 02000",
                    lat=50.435,
                    lng=30.512,
                    geocode_status="ok",
                    geocode_precision="exact",
                    route_order=1,
                )
            ],
            optimization=OptimizationSummary(
                total_input_points=1,
                eligible_points=1,
                excluded_points=0,
                mode="google_routes_api",
                success=True,
                error_message=None,
            ),
            export=ExportResponse(
                success=True,
                spreadsheet_id="sheet-id",
                worksheet_name="routes",
                rows_written=1,
                error_message=None,
            ),
            error_message=None,
        )

    def test_process_route_photo_success(self) -> None:
        with patch(
            "app.api.routes.process_route_photo_service.process_route_photo",
            new=AsyncMock(return_value=self._build_response()),
        ):
            response = self.client.post(
                "/api/v1/process-route-photo",
                files={"file": ("route.png", b"\x89PNG\r\n\x1a\nimage", "image/png")},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertIn("Заказ № 1001", payload["extracted_text"])
        self.assertEqual(payload["parsed_points_count"], 1)
        self.assertEqual(payload["points"][0]["route_order"], 1)
        self.assertTrue(payload["export"]["success"])

    def test_process_route_photo_empty_ocr_text_returns_400(self) -> None:
        with patch(
            "app.api.routes.process_route_photo_service.process_route_photo",
            new=AsyncMock(side_effect=ValueError("OCR did not extract any text from the image.")),
        ):
            response = self.client.post(
                "/api/v1/process-route-photo",
                files={"file": ("route.png", b"\x89PNG\r\n\x1a\nimage", "image/png")},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "OCR did not extract any text from the image.",
        )


if __name__ == "__main__":
    unittest.main()

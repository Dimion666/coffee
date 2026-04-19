import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.optimize import OptimizedPoint
from app.services.sheets_service import SHEETS_HEADERS, SheetsService


class ExportEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_export_sheet_returns_success_response(self) -> None:
        payload = {
            "points": [
                {
                    "contact_name": "A",
                    "phone": "111",
                    "raw_address": "raw",
                    "clean_address": "clean",
                    "full_address": "full",
                    "status": "valid",
                    "is_crossed": False,
                    "formatted_address": "formatted",
                    "lat": 50.1,
                    "lng": 30.1,
                    "geocode_status": "ok",
                    "geocode_precision": "exact",
                    "route_order": 1,
                }
            ]
        }

        with patch(
            "app.api.routes.sheets_service.export_points",
            return_value={
                "success": True,
                "spreadsheet_id": "sheet-id",
                "worksheet_name": "routes",
                "rows_written": 1,
                "error_message": None,
            },
        ):
            response = self.client.post("/api/v1/export-sheet", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["rows_written"], 1)

    def test_export_sheet_returns_error_response(self) -> None:
        payload = {"points": []}

        with patch(
            "app.api.routes.sheets_service.export_points",
            side_effect=RuntimeError("Google Sheets credentials file not found"),
        ):
            response = self.client.post("/api/v1/export-sheet", json=payload)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["detail"],
            "Google Sheets credentials file not found",
        )

    def test_sheets_rows_use_public_columns_only(self) -> None:
        point = self._point(
            contact_name="Alice",
            phone="111",
            full_address="Full address",
            formatted_address="Formatted address",
            route_order=2,
        )

        service = SheetsService()

        self.assertEqual(
            SHEETS_HEADERS,
            [
                "route_order",
                "formatted_address",
                "phone",
                "contact_name",
                "full_address",
            ],
        )
        self.assertEqual(
            service._point_to_row(point),
            [2, "Formatted address", "111", "Alice", "Full address"],
        )

    def test_sheets_export_sorting(self) -> None:
        service = SheetsService()
        points = [
            self._point("Skipped", "333", "Skipped full", None, "skipped"),
            self._point("Second", "222", "Second full", 2),
            self._point("No order", "444", "No order full", None),
            self._point("First", "111", "First full", 1),
        ]

        sorted_points = service._sort_points_for_export(points)

        self.assertEqual(
            [point.contact_name for point in sorted_points],
            ["First", "Second", "Skipped", "No order"],
        )

    def _point(
        self,
        contact_name: str,
        phone: str,
        full_address: str,
        route_order: int | None,
        status: str = "valid",
        formatted_address: str | None = "Formatted address",
    ) -> OptimizedPoint:
        return OptimizedPoint(
            contact_name=contact_name,
            phone=phone,
            raw_address=full_address,
            clean_address=full_address,
            full_address=full_address,
            status=status,
            is_crossed=False,
            formatted_address=formatted_address,
            lat=50.1 if status == "valid" else None,
            lng=30.1 if status == "valid" else None,
            geocode_status="ok" if status == "valid" else "skipped",
            geocode_precision="exact" if status == "valid" else "unknown",
            route_order=route_order,
        )


if __name__ == "__main__":
    unittest.main()

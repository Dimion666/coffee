import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


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


if __name__ == "__main__":
    unittest.main()

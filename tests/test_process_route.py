import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class ProcessRouteEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.payload = {
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
                }
            ]
        }

    def test_process_route_returns_combined_success(self) -> None:
        with patch(
            "app.api.routes.process_route_service.process_route",
            return_value={
                "success": True,
                "start_point": {
                    "address": "Киев, Индустриальный переулок, 23",
                    "lat": 50.44,
                    "lng": 30.44,
                },
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
                ],
                "optimization": {
                    "total_input_points": 1,
                    "eligible_points": 1,
                    "excluded_points": 0,
                    "mode": "google_routes_api",
                    "success": True,
                    "error_message": None,
                },
                "export": {
                    "success": True,
                    "spreadsheet_id": "sheet-id",
                    "worksheet_name": "routes",
                    "rows_written": 1,
                    "error_message": None,
                },
                "error_message": None,
            },
        ):
            response = self.client.post("/api/v1/process-route", json=self.payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["points"][0]["route_order"], 1)
        self.assertEqual(body["export"]["rows_written"], 1)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.address_parser_service import AddressParserService


class ProcessRouteTextEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_process_route_text_returns_pipeline_result(self) -> None:
        payload = {"text": "Заказ № 1\nКонтактное лицо: A, тел. 111\nАдрес: Киев, Тестовая 1"}

        with patch(
            "app.api.routes.process_route_text_service.process_route_text",
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
                        "raw_address": "Киев, Тестовая 1",
                        "clean_address": "Киев, Тестовая 1",
                        "full_address": "Киев, Тестовая 1",
                        "status": "valid",
                        "is_crossed": False,
                        "formatted_address": "Киев, Тестовая 1",
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
                "parsed_points_count": 1,
                "raw_text_lines": 3,
                "parse_error_message": None,
            },
        ):
            response = self.client.post("/api/v1/process-route-text", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["parsed_points_count"], 1)
        self.assertEqual(body["points"][0]["route_order"], 1)

    def test_process_route_text_rejects_empty_text(self) -> None:
        response = self.client.post("/api/v1/process-route-text", json={"text": "   "})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Text payload must not be empty.")

    def test_parser_accepts_transliterated_markers(self) -> None:
        text = (
            "Service header\n"
            "Zakaz No 1001\n"
            "Kontaktnoe lico: PETRENKO IVAN, tel. +38 067-123-45-67\n"
            "Adres: Kyiv, Antonovycha 28\n"
        )

        points = AddressParserService().parse_route_text(text)

        self.assertEqual(len(points), 1)
        self.assertEqual(points[0].contact_name, "PETRENKO IVAN")
        self.assertEqual(points[0].phone, "+380671234567")
        self.assertEqual(points[0].raw_address, "Kyiv, Antonovycha 28")
        self.assertEqual(points[0].status, "valid")


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


class MockResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.request = httpx.Request(
            "GET",
            "https://maps.googleapis.com/maps/api/geocode/json",
        )

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=self.request,
                response=httpx.Response(self.status_code, request=self.request),
            )

    def json(self) -> dict:
        return self._payload


class GeocodeEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.original_key = settings.GOOGLE_MAPS_API_KEY
        settings.GOOGLE_MAPS_API_KEY = "test-key"

    def tearDown(self) -> None:
        settings.GOOGLE_MAPS_API_KEY = self.original_key

    def test_geocode_endpoint_handles_all_statuses(self) -> None:
        payload = {
            "points": [
                {
                    "contact_name": "Ольга",
                    "phone": "0660841846",
                    "raw_address": "вул. Антоновича 28 (БЦ Волна)",
                    "clean_address": "Киев, вул. Антоновича 28",
                    "full_address": "вул. Антоновича 28 (БЦ Волна)",
                    "status": "valid",
                    "is_crossed": False,
                },
                {
                    "contact_name": "Ірина",
                    "phone": "0670000001",
                    "raw_address": "Софіївська Борщагівка, вул. Соборна 126",
                    "clean_address": "Софіївська Борщагівка, вул. Соборна 126",
                    "full_address": "Софіївська Борщагівка, вул. Соборна 126",
                    "status": "valid",
                    "is_crossed": False,
                },
                {
                    "contact_name": "Самовивоз",
                    "phone": "0501112233",
                    "raw_address": "самовивоз, склад №1",
                    "clean_address": "Киев, самовивоз, склад №1",
                    "full_address": "самовивоз, склад №1",
                    "status": "skipped",
                    "is_crossed": False,
                },
                {
                    "contact_name": "Нет адреса",
                    "phone": "0670000002",
                    "raw_address": "несуществующий адрес 12345",
                    "clean_address": "Киев, несуществующий адрес 12345",
                    "full_address": "несуществующий адрес 12345",
                    "status": "valid",
                    "is_crossed": False,
                },
                {
                    "contact_name": "Сетевая ошибка",
                    "phone": "0670000003",
                    "raw_address": "Киев, ул. Тестовая 99",
                    "clean_address": "Киев, ул. Тестовая 99",
                    "full_address": "Киев, ул. Тестовая 99",
                    "status": "valid",
                    "is_crossed": False,
                },
            ]
        }

        responses = [
            MockResponse(
                {
                    "status": "OK",
                    "results": [
                        {
                            "formatted_address": "вулиця Антоновича, 28, Київ, Україна, 02000",
                            "geometry": {"location": {"lat": 50.4266, "lng": 30.5165}},
                        }
                    ],
                }
            ),
            MockResponse(
                {
                    "status": "OK",
                    "results": [
                        {
                            "formatted_address": "вулиця Соборна, 126, Софіївська Борщагівка, Київська область, Україна, 08131",
                            "geometry": {"location": {"lat": 50.4072, "lng": 30.3671}},
                        }
                    ],
                }
            ),
            MockResponse({"status": "ZERO_RESULTS", "results": []}),
            httpx.ConnectError(
                "network down",
                request=httpx.Request(
                    "GET",
                    "https://maps.googleapis.com/maps/api/geocode/json",
                ),
            ),
        ]

        with patch("httpx.Client.get", side_effect=responses):
            response = self.client.post("/api/v1/geocode", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["points"][0]["geocode_status"], "ok")
        self.assertEqual(body["points"][1]["geocode_status"], "ok")
        self.assertEqual(body["points"][2]["geocode_status"], "skipped")
        self.assertEqual(body["points"][3]["geocode_status"], "not_found")
        self.assertEqual(body["points"][3]["status"], "skipped")
        self.assertEqual(body["points"][4]["geocode_status"], "error")

    def test_geocode_endpoint_requires_api_key(self) -> None:
        settings.GOOGLE_MAPS_API_KEY = ""
        response = self.client.post("/api/v1/geocode", json={"points": []})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "GOOGLE_MAPS_API_KEY is required for geocoding.",
        )


if __name__ == "__main__":
    unittest.main()

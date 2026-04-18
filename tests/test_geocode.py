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

    def _post_geocode(self, point: dict, response_payload: object) -> dict:
        side_effect = [response_payload] if not isinstance(response_payload, Exception) else [response_payload]
        with patch("httpx.Client.get", side_effect=side_effect):
            response = self.client.post("/api/v1/geocode", json={"points": [point]})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_geocode_endpoint_marks_exact_result(self) -> None:
        point = {
            "contact_name": "Exact",
            "phone": "111",
            "raw_address": "Kyiv, Antonovycha 28",
            "clean_address": "Kyiv, Antonovycha 28",
            "full_address": "Kyiv, Antonovycha 28",
            "status": "valid",
            "is_crossed": False,
        }
        google_response = MockResponse(
            {
                "status": "OK",
                "results": [
                    {
                        "formatted_address": "Antonovycha St, 28, Kyiv, Ukraine",
                        "types": ["street_address"],
                        "address_components": [
                            {"long_name": "28", "types": ["street_number"]},
                            {"long_name": "Antonovycha St", "types": ["route"]},
                        ],
                        "geometry": {
                            "location": {"lat": 50.4266, "lng": 30.5165},
                            "location_type": "ROOFTOP",
                        },
                    }
                ],
            }
        )

        body = self._post_geocode(point, google_response)

        self.assertEqual(body["points"][0]["geocode_status"], "ok")
        self.assertEqual(body["points"][0]["geocode_precision"], "exact")
        self.assertEqual(
            body["start_point"]["address"],
            "Киев, Индустриальный переулок, 23",
        )

    def test_geocode_endpoint_marks_acceptable_result(self) -> None:
        point = {
            "contact_name": "Acceptable",
            "phone": "222",
            "raw_address": "Sofiivska Borshchahivka, Soborna 126",
            "clean_address": "Sofiivska Borshchahivka, Soborna 126",
            "full_address": "Sofiivska Borshchahivka, Soborna 126",
            "status": "valid",
            "is_crossed": False,
        }
        google_response = MockResponse(
            {
                "status": "OK",
                "results": [
                    {
                        "formatted_address": "Soborna St, 126, Sofiivska Borshchahivka, Ukraine",
                        "types": ["street_address"],
                        "address_components": [
                            {"long_name": "126", "types": ["street_number"]},
                            {"long_name": "Soborna St", "types": ["route"]},
                        ],
                        "geometry": {
                            "location": {"lat": 50.4072, "lng": 30.3671},
                            "location_type": "RANGE_INTERPOLATED",
                        },
                    }
                ],
            }
        )

        body = self._post_geocode(point, google_response)

        self.assertEqual(body["points"][0]["geocode_status"], "ok")
        self.assertEqual(body["points"][0]["geocode_precision"], "acceptable")

    def test_geocode_endpoint_downgrades_city_level_result(self) -> None:
        point = {
            "contact_name": "TooGeneral",
            "phone": "333",
            "raw_address": "Kyiv",
            "clean_address": "Kyiv",
            "full_address": "Kyiv",
            "status": "valid",
            "is_crossed": False,
        }
        google_response = MockResponse(
            {
                "status": "OK",
                "results": [
                    {
                        "formatted_address": "Kyiv, Ukraine",
                        "types": ["locality", "political"],
                        "address_components": [
                            {"long_name": "Kyiv", "types": ["locality", "political"]},
                            {"long_name": "Ukraine", "types": ["country", "political"]},
                        ],
                        "geometry": {
                            "location": {"lat": 50.4501, "lng": 30.5234},
                            "location_type": "APPROXIMATE",
                        },
                    }
                ],
            }
        )

        body = self._post_geocode(point, google_response)

        self.assertEqual(body["points"][0]["geocode_status"], "not_found")
        self.assertEqual(body["points"][0]["geocode_precision"], "too_general")
        self.assertEqual(body["points"][0]["status"], "skipped")
        self.assertIsNone(body["points"][0]["formatted_address"])

    def test_geocode_endpoint_rejects_missing_house_precision(self) -> None:
        point = {
            "contact_name": "MissingHouse",
            "phone": "444",
            "raw_address": "Kyiv, Test Street 10",
            "clean_address": "Kyiv, Test Street 10",
            "full_address": "Kyiv, Test Street 10",
            "status": "valid",
            "is_crossed": False,
        }
        google_response = MockResponse(
            {
                "status": "OK",
                "results": [
                    {
                        "formatted_address": "Test Street, Kyiv, Ukraine",
                        "types": ["route"],
                        "address_components": [
                            {"long_name": "Test Street", "types": ["route"]},
                            {"long_name": "Kyiv", "types": ["locality", "political"]},
                        ],
                        "geometry": {
                            "location": {"lat": 50.451, "lng": 30.52},
                            "location_type": "GEOMETRIC_CENTER",
                        },
                    }
                ],
            }
        )

        body = self._post_geocode(point, google_response)

        self.assertEqual(body["points"][0]["geocode_status"], "not_found")
        self.assertEqual(body["points"][0]["geocode_precision"], "too_general")
        self.assertEqual(body["points"][0]["status"], "skipped")
        self.assertIsNone(body["points"][0]["lat"])
        self.assertIsNone(body["points"][0]["lng"])

    def test_skipped_point_remains_skipped(self) -> None:
        response = self.client.post(
            "/api/v1/geocode",
            json={
                "points": [
                    {
                        "contact_name": "Skipped",
                        "phone": "555",
                        "raw_address": "pickup",
                        "clean_address": "Kyiv, pickup",
                        "full_address": "pickup",
                        "status": "skipped",
                        "is_crossed": False,
                    }
                ]
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["points"][0]["geocode_status"], "skipped")
        self.assertEqual(body["points"][0]["geocode_precision"], "unknown")
        self.assertIsNone(body["points"][0]["formatted_address"])

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

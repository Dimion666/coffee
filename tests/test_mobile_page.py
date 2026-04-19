import unittest

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


class MobilePageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_root_redirects_to_mobile(self) -> None:
        response = self.client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], "/mobile")

    def test_mobile_page_is_available(self) -> None:
        response = self.client.get("/mobile")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Coffee Mobile OCR", response.text)
        self.assertIn("uploadButton", response.text)
        self.assertIn("/api/v1/process-route-photo", response.text)
        self.assertIn('accept="image/jpeg,image/png"', response.text)
        self.assertNotIn("capture=", response.text)
        self.assertIn("Фотографируйте сверху", response.text)
        self.assertIn("qualityNotice", response.text)
        self.assertIn("partial success", response.text)
        self.assertIn("parsed_points_count", response.text)
        self.assertIn("rows_written", response.text)
        self.assertIn("Valid / skipped", response.text)
        self.assertIn(settings.GOOGLE_SHEETS_URL, response.text)


if __name__ == "__main__":
    unittest.main()

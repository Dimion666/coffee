import unittest

from fastapi.testclient import TestClient

from app.main import app


class UploadRoutePhotoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_upload_route_photo_success(self) -> None:
        response = self.client.post(
            "/api/v1/upload-route-photo",
            files={"file": ("route.png", b"\x89PNG\r\n\x1a\nrest", "image/png")},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["filename"], "route.png")
        self.assertEqual(payload["content_type"], "image/png")
        self.assertEqual(payload["file_size"], 12)
        self.assertEqual(payload["message"], "uploaded")

    def test_upload_route_photo_requires_file(self) -> None:
        response = self.client.post("/api/v1/upload-route-photo")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "File field is required.")

    def test_upload_route_photo_rejects_empty_file(self) -> None:
        response = self.client.post(
            "/api/v1/upload-route-photo",
            files={"file": ("empty.jpg", b"", "image/jpeg")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Uploaded file is empty.")

    def test_upload_route_photo_rejects_type(self) -> None:
        response = self.client.post(
            "/api/v1/upload-route-photo",
            files={"file": ("notes.pdf", b"%PDF-1.7", "application/pdf")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "Unsupported file type. Only JPG, JPEG, and PNG are allowed.",
        )

    def test_upload_route_photo_rejects_large_file(self) -> None:
        response = self.client.post(
            "/api/v1/upload-route-photo",
            files={"file": ("large.png", b"a" * (10 * 1024 * 1024 + 1), "image/png")},
        )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(
            response.json()["detail"],
            "Uploaded file is too large. Maximum size is 10 MB.",
        )


if __name__ == "__main__":
    unittest.main()

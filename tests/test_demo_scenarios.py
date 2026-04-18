import unittest

from fastapi.testclient import TestClient

from app.main import app


class DemoScenariosEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_demo_scenarios_endpoint_returns_examples(self) -> None:
        response = self.client.get("/api/v1/demo-scenarios")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreaterEqual(len(body["scenarios"]), 3)
        ids = {scenario["id"] for scenario in body["scenarios"]}
        self.assertIn("happy_path", ids)
        self.assertIn("mixed_path", ids)
        self.assertIn("noisy_path", ids)


if __name__ == "__main__":
    unittest.main()

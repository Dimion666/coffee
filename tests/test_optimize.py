import unittest
from unittest.mock import patch

from app.schemas.geocode import GeocodedPoint
from app.services.route_optimizer_service import RouteOptimizerService


def make_point(
    contact_name: str,
    *,
    status: str = "valid",
    is_crossed: bool = False,
    geocode_status: str = "ok",
    geocode_precision: str = "exact",
    lat: float | None = 50.45,
    lng: float | None = 30.52,
) -> GeocodedPoint:
    return GeocodedPoint(
        contact_name=contact_name,
        phone="000",
        raw_address=f"{contact_name} raw",
        clean_address=f"{contact_name} clean",
        full_address=f"{contact_name} full",
        status=status,
        is_crossed=is_crossed,
        formatted_address=f"{contact_name} formatted" if lat is not None else None,
        lat=lat,
        lng=lng,
        geocode_status=geocode_status,
        geocode_precision=geocode_precision,
    )


class RouteOptimizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = RouteOptimizerService()

    def test_optimize_route_handles_no_eligible_points(self) -> None:
        points = [
            make_point("Skipped", status="skipped", geocode_status="skipped", lat=None, lng=None),
            make_point("NotFound", status="skipped", geocode_status="not_found", geocode_precision="too_general", lat=None, lng=None),
        ]

        with patch.object(
            self.service,
            "_geocode_start_point",
            return_value={
                "geocode_status": "ok",
                "lat": 50.43,
                "lng": 30.41,
            },
        ):
            result = self.service.optimize_route(points)

        self.assertTrue(result.optimization.success)
        self.assertEqual(result.optimization.eligible_points, 0)
        self.assertEqual(result.optimization.excluded_points, 2)
        self.assertEqual(result.points[0].route_order, None)
        self.assertEqual(result.points[1].route_order, None)

    def test_optimize_route_handles_one_eligible_point(self) -> None:
        points = [make_point("One")]

        with patch.object(
            self.service,
            "_geocode_start_point",
            return_value={
                "geocode_status": "ok",
                "lat": 50.43,
                "lng": 30.41,
            },
        ) as geocode_mock, patch.object(
            self.service,
            "_request_optimized_order",
        ) as routes_mock:
            result = self.service.optimize_route(points)

        self.assertTrue(result.optimization.success)
        self.assertEqual(result.optimization.eligible_points, 1)
        self.assertEqual(result.points[0].route_order, 1)
        geocode_mock.assert_called_once()
        routes_mock.assert_not_called()

    def test_optimize_route_assigns_orders_for_multiple_points(self) -> None:
        points = [
            make_point("A"),
            make_point("B"),
            make_point("C"),
            make_point("Skipped", status="skipped", geocode_status="skipped", lat=None, lng=None),
        ]

        with patch.object(
            self.service,
            "_geocode_start_point",
            return_value={
                "geocode_status": "ok",
                "lat": 50.43,
                "lng": 30.41,
            },
        ), patch.object(
            self.service,
            "_request_optimized_order",
            return_value=[2, 0, 1],
        ):
            result = self.service.optimize_route(points)

        self.assertTrue(result.optimization.success)
        self.assertEqual(result.optimization.eligible_points, 3)
        self.assertEqual(result.optimization.excluded_points, 1)
        self.assertEqual(result.points[0].route_order, 2)
        self.assertEqual(result.points[1].route_order, 3)
        self.assertEqual(result.points[2].route_order, 1)
        self.assertEqual(result.points[3].route_order, None)

    def test_crossed_and_skipped_points_remain_without_route_order(self) -> None:
        points = [
            make_point("Eligible"),
            make_point("Crossed", is_crossed=True),
            make_point("Skipped", status="skipped", geocode_status="skipped", lat=None, lng=None),
        ]

        with patch.object(
            self.service,
            "_geocode_start_point",
            return_value={
                "geocode_status": "ok",
                "lat": 50.43,
                "lng": 30.41,
            },
        ):
            result = self.service.optimize_route(points)

        self.assertEqual(result.points[0].route_order, 1)
        self.assertIsNone(result.points[1].route_order)
        self.assertIsNone(result.points[2].route_order)

    def test_optimize_route_handles_routes_api_failure(self) -> None:
        points = [make_point("A"), make_point("B"), make_point("C")]

        with patch.object(
            self.service,
            "_geocode_start_point",
            return_value={
                "geocode_status": "ok",
                "lat": 50.43,
                "lng": 30.41,
            },
        ), patch.object(
            self.service,
            "_request_optimized_order",
            side_effect=RuntimeError("Routes API unavailable"),
        ):
            result = self.service.optimize_route(points)

        self.assertFalse(result.optimization.success)
        self.assertEqual(result.optimization.error_message, "Routes API unavailable")
        self.assertTrue(all(point.route_order is None for point in result.points))


if __name__ == "__main__":
    unittest.main()

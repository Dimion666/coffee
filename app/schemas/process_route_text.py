from app.schemas.process_route import ProcessRouteResponse


class ProcessRouteTextResponse(ProcessRouteResponse):
    parsed_points_count: int
    raw_text_lines: int
    parse_error_message: str | None

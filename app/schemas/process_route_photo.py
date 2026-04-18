from app.schemas.process_route_text import ProcessRouteTextResponse


class ProcessRoutePhotoResponse(ProcessRouteTextResponse):
    extracted_text: str
    filename: str
    content_type: str
    file_size: int

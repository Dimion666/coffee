from pydantic import BaseModel


class RoutePhotoUploadResponse(BaseModel):
    success: bool
    filename: str
    content_type: str
    file_size: int
    message: str

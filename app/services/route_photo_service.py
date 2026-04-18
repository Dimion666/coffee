from pathlib import Path

from fastapi import UploadFile

from app.schemas.upload import RoutePhotoUploadResponse

ALLOWED_ROUTE_PHOTO_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
}
ALLOWED_ROUTE_PHOTO_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}
MAX_ROUTE_PHOTO_SIZE_BYTES = 10 * 1024 * 1024


class RoutePhotoUploadError(ValueError):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class RoutePhotoService:
    async def inspect_upload(
        self,
        file: UploadFile | None,
    ) -> RoutePhotoUploadResponse:
        if file is None:
            raise RoutePhotoUploadError("File field is required.")

        filename = Path(file.filename or "").name
        if not filename:
            raise RoutePhotoUploadError("Filename is required.")

        extension = Path(filename).suffix.lower()
        content_type = (file.content_type or "").lower()
        if content_type == "application/octet-stream" and extension in ALLOWED_ROUTE_PHOTO_EXTENSIONS:
            if extension == ".png":
                content_type = "image/png"
            else:
                content_type = "image/jpeg"

        if (
            extension not in ALLOWED_ROUTE_PHOTO_EXTENSIONS
            or content_type not in ALLOWED_ROUTE_PHOTO_TYPES
        ):
            raise RoutePhotoUploadError(
                "Unsupported file type. Only JPG, JPEG, and PNG are allowed."
            )

        content = await file.read()
        file_size = len(content)
        await file.close()

        if file_size == 0:
            raise RoutePhotoUploadError("Uploaded file is empty.")

        if file_size > MAX_ROUTE_PHOTO_SIZE_BYTES:
            raise RoutePhotoUploadError(
                "Uploaded file is too large. Maximum size is 10 MB.",
                status_code=413,
            )

        return RoutePhotoUploadResponse(
            success=True,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            message="uploaded",
        )

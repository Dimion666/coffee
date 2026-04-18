from pydantic import BaseModel

from app.schemas.optimize import OptimizedPoint


class ExportRequest(BaseModel):
    points: list[OptimizedPoint]


class ExportResponse(BaseModel):
    success: bool
    spreadsheet_id: str
    worksheet_name: str
    rows_written: int
    error_message: str | None

from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.export import ExportResponse
from app.schemas.optimize import OptimizedPoint

logger = get_logger(__name__)

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEETS_HEADERS = [
    "route_order",
    "contact_name",
    "phone",
    "raw_address",
    "clean_address",
    "full_address",
    "formatted_address",
    "lat",
    "lng",
    "status",
    "geocode_status",
    "geocode_precision",
    "is_crossed",
]


class SheetsService:
    """Google Sheets export service for optimized route rows."""

    def _get_credentials_path(self) -> str:
        if settings.GOOGLE_APPLICATION_CREDENTIALS.strip():
            return settings.GOOGLE_APPLICATION_CREDENTIALS.strip()
        return settings.GOOGLE_SERVICE_ACCOUNT_FILE.strip()

    def _build_client(self):
        spreadsheet_id = settings.GOOGLE_SHEETS_SPREADSHEET_ID.strip()
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID is required.")

        credentials_path = self._get_credentials_path()
        if not credentials_path:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_APPLICATION_CREDENTIALS is required."
            )

        if not Path(credentials_path).exists():
            raise FileNotFoundError(
                f"Google Sheets credentials file not found: {credentials_path}"
            )

        credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=SHEETS_SCOPES,
        )
        service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        return service.spreadsheets(), spreadsheet_id

    def _ensure_worksheet_exists(self, sheets_api, spreadsheet_id: str, worksheet_name: str) -> None:
        spreadsheet = sheets_api.get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get("sheets", [])
        if any(
            sheet.get("properties", {}).get("title") == worksheet_name for sheet in sheets
        ):
            return

        sheets_api.batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": [
                    {
                        "addSheet": {
                            "properties": {
                                "title": worksheet_name,
                            }
                        }
                    }
                ]
            },
        ).execute()

    def _point_to_row(self, point: OptimizedPoint) -> list[str | int | float | bool | None]:
        return [
            point.route_order,
            point.contact_name,
            point.phone,
            point.raw_address,
            point.clean_address,
            point.full_address,
            point.formatted_address,
            point.lat,
            point.lng,
            point.status,
            point.geocode_status,
            point.geocode_precision,
            point.is_crossed,
        ]

    def export_points(self, points: list[OptimizedPoint]) -> ExportResponse:
        worksheet_name = settings.GOOGLE_SHEETS_WORKSHEET_NAME.strip() or "routes"
        sheets_api, spreadsheet_id = self._build_client()

        try:
            self._ensure_worksheet_exists(sheets_api, spreadsheet_id, worksheet_name)
            sheet_range = f"{worksheet_name}!A:M"

            sheets_api.values().clear(
                spreadsheetId=spreadsheet_id,
                range=sheet_range,
            ).execute()

            values = [SHEETS_HEADERS] + [self._point_to_row(point) for point in points]
            sheets_api.values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{worksheet_name}!A1",
                valueInputOption="RAW",
                body={"values": values},
            ).execute()

            logger.info(
                "Google Sheets export completed | worksheet=%s rows_written=%s",
                worksheet_name,
                len(points),
            )
            return ExportResponse(
                success=True,
                spreadsheet_id=spreadsheet_id,
                worksheet_name=worksheet_name,
                rows_written=len(points),
                error_message=None,
            )
        except HttpError as exc:
            logger.exception("Google Sheets API export failed.")
            raise RuntimeError(f"Google Sheets API error: {exc}") from exc
        except Exception:
            logger.exception("Google Sheets export failed.")
            raise

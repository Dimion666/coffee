# Coffee

Coffee is an MVP backend skeleton for a one-vehicle route address optimizer.
This block includes only the project structure, configuration, logging, API
health endpoints, and service/database placeholders.

## Install

```powershell
pip install -r requirements.txt
```

## Run

```powershell
powershell ./run.ps1
```

The API starts on `http://127.0.0.1:8000`.

## Available endpoints

- `GET /health`
- `GET /api/v1/system/ping`
- `GET /api/v1/demo-scenarios`
- `POST /api/v1/upload-route-photo`
- `POST /api/v1/process-route-photo`
- `POST /api/v1/parse/text`
- `POST /api/v1/normalize`
- `POST /api/v1/geocode`
- `POST /api/v1/optimize`
- `POST /api/v1/export-sheet`
- `POST /api/v1/process-route`
- `POST /api/v1/process-route-text`

## Required environment variables

- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `GOOGLE_MAPS_API_KEY`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SHEETS_WORKSHEET_NAME`
- `GOOGLE_SHEETS_TARGET_RANGE`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `TESSERACT_CMD`
- `TESSERACT_LANG`
- `TESSDATA_DIR`
- `SQLITE_DB_PATH`

Copy `.env.example` to `.env` and fill in the values you need for local work.

## OCR Setup

`POST /api/v1/process-route-photo` uses Tesseract OCR through `pytesseract`.

Local MVP setup:
- install Tesseract OCR locally
- keep `eng`, `rus`, and `ukr` traineddata available
- optionally set `TESSERACT_CMD` if `tesseract.exe` is not in the default location
- optionally set `TESSDATA_DIR` if traineddata are stored outside the system folder

The project also auto-detects local traineddata from `.ocr-data/tessdata` when that folder exists.

## Demo Flow

1. Start the backend:

```powershell
powershell ./run.ps1
```

2. Open docs:

```text
http://127.0.0.1:8000/docs
```

3. Fetch demo scenarios from:

```text
GET /api/v1/demo-scenarios
```

4. Run the first manual test with scenario `happy_path`:

```text
POST /api/v1/process-route-text
```

Request body:

```json
{
  "text": "<paste scenario text here>"
}
```

5. Successful result means:
- response status is `200`
- `success = true`
- `parsed_points_count > 0`
- eligible points have `route_order`
- `export.success = true`
- `export.rows_written > 0`

6. Check Google Sheets:
- open `https://docs.google.com/spreadsheets/d/<GOOGLE_SHEETS_SPREADSHEET_ID>`
- inspect worksheet from `GOOGLE_SHEETS_WORKSHEET_NAME`
- confirm rows were updated after the request

## Manual Test Checklist

- Start backend and confirm `GET /health` returns `{"status":"ok"}`.
- Open `GET /api/v1/demo-scenarios` and choose `happy_path` for the first run.
- Send selected raw text to `POST /api/v1/process-route-text`.
- Confirm response has `success = true`.
- Confirm at least one valid point has `route_order`.
- Confirm `export.success = true` and `rows_written > 0`.
- Open the configured Google Sheet and verify the written rows match the response.

## Mobile Flow

Open `http://<your-local-ip>:8000/mobile` on the phone.

Flow:
- take a photo of the route sheet
- tap `Распознать и обработать`
- wait for OCR, route processing, and export to Google Sheets
- use `Открыть Google Sheets` to jump to the table from the phone

Expected success:
- backend returns `success = true`
- response includes `extracted_text`
- valid points receive `route_order`
- `export.rows_written > 0`
- Google Sheets link is visible on the page and opens the configured spreadsheet
- mobile page shows overall status, OCR preview, parsed points, valid/skipped counts, optimize/export status, and rows written
- if OCR is weak, mobile page shows a clear reshoot hint instead of an empty result

If the result is weak:
- retake the photo from above
- use good light
- keep the whole sheet in frame
- avoid strong tilt and cropped addresses

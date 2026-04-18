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
- `SQLITE_DB_PATH`

Copy `.env.example` to `.env` and fill in the values you need for local work.

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
- wait for OCR in the browser
- correct text if needed
- tap `Обработать маршрут и записать в Sheets`
- open the Google Sheets button after success

Expected success:
- OCR fills the text area
- backend returns `success = true`
- valid points receive `route_order`
- Google Sheets button appears
- written rows match the latest run in the configured worksheet

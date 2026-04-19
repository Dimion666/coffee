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

## Render Deployment

Coffee is prepared for Render as a Docker web service because the mobile photo
flow needs the system `tesseract` binary and Ukrainian/Russian OCR language
packs.

Render files:
- `Dockerfile` installs Python 3.11 dependencies and Tesseract OCR.
- `render.yaml` declares the web service, health check, and non-secret env keys.
- `.dockerignore` excludes local secrets, credentials, logs, caches, and tests
  from the Docker build context.

Production start command inside the Docker image:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Render provides `PORT` automatically. The service must be opened at:

```text
https://<your-render-service>.onrender.com/mobile
```

Manual Render setup:
- push this commit to the Git repository connected to Render
- in Render Dashboard create a new Blueprint from `render.yaml`, or create a new
  Web Service with runtime `Docker`
- use the repository root as the Docker context
- keep the health check path as `/health`
- add the env variables below
- add the service account JSON as a Secret File named `service_account.json`
- deploy and open the generated `https://*.onrender.com/mobile` URL

Required Render environment variables:
- `APP_ENV=production`
- `APP_HOST=0.0.0.0`
- `GOOGLE_MAPS_API_KEY`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SHEETS_WORKSHEET_NAME=routes`
- `GOOGLE_SHEETS_TARGET_RANGE=routes!A:C`
- `GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/service_account.json`
- `GOOGLE_SERVICE_ACCOUNT_FILE=/etc/secrets/service_account.json`
- `TESSERACT_CMD=/usr/bin/tesseract`
- `TESSERACT_LANG=ukr+rus+eng`
- `TESSDATA_DIR=/usr/share/tesseract-ocr/5/tessdata`
- `SQLITE_DB_PATH=coffee.db`

Do not add secrets to git. In Render Dashboard, add the service account JSON as
a Secret File:

```text
Filename: service_account.json
Runtime path: /etc/secrets/service_account.json
```

The service account email must have Editor access to the target Google Sheet.

Render smoke test after deploy:
- open `GET /health`
- open `GET /docs`
- open `GET /mobile`
- upload a route sheet photo from `/mobile`
- confirm `success = true`, `route_order` is assigned, and `export.rows_written > 0`
- open the Google Sheets link from the page and confirm rows appeared

If `/api/v1/process-route-photo` fails on Render, check the Render logs first:
- `Tesseract OCR executable was not found` means the service is not running the Docker image or `TESSERACT_CMD` is wrong.
- `Error opening data file` means `TESSDATA_DIR` or language packs are wrong.
- `Google Sheets credentials file not found` means the Render Secret File is missing or the credentials path env value is wrong.
- Google API `403` usually means API access, billing, or service account sharing is not configured.

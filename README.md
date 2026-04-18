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

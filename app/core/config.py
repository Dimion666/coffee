import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    APP_ENV: str = Field(default="local")
    APP_HOST: str = Field(default="127.0.0.1")
    APP_PORT: int = Field(default=8000)

    GOOGLE_MAPS_API_KEY: str = Field(default="")
    GOOGLE_SHEETS_SPREADSHEET_ID: str = Field(default="")
    GOOGLE_SHEETS_TARGET_RANGE: str = Field(default="routes!A:C")
    GOOGLE_SERVICE_ACCOUNT_FILE: str = Field(
        default="credentials/service_account.json"
    )

    SQLITE_DB_PATH: str = Field(default="coffee.db")


def get_settings() -> Settings:
    return Settings(
        APP_ENV=os.getenv("APP_ENV", "local"),
        APP_HOST=os.getenv("APP_HOST", "127.0.0.1"),
        APP_PORT=int(os.getenv("APP_PORT", "8000")),
        GOOGLE_MAPS_API_KEY=os.getenv("GOOGLE_MAPS_API_KEY", ""),
        GOOGLE_SHEETS_SPREADSHEET_ID=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
        GOOGLE_SHEETS_TARGET_RANGE=os.getenv(
            "GOOGLE_SHEETS_TARGET_RANGE",
            "routes!A:C",
        ),
        GOOGLE_SERVICE_ACCOUNT_FILE=os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE",
            "credentials/service_account.json",
        ),
        SQLITE_DB_PATH=os.getenv("SQLITE_DB_PATH", "coffee.db"),
    )


settings = get_settings()

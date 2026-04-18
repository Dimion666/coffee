from typing import Literal

from pydantic import BaseModel


class ParseTextRequest(BaseModel):
    text: str


class Point(BaseModel):
    contact_name: str
    phone: str
    raw_address: str
    status: Literal["valid", "skipped"]


class ParseTextResponse(BaseModel):
    points: list[Point]

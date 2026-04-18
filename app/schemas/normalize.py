from pydantic import BaseModel

from app.schemas.parse import Point as ParsedPoint


class NormalizeRequest(BaseModel):
    points: list[ParsedPoint]


class NormalizedPoint(ParsedPoint):
    clean_address: str
    full_address: str
    is_crossed: bool


class NormalizeResponse(BaseModel):
    points: list[NormalizedPoint]

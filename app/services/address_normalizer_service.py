import re
from typing import List

from app.core.logger import get_logger
from app.schemas.normalize import NormalizedPoint
from app.schemas.parse import Point as ParsedPoint

logger = get_logger(__name__)

MULTISPACE_PATTERN = re.compile(r"\s{2,}")
COMMA_SPACING_PATTERN = re.compile(r"\s*,\s*")
EMPTY_COMMA_PATTERN = re.compile(r"(,\s*){2,}")
PARENTHESIS_PATTERN = re.compile(r"\([^)]*\)")
ORIENTATION_PATTERNS = [
    re.compile(r"\bж[её]лтый\s+склад\b", re.IGNORECASE),
    re.compile(r"\bжовтий\s+склад\b", re.IGNORECASE),
    re.compile(r"\bg\s*park\b", re.IGNORECASE),
]
CITY_MARKERS = [
    "киев",
    "київ",
    "м. київ",
    "м. киев",
    "смт.",
    "с.",
    "софиевская борщаговка",
    "софіївська борщагівка",
    "коцюбинское",
    "коцюбинське",
    "kyiv",
    "kiev",
    "sofiivska borshchahivka",
    "sofievskaya borshchagovka",
    "kotsiubynske",
    "kotsyubinskoe",
]


def _normalize_spacing(value: str) -> str:
    normalized = (value or "").replace("\xa0", " ").strip()
    normalized = COMMA_SPACING_PATTERN.sub(", ", normalized)
    normalized = MULTISPACE_PATTERN.sub(" ", normalized)
    normalized = EMPTY_COMMA_PATTERN.sub(", ", normalized)
    normalized = re.sub(r"\s+,", ",", normalized)
    normalized = re.sub(r",\s*$", "", normalized)
    return normalized.strip(" ,")


def _build_full_address(raw_address: str) -> str:
    return _normalize_spacing(raw_address)


def _remove_orientation_fragments(address: str) -> str:
    cleaned = address
    for pattern in ORIENTATION_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    return cleaned


def _has_city_marker(address: str) -> bool:
    lowered = address.lower()
    return any(marker in lowered for marker in CITY_MARKERS)


def _build_clean_address(raw_address: str) -> str:
    cleaned = PARENTHESIS_PATTERN.sub("", raw_address or "")
    cleaned = _remove_orientation_fragments(cleaned)
    cleaned = _normalize_spacing(cleaned)

    if cleaned and not _has_city_marker(cleaned):
        cleaned = _normalize_spacing(f"Киев, {cleaned}")

    return cleaned


def normalize_points(points: List[ParsedPoint]) -> List[NormalizedPoint]:
    normalized_points: List[NormalizedPoint] = []
    skipped_points = 0
    changed_examples: list[str] = []

    for point in points:
        full_address = _build_full_address(point.raw_address)
        clean_address = _build_clean_address(point.raw_address)

        status = point.status
        if status != "skipped" and len(clean_address) < 8:
            status = "skipped"

        if status == "skipped":
            skipped_points += 1

        if len(changed_examples) < 3 and (
            full_address != point.raw_address.strip() or clean_address != full_address
        ):
            changed_examples.append(
                f"raw='{point.raw_address}' | clean='{clean_address}' | full='{full_address}'"
            )

        normalized_points.append(
            NormalizedPoint(
                contact_name=point.contact_name,
                phone=point.phone,
                raw_address=point.raw_address,
                clean_address=clean_address,
                full_address=full_address,
                status=status,
                is_crossed=False,
            )
        )

    valid_points = len(normalized_points) - skipped_points
    log_message = (
        "Points normalized | total_points=%s valid_points=%s skipped_points=%s"
    )
    if changed_examples:
        log_message += " changed_examples=%s"
        logger.info(
            log_message,
            len(points),
            valid_points,
            skipped_points,
            changed_examples,
        )
    else:
        logger.info(log_message, len(points), valid_points, skipped_points)

    return normalized_points


class AddressNormalizerService:
    """Service wrapper for route point address normalization."""

    def normalize_points(self, points: List[ParsedPoint]) -> List[NormalizedPoint]:
        return normalize_points(points)

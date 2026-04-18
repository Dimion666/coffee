import re
import unicodedata
from typing import List

from app.core.logger import get_logger
from app.schemas.parse import Point

logger = get_logger(__name__)

ORDER_DELIMITER_PATTERN = re.compile(
    r"(?:Заказ\s*(?:№|No)|Zakaz\s*(?:#|No)|Order\s*(?:#|No))",
    re.IGNORECASE,
)
CONTACT_MARKER_PATTERNS = [
    re.compile(r"Контактное\s+лицо", re.IGNORECASE),
    re.compile(r"Kontaktnoe\s+lico", re.IGNORECASE),
    re.compile(r"Kontaktna\s+osoba", re.IGNORECASE),
    re.compile(r"Contact", re.IGNORECASE),
]
ADDRESS_MARKER_PATTERNS = [
    re.compile(r"Адрес\s*:", re.IGNORECASE),
    re.compile(r"Adres\s*:", re.IGNORECASE),
    re.compile(r"Address\s*:", re.IGNORECASE),
]
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s\-]{8,})")
CONTACT_PHONE_SPLIT_PATTERN = re.compile(
    r"(?:тел\.?|tel\.?|phone\s*:?)",
    re.IGNORECASE,
)
MULTISPACE_PATTERN = re.compile(r"\s{2,}")
SKIP_MARKERS = [
    "самовивоз",
    "самовывоз",
    "samovyvoz",
    "samovuvoz",
]


def _clean_text(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value or "")
    normalized = normalized.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
    return normalized


def _clean_inline_value(value: str) -> str:
    cleaned = MULTISPACE_PATTERN.sub(" ", value.replace("\n", " ")).strip(" ,")
    return cleaned.strip()


def _extract_after_patterns(line: str, patterns: list[re.Pattern[str]]) -> str | None:
    for pattern in patterns:
        match = pattern.search(line)
        if not match:
            continue
        return line[match.end() :].lstrip(": ").strip()
    return None


def _extract_contact_name(block: str) -> str:
    lines = block.split("\n")
    for index, line in enumerate(lines):
        candidate = _extract_after_patterns(line, CONTACT_MARKER_PATTERNS)
        if candidate is None:
            continue

        if not candidate:
            for next_line in lines[index + 1 :]:
                next_line = next_line.strip()
                if next_line:
                    candidate = next_line
                    break

        candidate = CONTACT_PHONE_SPLIT_PATTERN.split(candidate, maxsplit=1)[0]
        return _clean_inline_value(candidate)

    for line in lines:
        phone_match = PHONE_PATTERN.search(line)
        if not phone_match:
            continue

        if _extract_after_patterns(line, ADDRESS_MARKER_PATTERNS) is not None:
            continue

        candidate = line[: phone_match.start()].strip(" ,")
        if ":" in candidate:
            candidate = candidate.split(":")[-1]

        candidate = CONTACT_PHONE_SPLIT_PATTERN.split(candidate, maxsplit=1)[0]
        candidate = _clean_inline_value(candidate)
        if candidate:
            return candidate

    return ""


def _extract_phone(block: str) -> str:
    match = PHONE_PATTERN.search(block)
    if not match:
        return ""
    return re.sub(r"[\s\-]+", "", match.group(1)).strip()


def _extract_address(block: str) -> str:
    for line in block.split("\n"):
        remainder = _extract_after_patterns(line, ADDRESS_MARKER_PATTERNS)
        if remainder is None:
            continue
        return _clean_inline_value(remainder)
    return ""


def parse_route_text(text: str) -> List[Point]:
    cleaned_text = _clean_text(text)
    raw_blocks = ORDER_DELIMITER_PATTERN.split(cleaned_text)
    blocks = [block.strip() for block in raw_blocks[1:] if block.strip()]

    points: List[Point] = []
    skipped_points = 0

    for block in blocks:
        raw_address = _extract_address(block)
        if not raw_address:
            continue

        lowered_address = raw_address.lower()
        status = "valid"
        if any(marker in lowered_address for marker in SKIP_MARKERS):
            status = "skipped"
            skipped_points += 1

        points.append(
            Point(
                contact_name=_extract_contact_name(block),
                phone=_extract_phone(block),
                raw_address=raw_address,
                status=status,
            )
        )

    parsed_points = len(points) - skipped_points
    logger.info(
        "Route text parsed | total_blocks=%s parsed_points=%s skipped_points=%s",
        len(blocks),
        parsed_points,
        skipped_points,
    )
    return points


class AddressParserService:
    """Service wrapper for parsing route sheet text into delivery points."""

    def parse_route_text(self, text: str) -> List[Point]:
        return parse_route_text(text)

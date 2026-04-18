import re
import shutil
from io import BytesIO
import os
from pathlib import Path

import pytesseract
from PIL import Image, ImageOps
from pytesseract import TesseractError, TesseractNotFoundError

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TESSERACT_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
]
LOCAL_TESSDATA_DIR = Path(".ocr-data") / "tessdata"


class OCRService:
    """Extracts route sheet text from an uploaded image with Tesseract OCR."""

    def _resolve_tesseract_cmd(self) -> str:
        configured_path = settings.TESSERACT_CMD.strip()
        if configured_path:
            return configured_path

        for candidate in DEFAULT_TESSERACT_PATHS:
            if candidate.exists():
                return str(candidate)

        discovered = shutil.which("tesseract")
        if discovered:
            return discovered

        raise RuntimeError(
            "Tesseract OCR executable was not found. Configure TESSERACT_CMD or install Tesseract."
        )

    def _resolve_tessdata_dir(self) -> str | None:
        configured_dir = settings.TESSDATA_DIR.strip()
        if configured_dir:
            return str(Path(configured_dir).resolve())

        if LOCAL_TESSDATA_DIR.exists():
            return str(LOCAL_TESSDATA_DIR.resolve())

        return None

    def _preprocess_image(self, image_bytes: bytes) -> Image.Image:
        image = Image.open(BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image).convert("L")

        if image.width < 1600:
            scale = max(2, round(1600 / max(image.width, 1)))
            image = image.resize(
                (image.width * scale, image.height * scale),
                Image.Resampling.LANCZOS,
            )

        image = ImageOps.autocontrast(image)
        image = image.point(lambda pixel: 255 if pixel > 180 else 0)
        return image

    def extract_text(self, image_bytes: bytes) -> str:
        pytesseract.pytesseract.tesseract_cmd = self._resolve_tesseract_cmd()
        tessdata_dir = self._resolve_tessdata_dir()
        config_parts = ["--oem 3", "--psm 6"]
        if tessdata_dir:
            config_parts.append(f"--tessdata-dir {Path(tessdata_dir).as_posix()}")

        image = self._preprocess_image(image_bytes)

        try:
            if tessdata_dir:
                os.environ["TESSDATA_PREFIX"] = tessdata_dir
            raw_text = pytesseract.image_to_string(
                image,
                lang=settings.TESSERACT_LANG,
                config=" ".join(config_parts),
            )
        except TesseractNotFoundError as exc:
            raise RuntimeError(
                "Tesseract OCR executable was not found. Configure TESSERACT_CMD or install Tesseract."
            ) from exc
        except TesseractError as exc:
            raise RuntimeError(f"OCR failed: {exc}") from exc

        normalized_lines = []
        for line in raw_text.splitlines():
            cleaned_line = re.sub(r"\s+", " ", line).strip()
            if cleaned_line:
                normalized_lines.append(cleaned_line)

        extracted_text = "\n".join(normalized_lines).strip()
        if not extracted_text:
            raise ValueError("OCR did not extract any text from the image.")

        logger.info(
            "OCR extraction completed | characters=%s lines=%s",
            len(extracted_text),
            len(normalized_lines),
        )
        return extracted_text

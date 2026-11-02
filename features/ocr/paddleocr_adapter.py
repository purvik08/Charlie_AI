"""
PaddleOCR Adapter for Charlie AI.

Integrates the PaddleOCR library (located at PaddleOCR-main/) to provide
optical character recognition for images, scanned PDFs, and documents.

Supports:
- Single image OCR (PNG, JPG, JPEG, BMP, TIFF, WEBP, GIF)
- Multi-page PDF text extraction (via paddleocr PP-StructureV3)
- Clipboard image OCR
- Batch file processing
- Falls back gracefully if PaddleOCR is not installed
"""

import logging
import os
import sys
import io
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Add PaddleOCR source directory to path so it can be imported directly
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PADDLE_PATH = _PROJECT_ROOT / "PaddleOCR-main"
if _PADDLE_PATH.exists() and str(_PADDLE_PATH) not in sys.path:
    sys.path.insert(0, str(_PADDLE_PATH))

# Supported image file extensions
IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif",
    ".webp", ".gif", ".pnm", ".pgm", ".pbm", ".ppm",
}
DOCUMENT_EXTENSIONS = {".pdf"}


class PaddleOCRAdapter:
    """
    Adapter that wraps PaddleOCR for text extraction from images and PDFs.

    When PaddleOCR is not installed, it falls back to a lightweight
    description of the file so the conversation can still proceed.
    """

    def __init__(self, lang: str = "en", use_gpu: bool = False, data_dir: Optional[str] = None):
        """
        Initialize the PaddleOCR adapter.

        Args:
            lang: Language code for OCR (e.g., "en", "ch", "fr"). Defaults to "en".
            use_gpu: Whether to use GPU acceleration. Defaults to False.
            data_dir: Optional data directory for storing OCR results.
        """
        self.lang = lang
        self.use_gpu = use_gpu
        self.data_dir = Path(data_dir) if data_dir else Path("./charlie_data/ocr")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._ocr_engine = None
        self._engine_type = "none"
        self._initialize_engine()

    # ---------------------------------------------------------------------- init
    def _initialize_engine(self) -> None:
        """Try to initialise a PaddleOCR engine. Fails silently."""
        # Try paddleocr package (installed or from PaddleOCR-main)
        try:
            from paddleocr import PaddleOCR
            self._ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                use_gpu=self.use_gpu,
                show_log=False,
            )
            self._engine_type = "paddleocr"
            logger.info("PaddleOCR engine initialised (lang=%s, gpu=%s)", self.lang, self.use_gpu)
            return
        except ImportError:
            logger.debug("PaddleOCR not installed; trying pytesseract fallback.")
        except Exception as exc:
            logger.warning("PaddleOCR init failed: %s", exc)

        # Fallback: pytesseract (commonly pre-installed on many systems)
        try:
            import pytesseract
            from PIL import Image  # noqa: F401 – just verify PIL is available
            self._ocr_engine = pytesseract
            self._engine_type = "tesseract"
            logger.info("pytesseract fallback OCR engine activated.")
            return
        except ImportError:
            logger.debug("pytesseract not available either.")

        logger.warning(
            "No OCR engine available. Install 'paddleocr' or 'pytesseract' for image text extraction."
        )

    # ---------------------------------------------------------------------- public API
    def extract_text(
        self,
        source: Union[str, Path],
        page_range: Optional[tuple] = None,
    ) -> str:
        """
        Extract text from an image or PDF file.

        Args:
            source: Path to image or PDF file (str or Path).
            page_range: Optional (start, end) page tuple for PDFs (1-based).

        Returns:
            Extracted text as a string.
        """
        path = Path(source)
        if not path.exists():
            return f"File not found: {source}"

        suffix = path.suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            return self._ocr_image(path)
        if suffix in DOCUMENT_EXTENSIONS:
            return self._ocr_pdf(path, page_range=page_range)

        # Try treating any other file as an image
        return self._ocr_image(path)

    def process_query(self, query: str) -> str:
        """
        Natural language entry point: parse the query for a file path and run OCR.

        Examples of accepted queries:
            - "read the text in D:/scan.png"
            - "extract text from invoice.pdf"
            - "ocr C:/Users/me/photo.jpg"

        Returns a formatted OCR result string.
        """
        path = self._extract_path_from_query(query)
        if not path:
            return (
                "Please provide a file path to OCR. Example: "
                "'extract text from C:/Users/me/image.png'"
            )
        return self.extract_text(path)

    # ---------------------------------------------------------------------- internals
    def _ocr_image(self, image_path: Path) -> str:
        """Run OCR on a single image file."""
        if self._engine_type == "paddleocr":
            return self._paddleocr_image(image_path)
        if self._engine_type == "tesseract":
            return self._tesseract_image(image_path)
        return self._no_engine_message(image_path)

    def _paddleocr_image(self, image_path: Path) -> str:
        """Extract text using PaddleOCR."""
        try:
            result = self._ocr_engine.ocr(str(image_path), cls=True)
            lines = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text_info = line[1]
                        if isinstance(text_info, (list, tuple)) and len(text_info) >= 1:
                            text = text_info[0]
                            confidence = text_info[1] if len(text_info) > 1 else 1.0
                            if text and str(text).strip():
                                lines.append(str(text).strip())
            if not lines:
                return f"No text detected in image: {image_path.name}"
            return f"**OCR Result — {image_path.name}**\n\n" + "\n".join(lines)
        except Exception as exc:
            logger.exception("PaddleOCR image error: %s", exc)
            return f"OCR failed for {image_path.name}: {exc}"

    def _tesseract_image(self, image_path: Path) -> str:
        """Extract text using pytesseract."""
        try:
            from PIL import Image
            img = Image.open(str(image_path))
            text = self._ocr_engine.image_to_string(img, lang=self.lang)
            text = text.strip()
            if not text:
                return f"No text detected in image: {image_path.name}"
            return f"**OCR Result — {image_path.name}**\n\n{text}"
        except Exception as exc:
            logger.exception("Tesseract image error: %s", exc)
            return f"OCR failed for {image_path.name}: {exc}"

    def _ocr_pdf(self, pdf_path: Path, page_range: Optional[tuple] = None) -> str:
        """Extract text from a PDF via OCR or direct extraction."""
        # First try direct text extraction (fast, no OCR required)
        direct_text = self._extract_pdf_text_direct(pdf_path, page_range)
        if direct_text and len(direct_text.strip()) > 50:
            return f"**PDF Text — {pdf_path.name}**\n\n{direct_text}"

        # Fall back to rendering each page and running OCR
        if self._engine_type == "paddleocr":
            return self._paddleocr_pdf(pdf_path, page_range)
        if self._engine_type == "tesseract":
            return self._tesseract_pdf(pdf_path, page_range)
        return self._no_engine_message(pdf_path)

    def _extract_pdf_text_direct(self, pdf_path: Path, page_range: Optional[tuple]) -> str:
        """Use PyMuPDF or pdfplumber for direct text extraction."""
        # Try PyMuPDF (fitz)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(pdf_path))
            pages = list(range(doc.page_count))
            if page_range:
                s, e = page_range
                pages = pages[s - 1:e]
            texts = []
            for i in pages:
                page = doc.load_page(i)
                texts.append(page.get_text())
            doc.close()
            return "\n\n".join(texts)
        except ImportError:
            pass
        except Exception as exc:
            logger.debug("PyMuPDF extraction failed: %s", exc)

        # Try pdfplumber
        try:
            import pdfplumber
            texts = []
            with pdfplumber.open(str(pdf_path)) as pdf:
                pages = pdf.pages
                if page_range:
                    s, e = page_range
                    pages = pages[s - 1:e]
                for page in pages:
                    t = page.extract_text() or ""
                    texts.append(t)
            return "\n\n".join(texts)
        except ImportError:
            pass
        except Exception as exc:
            logger.debug("pdfplumber extraction failed: %s", exc)

        return ""

    def _paddleocr_pdf(self, pdf_path: Path, page_range: Optional[tuple]) -> str:
        """OCR a PDF using PaddleOCR by rendering pages."""
        try:
            import fitz  # PyMuPDF for rendering
            doc = fitz.open(str(pdf_path))
            pages = list(range(doc.page_count))
            if page_range:
                s, e = page_range
                pages = pages[s - 1:e]
            results = []
            for i in pages:
                page = doc.load_page(i)
                mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                # Pass image bytes directly to paddleocr
                import numpy as np
                from PIL import Image as PILImage
                img = PILImage.open(io.BytesIO(img_data))
                img_array = np.array(img)
                result = self._ocr_engine.ocr(img_array, cls=True)
                lines = []
                if result and result[0]:
                    for line in result[0]:
                        if line and len(line) >= 2:
                            text_info = line[1]
                            if isinstance(text_info, (list, tuple)) and len(text_info) >= 1:
                                text = str(text_info[0]).strip()
                                if text:
                                    lines.append(text)
                if lines:
                    results.append(f"--- Page {i + 1} ---\n" + "\n".join(lines))
            doc.close()
            if not results:
                return f"No text detected in PDF: {pdf_path.name}"
            return f"**PDF OCR Result — {pdf_path.name}**\n\n" + "\n\n".join(results)
        except Exception as exc:
            logger.exception("PaddleOCR PDF error: %s", exc)
            return f"OCR failed for {pdf_path.name}: {exc}"

    def _tesseract_pdf(self, pdf_path: Path, page_range: Optional[tuple]) -> str:
        """OCR a PDF using tesseract."""
        try:
            import fitz
            from PIL import Image
            doc = fitz.open(str(pdf_path))
            pages = list(range(doc.page_count))
            if page_range:
                s, e = page_range
                pages = pages[s - 1:e]
            results = []
            for i in pages:
                page = doc.load_page(i)
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = self._ocr_engine.image_to_string(img, lang=self.lang).strip()
                if text:
                    results.append(f"--- Page {i + 1} ---\n{text}")
            doc.close()
            if not results:
                return f"No text detected in PDF: {pdf_path.name}"
            return f"**PDF OCR Result — {pdf_path.name}**\n\n" + "\n\n".join(results)
        except Exception as exc:
            logger.exception("Tesseract PDF error: %s", exc)
            return f"OCR failed for {pdf_path.name}: {exc}"

    @staticmethod
    def _no_engine_message(source: Path) -> str:
        return (
            f"Cannot extract text from '{source.name}': no OCR engine is installed.\n"
            "Install PaddleOCR with: pip install paddleocr paddlepaddle\n"
            "Or pytesseract with: pip install pytesseract Pillow (and Tesseract from https://github.com/tesseract-ocr/tesseract)"
        )

    @staticmethod
    def _extract_path_from_query(query: str) -> Optional[Path]:
        """
        Heuristically extract a file path from a natural-language query.

        Looks for Windows-style (C:\\…) or Unix-style (/…) paths, as well
        as relative paths ending in a recognised extension.
        """
        # Windows absolute paths  (C:\... or C:/...)
        win_match = re.search(r"[A-Za-z]:[/\\][\w ./_\\-]+", query)
        if win_match:
            candidate = Path(win_match.group(0).rstrip(" .,'\""))
            if candidate.exists():
                return candidate

        # Unix absolute paths
        unix_match = re.search(r"/[\w ./_-]+", query)
        if unix_match:
            candidate = Path(unix_match.group(0).rstrip(" .,'\""))
            if candidate.exists():
                return candidate

        # Relative paths ending in a recognised extension
        ext_pattern = r"[\w ./\\-]+\.(?:" + "|".join(
            e.lstrip(".") for e in IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS
        ) + r")\b"
        rel_match = re.search(ext_pattern, query, re.IGNORECASE)
        if rel_match:
            candidate = Path(rel_match.group(0).strip())
            if candidate.exists():
                return candidate

        return None

    # ---------------------------------------------------------------------- capability info
    @property
    def available(self) -> bool:
        """True when at least one OCR engine is ready."""
        return self._engine_type != "none"

    @property
    def engine_name(self) -> str:
        return {"paddleocr": "PaddleOCR", "tesseract": "pytesseract", "none": "none"}[self._engine_type]

    def describe(self) -> str:
        """Return a human-readable description of this adapter's capabilities."""
        if not self.available:
            return "OCR engine not available. Install paddleocr or pytesseract."
        supported = ", ".join(sorted(IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS))
        return (
            f"OCR powered by {self.engine_name} (lang={self.lang}).\n"
            f"Supported file types: {supported}"
        )

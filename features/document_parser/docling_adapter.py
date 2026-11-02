"""
Docling Adapter for Charlie AI.

Integrates the Docling library (located at docling-main/) to parse and convert
diverse document formats into Markdown or plain text.

Supported formats:
  PDF, DOCX, PPTX, XLSX, HTML, EPUB, MD, TXT, Images (PNG, JPEG, TIFF …),
  Apple Pages/Numbers/Keynote, EML, MSG, ODF, XBRL, and more.

Falls back gracefully when Docling is not installed, providing a
basic text extraction layer using standard-library and common packages.
"""

import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Make the local docling-main directory importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DOCLING_PATH = _PROJECT_ROOT / "docling-main"
if _DOCLING_PATH.exists() and str(_DOCLING_PATH) not in sys.path:
    sys.path.insert(0, str(_DOCLING_PATH))

# Comprehensive list of extensions Docling handles
SUPPORTED_EXTENSIONS = {
    # Office / text
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls",
    ".html", ".htm", ".epub", ".md", ".txt", ".text", ".rst",
    ".odt", ".ods", ".odp",
    # Apple formats
    ".pages", ".numbers", ".key",
    # Email
    ".eml", ".msg",
    # Images (when used as document sources)
    ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp",
    # Other
    ".xml", ".json",
}


class DoclingAdapter:
    """
    Adapter that uses Docling to convert documents into Markdown/text.

    Cascades through three extraction strategies:
    1. Full Docling pipeline (best structure & accuracy).
    2. python-docx / openpyxl / python-pptx for common Office formats.
    3. Plain text read as a last resort.
    """

    def __init__(self, output_format: str = "markdown", data_dir: Optional[str] = None):
        """
        Args:
            output_format: "markdown" (default) or "text".
            data_dir: Optional directory for caching parsed results.
        """
        self.output_format = output_format
        self.data_dir = Path(data_dir) if data_dir else Path("./charlie_data/documents")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._docling_available = False
        self._converter = None
        self._try_init_docling()

    # ------------------------------------------------------------------ init
    def _try_init_docling(self) -> None:
        """Attempt to import and initialise the Docling DocumentConverter."""
        try:
            from docling.document_converter import DocumentConverter
            self._converter = DocumentConverter()
            self._docling_available = True
            logger.info("Docling DocumentConverter initialised successfully.")
        except ImportError:
            logger.info(
                "Docling not installed; using fallback text extraction. "
                "Install with: pip install docling"
            )
        except Exception as exc:
            logger.warning("Docling init failed (%s); using fallback.", exc)

    # ------------------------------------------------------------------ public API
    def convert(self, source: Union[str, Path]) -> str:
        """
        Convert a document to Markdown / plain text.

        Args:
            source: Local file path or URL string.

        Returns:
            Formatted text/markdown string.
        """
        src = str(source)
        path = Path(src) if not src.startswith(("http://", "https://")) else None

        # Validate local files exist
        if path and not path.exists():
            return f"File not found: {source}"

        # Docling supports both URLs and local paths
        if self._docling_available:
            result = self._docling_convert(src)
            if result:
                return result

        # Fallback: try format-specific extractors
        if path:
            return self._fallback_extract(path)

        return f"Cannot parse remote URL without Docling installed: {src}"

    def process_query(self, query: str) -> str:
        """
        Natural-language entry point.

        Parses a query like "parse report.pdf" or "read document invoice.docx"
        and returns the extracted text.
        """
        path = self._extract_path(query)
        if not path:
            return (
                "Please provide a file path. Example:\n"
                "  'parse C:/Users/me/report.pdf'\n"
                "  'read document invoice.docx'"
            )
        result = self.convert(path)
        # Summarise very long results
        if len(result) > 4000:
            preview = result[:3800]
            return (
                f"{preview}\n\n"
                f"… (output truncated — {len(result)} chars total). "
                "Ask me to continue or search within the document."
            )
        return result

    def get_summary(self, source: Union[str, Path], max_words: int = 200) -> str:
        """
        Extract document text and return only the first *max_words* words.
        Useful as a quick preview.
        """
        full = self.convert(source)
        words = full.split()
        if len(words) <= max_words:
            return full
        return " ".join(words[:max_words]) + f"\n\n… ({len(words)} words total)"

    # ------------------------------------------------------------------ Docling
    def _docling_convert(self, source: str) -> Optional[str]:
        """Run the full Docling pipeline and return Markdown/text."""
        try:
            result = self._converter.convert(source)
            if self.output_format == "markdown":
                md = result.document.export_to_markdown()
            else:
                md = result.document.export_to_text()
            if md and md.strip():
                return md
        except Exception as exc:
            logger.warning("Docling conversion failed for '%s': %s", source, exc)
        return None

    # ------------------------------------------------------------------ fallbacks
    def _fallback_extract(self, path: Path) -> str:
        """Try format-specific Python libraries to extract text."""
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return self._extract_pdf(path)
        if suffix in {".docx", ".doc"}:
            return self._extract_docx(path)
        if suffix in {".pptx", ".ppt"}:
            return self._extract_pptx(path)
        if suffix in {".xlsx", ".xls"}:
            return self._extract_xlsx(path)
        if suffix in {".html", ".htm"}:
            return self._extract_html(path)
        if suffix in {".md", ".txt", ".text", ".rst"}:
            return self._extract_plaintext(path)
        if suffix == ".epub":
            return self._extract_epub(path)

        # Last resort: try reading as text
        return self._extract_plaintext(path)

    # -- PDF
    @staticmethod
    def _extract_pdf(path: Path) -> str:
        # Try PyMuPDF
        try:
            import fitz
            doc = fitz.open(str(path))
            pages = [doc.load_page(i).get_text() for i in range(doc.page_count)]
            doc.close()
            text = "\n\n".join(pages).strip()
            if text:
                return f"**{path.name}**\n\n{text}"
        except ImportError:
            pass
        # Try pdfplumber
        try:
            import pdfplumber
            texts = []
            with pdfplumber.open(str(path)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text() or ""
                    texts.append(t)
            text = "\n\n".join(texts).strip()
            if text:
                return f"**{path.name}**\n\n{text}"
        except ImportError:
            pass
        return f"Cannot parse PDF '{path.name}': install PyMuPDF (pip install pymupdf) or pdfplumber."

    # -- DOCX
    @staticmethod
    def _extract_docx(path: Path) -> str:
        try:
            import docx
            doc = docx.Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return f"**{path.name}**\n\n" + "\n".join(paragraphs)
        except ImportError:
            return f"Cannot parse DOCX '{path.name}': install python-docx (pip install python-docx)."
        except Exception as exc:
            return f"Failed to parse {path.name}: {exc}"

    # -- PPTX
    @staticmethod
    def _extract_pptx(path: Path) -> str:
        try:
            from pptx import Presentation
            prs = Presentation(str(path))
            slides = []
            for i, slide in enumerate(prs.slides, 1):
                texts = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        texts.append(shape.text.strip())
                if texts:
                    slides.append(f"### Slide {i}\n" + "\n".join(texts))
            return f"**{path.name}**\n\n" + "\n\n".join(slides)
        except ImportError:
            return f"Cannot parse PPTX '{path.name}': install python-pptx (pip install python-pptx)."
        except Exception as exc:
            return f"Failed to parse {path.name}: {exc}"

    # -- XLSX
    @staticmethod
    def _extract_xlsx(path: Path) -> str:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
            output = []
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                rows = []
                for row in ws.iter_rows(values_only=True):
                    cells = [str(c) if c is not None else "" for c in row]
                    if any(cells):
                        rows.append("\t".join(cells))
                if rows:
                    output.append(f"### Sheet: {sheet_name}\n" + "\n".join(rows))
            return f"**{path.name}**\n\n" + "\n\n".join(output) if output else f"No data in {path.name}"
        except ImportError:
            return f"Cannot parse XLSX '{path.name}': install openpyxl (pip install openpyxl)."
        except Exception as exc:
            return f"Failed to parse {path.name}: {exc}"

    # -- HTML
    @staticmethod
    def _extract_html(path: Path) -> str:
        try:
            from html.parser import HTMLParser

            class _Extractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self._parts = []
                    self._skip = False

                def handle_starttag(self, tag, attrs):
                    if tag in ("script", "style"):
                        self._skip = True

                def handle_endtag(self, tag):
                    if tag in ("script", "style"):
                        self._skip = False

                def handle_data(self, data):
                    if not self._skip:
                        stripped = data.strip()
                        if stripped:
                            self._parts.append(stripped)

            raw = path.read_text(encoding="utf-8", errors="replace")
            ex = _Extractor()
            ex.feed(raw)
            return f"**{path.name}**\n\n" + "\n".join(ex._parts)
        except Exception as exc:
            return f"Failed to parse {path.name}: {exc}"

    # -- EPUB
    @staticmethod
    def _extract_epub(path: Path) -> str:
        try:
            import zipfile
            from html.parser import HTMLParser

            class _HTM(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.parts = []

                def handle_data(self, data):
                    stripped = data.strip()
                    if stripped:
                        self.parts.append(stripped)

            texts = []
            with zipfile.ZipFile(str(path)) as zf:
                for name in sorted(zf.namelist()):
                    if name.endswith((".html", ".htm", ".xhtml")):
                        raw = zf.read(name).decode("utf-8", errors="replace")
                        parser = _HTM()
                        parser.feed(raw)
                        texts.extend(parser.parts)
            return f"**{path.name}**\n\n" + "\n".join(texts) if texts else f"No text found in {path.name}"
        except Exception as exc:
            return f"Failed to parse {path.name}: {exc}"

    # -- Plain text
    @staticmethod
    def _extract_plaintext(path: Path) -> str:
        try:
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            return f"**{path.name}**\n\n{text}" if text else f"Empty file: {path.name}"
        except Exception as exc:
            return f"Cannot read {path.name}: {exc}"

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _extract_path(query: str) -> Optional[Path]:
        """Extract a file path from a natural-language query."""
        # Windows absolute
        m = re.search(r"[A-Za-z]:[/\\][\w ./_\\-]+", query)
        if m:
            p = Path(m.group(0).rstrip(" .,'\""))
            if p.exists():
                return p

        # Unix absolute
        m = re.search(r"/[\w ./_-]+", query)
        if m:
            p = Path(m.group(0).rstrip(" .,'\""))
            if p.exists():
                return p

        # Relative: anything ending with a known extension
        all_ext = "|".join(re.escape(e.lstrip(".")) for e in SUPPORTED_EXTENSIONS)
        m = re.search(rf"[\w ./\\-]+\.(?:{all_ext})\b", query, re.IGNORECASE)
        if m:
            p = Path(m.group(0).strip())
            if p.exists():
                return p

        return None

    # ------------------------------------------------------------------ info
    @property
    def available(self) -> bool:
        return self._docling_available

    def describe(self) -> str:
        status = "Docling (full pipeline)" if self._docling_available else "fallback extractors only"
        exts = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return (
            f"Document Parser powered by {status}.\n"
            f"Supported file types: {exts}\n"
            f"Output format: {self.output_format}"
        )

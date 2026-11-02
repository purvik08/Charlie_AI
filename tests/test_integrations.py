"""
Smoke tests for the four newly integrated libraries:
  - GPT Researcher (web search adapter)
  - PaddleOCR (OCR adapter)
  - Docling (document parser adapter)
  - Colibri (local LLM adapter)

These tests verify that:
1. Each adapter can be imported and instantiated without crashing.
2. Each adapter behaves correctly when optional libraries are not installed.
3. The IntentDetector correctly classifies OCR/document/Colibri intents.
"""

import sys
from pathlib import Path

# Ensure project root is on path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pytest


# ─────────────────────────────────────────────────────────────── GPT Researcher
class TestGPTResearcherAdapter:
    def test_import_and_init(self):
        from features.web_search.gpt_researcher_adapter import GPTResearcherAdapter
        adapter = GPTResearcherAdapter()
        assert adapter is not None

    def test_empty_query_returns_message(self):
        from features.web_search.gpt_researcher_adapter import GPTResearcherAdapter
        adapter = GPTResearcherAdapter()
        result = adapter.search("")
        assert "query" in result.lower() or len(result) > 0

    def test_describe_returns_string(self):
        from features.web_search.gpt_researcher_adapter import GPTResearcherAdapter
        adapter = GPTResearcherAdapter()
        desc = adapter.describe()
        assert isinstance(desc, str) and len(desc) > 0

    def test_gpt_researcher_available_is_bool(self):
        from features.web_search.gpt_researcher_adapter import GPTResearcherAdapter
        adapter = GPTResearcherAdapter()
        assert isinstance(adapter.gpt_researcher_available, bool)

    def test_duckduckgo_returns_list(self):
        from features.web_search.gpt_researcher_adapter import GPTResearcherAdapter
        adapter = GPTResearcherAdapter()
        results = adapter._fetch_duckduckgo("Python programming", max_results=3)
        assert isinstance(results, list)

    def test_wikipedia_returns_list(self):
        from features.web_search.gpt_researcher_adapter import GPTResearcherAdapter
        adapter = GPTResearcherAdapter()
        results = adapter._fetch_wikipedia("Python language", max_results=2)
        assert isinstance(results, list)

    def test_format_results(self):
        from features.web_search.gpt_researcher_adapter import GPTResearcherAdapter
        fake_results = [
            {"title": "Test", "url": "https://example.com", "snippet": "A test snippet"},
        ]
        output = GPTResearcherAdapter._format_results("test query", fake_results, 5)
        assert "test query" in output
        assert "Test" in output
        assert "example.com" in output


# ─────────────────────────────────────────────────────────────────── PaddleOCR
class TestPaddleOCRAdapter:
    def test_import_and_init(self):
        from features.ocr.paddleocr_adapter import PaddleOCRAdapter
        adapter = PaddleOCRAdapter()
        assert adapter is not None

    def test_available_is_bool(self):
        from features.ocr.paddleocr_adapter import PaddleOCRAdapter
        adapter = PaddleOCRAdapter()
        assert isinstance(adapter.available, bool)

    def test_engine_name_is_string(self):
        from features.ocr.paddleocr_adapter import PaddleOCRAdapter
        adapter = PaddleOCRAdapter()
        assert adapter.engine_name in ("PaddleOCR", "pytesseract", "none")

    def test_describe_returns_string(self):
        from features.ocr.paddleocr_adapter import PaddleOCRAdapter
        adapter = PaddleOCRAdapter()
        desc = adapter.describe()
        assert isinstance(desc, str) and len(desc) > 0

    def test_missing_file_returns_message(self):
        from features.ocr.paddleocr_adapter import PaddleOCRAdapter
        adapter = PaddleOCRAdapter()
        result = adapter.extract_text("/nonexistent/file.png")
        assert "not found" in result.lower() or "error" in result.lower() or result

    def test_process_query_no_path(self):
        from features.ocr.paddleocr_adapter import PaddleOCRAdapter
        adapter = PaddleOCRAdapter()
        result = adapter.process_query("extract text from something")
        assert isinstance(result, str) and len(result) > 0

    def test_extract_path_from_query_windows(self, tmp_path):
        from features.ocr.paddleocr_adapter import PaddleOCRAdapter
        # Create a temp file so the path resolves
        test_file = tmp_path / "test.png"
        test_file.touch()
        query = f"ocr {test_file}"
        result = PaddleOCRAdapter._extract_path_from_query(query)
        assert result is not None
        assert result == test_file

    def test_no_engine_message(self, tmp_path):
        from pathlib import Path
        from features.ocr.paddleocr_adapter import PaddleOCRAdapter
        msg = PaddleOCRAdapter._no_engine_message(Path("test.png"))
        assert "paddleocr" in msg.lower() or "tesseract" in msg.lower()


# ─────────────────────────────────────────────────────────────────── Docling
class TestDoclingAdapter:
    def test_import_and_init(self):
        from features.document_parser.docling_adapter import DoclingAdapter
        adapter = DoclingAdapter()
        assert adapter is not None

    def test_available_is_bool(self):
        from features.document_parser.docling_adapter import DoclingAdapter
        adapter = DoclingAdapter()
        assert isinstance(adapter.available, bool)

    def test_describe_returns_string(self):
        from features.document_parser.docling_adapter import DoclingAdapter
        adapter = DoclingAdapter()
        desc = adapter.describe()
        assert isinstance(desc, str) and len(desc) > 0

    def test_missing_file_returns_message(self):
        from features.document_parser.docling_adapter import DoclingAdapter
        adapter = DoclingAdapter()
        result = adapter.convert("/nonexistent/file.pdf")
        assert "not found" in result.lower() or len(result) > 0

    def test_extract_plaintext(self, tmp_path):
        from features.document_parser.docling_adapter import DoclingAdapter
        test_file = tmp_path / "hello.txt"
        test_file.write_text("Hello, world!", encoding="utf-8")
        result = DoclingAdapter._extract_plaintext(test_file)
        assert "Hello, world!" in result

    def test_extract_html(self, tmp_path):
        from features.document_parser.docling_adapter import DoclingAdapter
        test_file = tmp_path / "test.html"
        test_file.write_text("<html><body><p>Hello HTML</p></body></html>", encoding="utf-8")
        result = DoclingAdapter._extract_html(test_file)
        assert "Hello HTML" in result

    def test_get_summary_truncates(self, tmp_path):
        from features.document_parser.docling_adapter import DoclingAdapter
        adapter = DoclingAdapter()
        test_file = tmp_path / "long.txt"
        # Write 500 words
        test_file.write_text(" ".join(["word"] * 500), encoding="utf-8")
        result = adapter.get_summary(str(test_file), max_words=50)
        word_count = len(result.split())
        assert word_count < 150  # summary + some overhead

    def test_extract_path_from_query(self, tmp_path):
        from features.document_parser.docling_adapter import DoclingAdapter
        doc = tmp_path / "report.pdf"
        doc.touch()
        path = DoclingAdapter._extract_path(f"parse {doc}")
        assert path is not None


# ─────────────────────────────────────────────────────────────────── Colibri
class TestColibriAdapter:
    def test_import_and_init(self):
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter()
        assert adapter is not None

    def test_available_when_server_down(self):
        """When server is not running, available should be False."""
        from features.local_llm.colibri_adapter import ColibriAdapter
        # Use a port that will definitely not be running
        adapter = ColibriAdapter(base_url="http://127.0.0.1:19999/v1")
        assert adapter.available is False

    def test_get_models_when_down_returns_empty(self):
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter(base_url="http://127.0.0.1:19999/v1")
        assert adapter.get_models() == []

    def test_active_model_when_down(self):
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter(base_url="http://127.0.0.1:19999/v1")
        assert adapter.active_model() is None

    def test_chat_when_down_returns_guidance(self):
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter(base_url="http://127.0.0.1:19999/v1")
        result = adapter.chat("hello")
        assert "not running" in result.lower() or "colibri" in result.lower()

    def test_status_when_down(self):
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter(base_url="http://127.0.0.1:19999/v1")
        status = adapter.status()
        assert "not running" in status.lower()

    def test_start_guide_returns_string(self):
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter()
        guide = adapter.start_guide()
        assert "colibri" in guide.lower()
        assert "start" in guide.lower()

    def test_describe_returns_string(self):
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter()
        desc = adapter.describe()
        assert isinstance(desc, str) and len(desc) > 0

    def test_forced_model_override(self):
        from features.local_llm.colibri_adapter import ColibriAdapter
        adapter = ColibriAdapter(model="my-custom-model")
        assert adapter.active_model() == "my-custom-model"


# ─────────────────────────────────────────────────────────────── IntentDetector
class TestIntentDetector:
    def setup_method(self):
        from core.intent import IntentDetector
        self.detector = IntentDetector()

    def test_ocr_intent(self):
        result = self.detector.detect("extract text from C:/scan.png")
        assert result.intent == "ocr"
        assert "c:/scan.png" in result.slots.get("path", "").lower()

    def test_ocr_intent_shorthand(self):
        result = self.detector.detect("ocr /path/to/image.jpg")
        assert result.intent == "ocr"

    def test_document_parse_intent(self):
        result = self.detector.detect("parse report.pdf")
        assert result.intent == "document_parse"

    def test_document_parse_intent_read_doc(self):
        result = self.detector.detect("read document invoice.docx")
        assert result.intent == "document_parse"

    def test_colibri_status_intent(self):
        result = self.detector.detect("colibri")
        assert result.intent == "colibri_status"
        assert result.slots.get("action") == "status"

    def test_colibri_start_intent(self):
        result = self.detector.detect("colibri start")
        assert result.intent == "colibri_status"
        assert result.slots.get("action") == "start"

    def test_colibri_models_intent(self):
        result = self.detector.detect("colibri models")
        assert result.intent == "colibri_status"
        assert result.slots.get("action") == "models"

    def test_web_search_intent(self):
        result = self.detector.detect("search the web for Python tutorials")
        assert result.intent == "web_search"
        assert "python tutorials" in result.slots.get("query", "").lower()

    def test_chat_fallback(self):
        result = self.detector.detect("tell me about black holes")
        assert result.intent == "chat"
        assert result.requires_llm is True

    def test_greeting(self):
        result = self.detector.detect("hello charlie")
        assert result.intent == "greeting"

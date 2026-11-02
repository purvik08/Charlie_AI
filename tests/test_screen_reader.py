from pathlib import Path

from features.screen_reader import ScreenReader
from core.intent import IntentDetector


class _Image:
    def __init__(self):
        self.saved_to = None

    def save(self, path, image_format):
        self.saved_to = Path(path)
        self.saved_to.write_bytes(b"test image")


class _OCR:
    def __init__(self):
        self.path = None

    def extract_text(self, path):
        self.path = Path(path)
        return "Detected text"


def test_screen_reader_uses_a_temporary_capture_by_default(tmp_path):
    image = _Image()
    ocr = _OCR()
    reader = ScreenReader(ocr, tmp_path, capture=lambda: image)

    result = reader.read_current_screen()

    assert "Screen text" in result
    assert "Detected text" in result
    assert image.saved_to == ocr.path
    assert image.saved_to.parent == tmp_path / "screens"
    assert not image.saved_to.exists()


def test_screen_reader_can_retain_and_clear_captures(tmp_path):
    image = _Image()
    reader = ScreenReader(_OCR(), tmp_path, capture=lambda: image, retain_captures=True)

    result = reader.read_current_screen()

    assert "Saved locally" in result
    assert image.saved_to.is_file()
    assert reader.clear_captures() == "Cleared 1 saved screen capture."
    assert not image.saved_to.exists()


def test_screen_reader_reports_capture_errors(tmp_path):
    def broken_capture():
        raise RuntimeError("permission denied")

    result = ScreenReader(_OCR(), tmp_path, capture=broken_capture).read_current_screen()

    assert "Could not capture" in result
    assert "permission denied" in result


def test_read_screen_command_has_a_direct_intent():
    result = IntentDetector().detect("read screen")

    assert result.intent == "read_screen"
    assert result.requires_llm is False


def test_clear_screen_captures_has_a_direct_intent():
    result = IntentDetector().detect("clear screen captures")

    assert result.intent == "clear_screen_captures"
